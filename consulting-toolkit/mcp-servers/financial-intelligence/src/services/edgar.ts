import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from "axios";
import {
  EDGAR_BASE_URL,
  EDGAR_XBRL_URL,
  EDGAR_SUBMISSIONS_URL,
  EDGAR_BROWSE_URL,
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
  ShareCountFact,
  EpsFact,
  EquityFundamentals,
} from "../types.js";
import { RateLimiter } from "./rate-limiter.js";
import { cachedFetch, CACHE_TTLS } from "./cache.js";

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
// payload; a short in-memory TTL cache avoids re-downloading it within one
// workflow, backed by the shared disk cache across server restarts.

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

  const data = await cachedFetch<SubmissionsPayload>(
    "submissions",
    key,
    CACHE_TTLS.submissions,
    async () => {
      const resp = await edgarGet<SubmissionsPayload>(
        `${EDGAR_SUBMISSIONS_URL}/CIK${key}.json`
      );
      return resp.data;
    }
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
  cik_str: string | number;
  ticker: string;
  title: string;
}

const TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json";

let tickerMap: Map<string, TickerMapping> | null = null;
let cikListingMap: Map<string, TickerMapping> | null = null;

async function loadTickerMaps(): Promise<{
  byTicker: Map<string, TickerMapping>;
  byCik: Map<string, TickerMapping>;
}> {
  if (tickerMap && cikListingMap) {
    return { byTicker: tickerMap, byCik: cikListingMap };
  }
  const data = await cachedFetch<Record<string, TickerMapping>>(
    "tickerMap",
    TICKER_MAP_URL,
    CACHE_TTLS.tickerMap,
    async () => {
      const resp = await edgarGet<Record<string, TickerMapping>>(TICKER_MAP_URL);
      return resp.data;
    }
  );
  const byTicker = new Map<string, TickerMapping>();
  const byCik = new Map<string, TickerMapping>();
  for (const entry of Object.values(data)) {
    byTicker.set(entry.ticker.toUpperCase(), entry);
    const cikKey = String(entry.cik_str);
    // First listing per CIK wins — the SEC file orders primary listings first.
    if (!byCik.has(cikKey)) byCik.set(cikKey, entry);
  }
  tickerMap = byTicker;
  cikListingMap = byCik;
  return { byTicker, byCik };
}

export async function resolveTickerToCik(ticker: string): Promise<string> {
  const { byTicker } = await loadTickerMaps();
  const entry = byTicker.get(ticker.toUpperCase());
  if (!entry) {
    throw new Error(`Ticker "${ticker}" not found in SEC EDGAR.`);
  }
  return String(entry.cik_str);
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
  const key = padCik(cik);
  return cachedFetch<XBRLResponse>(
    "companyFacts",
    key,
    CACHE_TTLS.companyFacts,
    async () => {
      const { data } = await edgarGet<XBRLResponse>(`${EDGAR_XBRL_URL}/CIK${key}.json`);
      return data;
    }
  );
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
  // Filed documents are immutable once published; cache the stripped text.
  return cachedFetch<string>(
    "filingDocument",
    url,
    CACHE_TTLS.filingDocument,
    async () => {
      const { data } = await edgarGet<string>(url, {
        responseType: "text",
        headers: { Accept: "text/html,text/plain,*/*" },
      });
      return stripHtml(data);
    }
  );
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
//
// Uses EDGAR's classic browse endpoint — the supported way to list companies
// by SIC code (the full-text search API cannot filter by SIC; a previous
// implementation derived CIKs from EFTS file numbers, which never resolve).
//
// Note on parsing: the atom output's name attributes are broken server-side
// (they serialize as Perl "ARRAY(0x...)" strings), so only CIKs are parsed
// from the feed. Names and tickers come from the cached company_tickers.json
// listing map, which also filters the alphabetical registrant roll (full of
// long-dead filers) down to currently listed companies — the population that
// peer benchmarking actually wants.

const SIC_BROWSE_PAGE_SIZE = 40;
const MAX_SIC_BROWSE_PAGES = 5;

export interface SicSearchResult {
  companies: EdgarCompanyInfo[];
  note?: string;
}

function parseSicBrowseCiks(atomXml: string): string[] {
  const ciks: string[] = [];
  const seen = new Set<string>();
  for (const m of atomXml.matchAll(/<cik>\s*0*(\d+)\s*<\/cik>/gi)) {
    if (!seen.has(m[1])) {
      seen.add(m[1]);
      ciks.push(m[1]);
    }
  }
  return ciks;
}

async function fetchSicBrowsePage(sicCode: string, start: number): Promise<string[]> {
  const url =
    `${EDGAR_BROWSE_URL}?action=getcompany&SIC=${encodeURIComponent(sicCode)}` +
    `&type=10-K&dateb=&owner=include&count=${SIC_BROWSE_PAGE_SIZE}&start=${start}&output=atom`;
  const xml = await cachedFetch<string>("sicBrowse", url, CACHE_TTLS.sicBrowse, async () => {
    const { data } = await edgarGet<string>(url, {
      responseType: "text",
      headers: { Accept: "application/atom+xml,application/xml,text/xml,*/*" },
    });
    return data;
  });
  return parseSicBrowseCiks(xml);
}

export async function getCompaniesBySic(
  sicCode: string,
  limit: number = 15
): Promise<SicSearchResult> {
  const { byCik } = await loadTickerMaps();

  const allCiks: string[] = [];
  const seen = new Set<string>();
  const listed: { cik: string; entry: TickerMapping }[] = [];
  let exhausted = false;

  for (let page = 0; page < MAX_SIC_BROWSE_PAGES && listed.length < limit; page++) {
    const pageCiks = await fetchSicBrowsePage(sicCode, page * SIC_BROWSE_PAGE_SIZE);
    for (const cik of pageCiks) {
      if (seen.has(cik)) continue;
      seen.add(cik);
      allCiks.push(cik);
      const entry = byCik.get(cik);
      if (entry && listed.length < limit) listed.push({ cik, entry });
    }
    if (pageCiks.length < SIC_BROWSE_PAGE_SIZE) {
      exhausted = true;
      break;
    }
  }

  if (listed.length > 0) {
    const companies: EdgarCompanyInfo[] = listed.map(({ cik, entry }) => ({
      cik,
      ticker: entry.ticker.toUpperCase(),
      name: entry.title,
      sic: sicCode,
      sicDescription: "",
      exchanges: [],
    }));
    return {
      companies,
      note: !exhausted
        ? `SIC ${sicCode} has more registrants than scanned (${allCiks.length} checked across ${MAX_SIC_BROWSE_PAGES} pages); the EDGAR listing is alphabetical, so these are the first ${companies.length} currently listed 10-K filers by name, not a size-ranked sample.`
        : undefined,
    };
  }

  // No currently listed registrants matched — fall back to the raw browse
  // results (may include delisted or private filers), resolved via the
  // cached submissions payloads.
  const companies: EdgarCompanyInfo[] = [];
  for (const cik of allCiks.slice(0, limit)) {
    try {
      companies.push(await getCompanyInfo(cik));
    } catch {
      // Skip CIKs whose submissions payload fails to resolve
    }
  }
  return {
    companies,
    note:
      companies.length > 0
        ? `No currently listed registrants found for SIC ${sicCode}; returning raw EDGAR browse results, which may include delisted or private filers with stale financials.`
        : `EDGAR company browse returned no 10-K filers for SIC ${sicCode}.`,
  };
}

// ── Equity Fundamentals (shares outstanding, annual EPS) ──
// Powers the honestly-labeled computed fields in fin_get_stock_data: market
// cap is EDGAR-reported shares × a price the caller supplies, never a quoted
// figure from an unlicensed source.

const SHARES_SOURCES: { taxonomy: "dei" | "us-gaap"; tag: string }[] = [
  { taxonomy: "dei", tag: "EntityCommonStockSharesOutstanding" },
  { taxonomy: "us-gaap", tag: "CommonStockSharesOutstanding" },
];

const EPS_TAGS = ["EarningsPerShareDiluted", "EarningsPerShareBasic"];

export async function getEquityFundamentals(ticker: string): Promise<EquityFundamentals> {
  const cik = await resolveTickerToCik(ticker);
  const factsResp = await getCompanyFacts(cik);

  let shares: ShareCountFact | null = null;
  for (const src of SHARES_SOURCES) {
    const units = factsResp.facts[src.taxonomy]?.[src.tag]?.units?.["shares"];
    if (!units) continue;
    const usable = [...units].filter((f) => f.end && typeof f.val === "number");
    const latest = usable.sort((a, b) => b.end.localeCompare(a.end))[0];
    if (latest) {
      // A single fact is selected; multi-class issuers report cover-page
      // share counts per class (sometimes as several facts with the same end
      // date), so one fact may understate the total. Say so honestly.
      const sameEnd = usable.filter((f) => f.end === latest.end).length;
      shares = {
        value: latest.val,
        asOf: latest.end,
        form: latest.form,
        tag: `${src.taxonomy}:${src.tag}`,
        note:
          sameEnd > 1
            ? `EDGAR reports ${sameEnd} share-count facts as of ${latest.end} (typically one per share class); this figure is a single fact and may cover only one class, understating the total.`
            : "For multi-class issuers this fact may reflect a single share class, understating total shares.",
      };
      break;
    }
  }

  let eps: EpsFact | null = null;
  const gaap = factsResp.facts["us-gaap"] || {};
  for (const tag of EPS_TAGS) {
    const units = gaap[tag]?.units?.["USD/shares"];
    if (!units) continue;
    // A 10-K re-reports prior-year comparatives; the latest period end across
    // FY facts is the fiscal year the most recent 10-K actually covers.
    const latest = [...units]
      .filter((f) => f.form === "10-K" && f.fp === "FY" && f.end && typeof f.val === "number")
      .sort((a, b) => b.end.localeCompare(a.end))[0];
    if (latest) {
      eps = {
        value: latest.val,
        periodEnd: latest.end,
        fiscalYear: latest.fy,
        form: latest.form,
        tag: `us-gaap:${tag}`,
      };
      break;
    }
  }

  return {
    cik,
    entityName: factsResp.entityName,
    sharesOutstanding: shares,
    epsAnnual: eps,
  };
}
