import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from "axios";
import {
  EDGAR_BASE_URL,
  EDGAR_XBRL_URL,
  EDGAR_SUBMISSIONS_URL,
  EDGAR_EFTS_URL,
  RATE_LIMITS,
  XBRL_METRIC_TAGS,
} from "../constants.js";
import type {
  EdgarCompanyInfo,
  EdgarXBRLFact,
  FinancialMetric,
  FinancialPeriod,
  DerivedMetric,
  FilingInfo,
} from "../types.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.edgar);

// Placeholder only — the SEC requires a real contact; index.ts warns loudly
// at startup when EDGAR_USER_AGENT is unset.
const EDGAR_USER_AGENT_PLACEHOLDER = "FinancialIntelligenceMCP bot@example.com";

function createClient(): AxiosInstance {
  const userAgent = process.env.EDGAR_USER_AGENT || EDGAR_USER_AGENT_PLACEHOLDER;
  return axios.create({
    baseURL: EDGAR_BASE_URL,
    headers: {
      "User-Agent": userAgent,
      Accept: "application/json",
    },
    timeout: 30_000,
  });
}

let client: AxiosInstance | null = null;
function getClient(): AxiosInstance {
  if (!client) client = createClient();
  return client;
}

// ── Rate-limited GET with retry ──
// SEC returns 429/503 when throttling; retry with exponential backoff.

const MAX_RETRIES = 3;
const RETRY_BASE_DELAY_MS = 500;

async function edgarGet<T = unknown>(
  url: string,
  config?: AxiosRequestConfig
): Promise<AxiosResponse<T>> {
  for (let attempt = 0; ; attempt++) {
    await limiter.acquire();
    try {
      return await getClient().get<T>(url, config);
    } catch (err) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      const retryable = status === 429 || (status !== undefined && status >= 500);
      if (!retryable || attempt >= MAX_RETRIES) throw err;
      const backoffMs = RETRY_BASE_DELAY_MS * 2 ** attempt;
      await new Promise((resolve) => setTimeout(resolve, backoffMs));
    }
  }
}

// Pad CIK to 10 digits as required by EDGAR URLs
function padCik(cik: string): string {
  return cik.replace(/^0+/, "").padStart(10, "0");
}

// ── Submissions Cache ──
// getCompanyInfo and getFilings both need the CIK{cik}.json submissions
// payload; a short TTL cache avoids re-downloading it within one workflow.

interface SubmissionsPayload {
  cik: string;
  name?: string;
  entityName?: string;
  tickers?: string[];
  sic?: string;
  sicDescription?: string;
  exchanges?: string[];
  filings?: {
    recent?: Record<string, string[]>;
  };
}

const SUBMISSIONS_CACHE_TTL_MS = 15 * 60 * 1000;
const SUBMISSIONS_CACHE_MAX_ENTRIES = 32;
const submissionsCache = new Map<string, { data: SubmissionsPayload; fetchedAt: number }>();

async function getSubmissions(cik: string): Promise<SubmissionsPayload> {
  const key = padCik(cik);
  const cached = submissionsCache.get(key);
  if (cached && Date.now() - cached.fetchedAt < SUBMISSIONS_CACHE_TTL_MS) {
    return cached.data;
  }

  const { data } = await edgarGet<SubmissionsPayload>(
    `${EDGAR_SUBMISSIONS_URL}/CIK${key}.json`
  );

  // Evict oldest entries to bound memory (submissions payloads can be large)
  while (submissionsCache.size >= SUBMISSIONS_CACHE_MAX_ENTRIES) {
    const oldestKey = submissionsCache.keys().next().value;
    if (oldestKey === undefined) break;
    submissionsCache.delete(oldestKey);
  }
  submissionsCache.set(key, { data, fetchedAt: Date.now() });
  return data;
}

// ── Ticker → CIK Resolution ──

interface TickerMapping {
  cik_str: string;
  ticker: string;
  title: string;
}

let tickerMap: Map<string, TickerMapping> | null = null;

async function loadTickerMap(): Promise<Map<string, TickerMapping>> {
  if (tickerMap) return tickerMap;
  const { data } = await edgarGet<Record<string, TickerMapping>>(
    "https://www.sec.gov/files/company_tickers.json"
  );
  tickerMap = new Map<string, TickerMapping>();
  for (const entry of Object.values(data)) {
    tickerMap.set(entry.ticker.toUpperCase(), entry);
  }
  return tickerMap;
}

export async function resolveTickerToCik(ticker: string): Promise<string> {
  const map = await loadTickerMap();
  const entry = map.get(ticker.toUpperCase());
  if (!entry) {
    throw new Error(`Ticker "${ticker}" not found in SEC EDGAR.`);
  }
  return entry.cik_str.toString();
}

// ── Company Info ──

export async function getCompanyInfo(
  tickerOrCik: string
): Promise<EdgarCompanyInfo> {
  let cik: string;
  if (/^\d+$/.test(tickerOrCik)) {
    cik = tickerOrCik;
  } else {
    cik = await resolveTickerToCik(tickerOrCik);
  }

  const data = await getSubmissions(cik);

  return {
    cik: data.cik,
    ticker: (data.tickers?.[0] || tickerOrCik).toUpperCase(),
    name: data.name || data.entityName || "",
    sic: data.sic || "",
    sicDescription: data.sicDescription || "",
    exchanges: data.exchanges || [],
  };
}

// ── XBRL Company Facts ──

interface XBRLResponse {
  entityName: string;
  facts: {
    "us-gaap"?: Record<string, { units: Record<string, EdgarXBRLFact[]> }>;
    "dei"?: Record<string, { units: Record<string, EdgarXBRLFact[]> }>;
  };
}

export async function getCompanyFacts(cik: string): Promise<XBRLResponse> {
  const { data } = await edgarGet<XBRLResponse>(
    `${EDGAR_XBRL_URL}/CIK${padCik(cik)}.json`
  );
  return data;
}

function extractMetricFromFacts(
  facts: XBRLResponse["facts"],
  metricName: string,
  period: "annual" | "quarterly",
  limit: number
): FinancialPeriod[] {
  const tags = (XBRL_METRIC_TAGS as Record<string, string[] | undefined>)[metricName];
  if (!tags || tags.length === 0) return [];

  const gaap = facts["us-gaap"] || {};
  const formFilter = period === "annual" ? "10-K" : "10-Q";

  // Try all tags and pick the one with the most recent data
  let bestResult: FinancialPeriod[] = [];
  let bestLatestDate = "";

  for (const tag of tags) {
    const factData = gaap[tag];
    if (!factData) continue;

    // Try USD first, then pure number
    const units = factData.units["USD"] || factData.units["USD/shares"] || factData.units["shares"] || factData.units["pure"];
    if (!units) continue;

    const filtered = units
      .filter((f) => f.form === formFilter && f.end && f.val !== undefined)
      .sort((a, b) => b.end.localeCompare(a.end));

    // Deduplicate by period end date (keep latest filing)
    const seen = new Set<string>();
    const deduped: EdgarXBRLFact[] = [];
    for (const fact of filtered) {
      if (!seen.has(fact.end)) {
        seen.add(fact.end);
        deduped.push(fact);
      }
    }

    if (deduped.length === 0) continue;

    const latestDate = deduped[0].end;
    if (latestDate > bestLatestDate) {
      bestLatestDate = latestDate;
      bestResult = deduped.slice(0, limit).map((fact) => ({
        period: period === "annual" ? `FY${fact.fy}` : `${fact.fp} ${fact.fy}`,
        endDate: fact.end,
        value: fact.val,
        form: fact.form,
        filed: fact.filed,
      }));
    }
  }

  return bestResult;
}

export async function getFinancialMetrics(
  tickerOrCik: string,
  metrics: string[],
  period: "annual" | "quarterly",
  limit: number
): Promise<{ company: EdgarCompanyInfo; metrics: FinancialMetric[]; derived: DerivedMetric[] }> {
  const info = await getCompanyInfo(tickerOrCik);
  const facts = await getCompanyFacts(info.cik);

  const result: FinancialMetric[] = [];
  for (const metric of metrics) {
    if (metric === "ebitda") continue; // Computed below
    const periods = extractMetricFromFacts(facts.facts, metric, period, limit);
    result.push({ metric, periods });
  }

  // Compute derived metrics
  const derived: DerivedMetric[] = [];

  // EBITDA = operating_income + depreciation
  if (metrics.includes("ebitda")) {
    const opIncome = extractMetricFromFacts(facts.facts, "operating_income", period, limit);
    const depreciation = extractMetricFromFacts(facts.facts, "depreciation", period, limit);
    const ebitdaPeriods = opIncome.map((oi) => {
      const dep = depreciation.find((d) => d.endDate === oi.endDate);
      return {
        period: oi.period,
        value: dep ? oi.value + dep.value : null,
      };
    });
    derived.push({ metric: "ebitda", periods: ebitdaPeriods });
  }

  // Revenue growth (YoY)
  const revenueMetric = result.find((m) => m.metric === "revenue");
  if (revenueMetric && revenueMetric.periods.length >= 2) {
    const growthPeriods = [];
    for (let i = 0; i < revenueMetric.periods.length - 1; i++) {
      const current = revenueMetric.periods[i].value;
      const prior = revenueMetric.periods[i + 1].value;
      growthPeriods.push({
        period: revenueMetric.periods[i].period,
        value: prior !== 0 ? ((current - prior) / Math.abs(prior)) * 100 : null,
      });
    }
    derived.push({ metric: "revenue_growth_pct", periods: growthPeriods });
  }

  // Gross margin
  const grossProfit = result.find((m) => m.metric === "gross_profit");
  if (grossProfit && revenueMetric) {
    const marginPeriods = grossProfit.periods.map((gp) => {
      const rev = revenueMetric.periods.find((r) => r.endDate === gp.endDate);
      return {
        period: gp.period,
        value: rev && rev.value !== 0 ? (gp.value / rev.value) * 100 : null,
      };
    });
    derived.push({ metric: "gross_margin_pct", periods: marginPeriods });
  }

  // Net margin
  const netIncome = result.find((m) => m.metric === "net_income");
  if (netIncome && revenueMetric) {
    const marginPeriods = netIncome.periods.map((ni) => {
      const rev = revenueMetric.periods.find((r) => r.endDate === ni.endDate);
      return {
        period: ni.period,
        value: rev && rev.value !== 0 ? (ni.value / rev.value) * 100 : null,
      };
    });
    derived.push({ metric: "net_margin_pct", periods: marginPeriods });
  }

  return { company: info, metrics: result, derived };
}

// ── Filing Retrieval ──

export async function getFilings(
  tickerOrCik: string,
  filingType: string,
  limit: number
): Promise<{ company: EdgarCompanyInfo; filings: FilingInfo[] }> {
  const info = await getCompanyInfo(tickerOrCik);
  // Served from the submissions cache — getCompanyInfo just fetched this payload
  const data = await getSubmissions(info.cik);

  const recentFilings = data.filings?.recent || {};
  const forms: string[] = recentFilings.form || [];
  const accessions: string[] = recentFilings.accessionNumber || [];
  const filingDates: string[] = recentFilings.filingDate || [];
  const reportDates: string[] = recentFilings.reportDate || [];
  const primaryDocs: string[] = recentFilings.primaryDocument || [];
  const primaryDocDescs: string[] = recentFilings.primaryDocDescription || [];
  const items: string[] = recentFilings.items || [];

  const filings: FilingInfo[] = [];
  for (let i = 0; i < forms.length && filings.length < limit; i++) {
    if (forms[i] === filingType) {
      filings.push({
        accessionNumber: accessions[i],
        filingDate: filingDates[i],
        reportDate: reportDates[i] || filingDates[i],
        form: forms[i],
        primaryDocument: primaryDocs[i] || "",
        primaryDocDescription: primaryDocDescs[i] || "",
        items: items[i] || "",
      });
    }
  }

  return { company: info, filings };
}

export async function getFilingDocument(
  cik: string,
  accessionNumber: string,
  primaryDocument: string
): Promise<string> {
  const accessionPath = accessionNumber.replace(/-/g, "");
  const numericCik = parseInt(cik, 10).toString();
  const url = `https://www.sec.gov/Archives/edgar/data/${numericCik}/${accessionPath}/${primaryDocument}`;
  const { data } = await edgarGet<string>(url, {
    responseType: "text",
    headers: { Accept: "text/html,text/plain,*/*" },
  });
  return stripHtml(data);
}

function stripHtml(html: string): string {
  return html
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, "")
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#?\w+;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// ── Company Search by SIC Code ──

// Hard cap on submissions lookups during the fallback ticker-map scan so a
// niche SIC code cannot hammer data.sec.gov for minutes on end.
const MAX_SIC_SCAN_REQUESTS = 300;

export interface SicSearchResult {
  companies: EdgarCompanyInfo[];
  note?: string;
}

interface EftsSearchResponse {
  hits?: {
    hits?: { _source?: { file_num?: string } }[];
  };
}

export async function getCompaniesBySic(sicCode: string, limit: number = 15): Promise<SicSearchResult> {
  const encodedSic = encodeURIComponent(sicCode);
  const companies: EdgarCompanyInfo[] = [];
  const seenCiks = new Set<string>();

  // Best-effort full-text search for recent 10-K filers mentioning the SIC code
  let searchData: EftsSearchResponse | null = null;
  try {
    const { data } = await edgarGet<EftsSearchResponse>(
      `${EDGAR_EFTS_URL}/search-index?q=%22${encodedSic}%22&forms=10-K`,
      { baseURL: "" }
    );
    searchData = data;
  } catch {
    // Full-text search is best-effort; fall through to the ticker-map scan
  }

  if (searchData?.hits?.hits) {
    for (const hit of searchData.hits.hits) {
      if (companies.length >= limit) break;
      const fileCik = hit._source?.file_num?.split("-")[0];
      if (fileCik && !seenCiks.has(fileCik)) {
        seenCiks.add(fileCik);
        try {
          const info = await getCompanyInfo(fileCik);
          if (info.sic === sicCode) {
            companies.push(info);
          }
        } catch {
          // Skip companies that fail to resolve
        }
      }
    }
  }

  // If we didn't find enough via search, scan the ticker map (capped)
  let scanned = 0;
  let scanCapped = false;
  if (companies.length < limit) {
    const map = await loadTickerMap();
    for (const entry of map.values()) {
      if (companies.length >= limit) break;
      if (scanned >= MAX_SIC_SCAN_REQUESTS) {
        scanCapped = true;
        break;
      }
      if (seenCiks.has(entry.cik_str)) continue;
      scanned++;
      try {
        const info = await getCompanyInfo(entry.cik_str);
        if (info.sic === sicCode) {
          seenCiks.add(entry.cik_str);
          companies.push(info);
        }
      } catch {
        // Skip
      }
    }
  }

  return {
    companies,
    note: scanCapped
      ? `Peer discovery stopped after ${MAX_SIC_SCAN_REQUESTS} SEC submissions lookups to respect SEC fair-access limits; results may be a partial sample of SIC ${sicCode}.`
      : undefined,
  };
}
