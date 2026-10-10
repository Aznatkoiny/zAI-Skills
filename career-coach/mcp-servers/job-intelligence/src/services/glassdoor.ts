/**
 * Glassdoor HTML scraper — best-effort source (scraper tier) for company
 * profiles, salaries, and interview experiences. Glassdoor frequently
 * bot-blocks; failures are reported honestly via SourceMeta and successful
 * results are cached for 24h (company/salary lookups).
 */

import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, SCRAPERS_DISABLED_DETAIL, SCRAPERS_ENABLED, USER_AGENT } from "../constants.js";
import type { CompanyInfo, InterviewExperience, SalaryData, SourceMeta, SourceResult } from "../types.js";
import { fetchWithCache, LOOKUP_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.glassdoor);

const GLASSDOOR_BASE_URL = "https://www.glassdoor.com";

/**
 * Fetch and parse a company overview page. Throws on bot-block/miss so
 * failures are never cached.
 */
async function fetchCompanyInfo(company: string): Promise<CompanyInfo> {
  // Search for the company
  const searchUrl = `${GLASSDOOR_BASE_URL}/Search/results.htm?keyword=${encodeURIComponent(company)}&typedKeyword=${encodeURIComponent(company)}&sc.keyword=${encodeURIComponent(company)}`;

  await limiter.acquire();

  const searchResponse = await axios.get(searchUrl, {
    headers: {
      "User-Agent": USER_AGENT,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
    timeout: 15_000,
    maxRedirects: 5,
  });

  const $search = cheerio.load(searchResponse.data);

  // Try to find company overview link from search results
  const companyLink = $search("a[href*='/Overview/'], a[data-test='employer-short-name']").first().attr("href");
  const overviewUrl = companyLink
    ? (companyLink.startsWith("http") ? companyLink : `${GLASSDOOR_BASE_URL}${companyLink}`)
    : null;

  // Without a real overview link there is no valid URL to guess (Glassdoor
  // overview URLs require the numeric employer id), so fail explicitly
  // instead of burning a rate-limit slot on a guaranteed-dead request.
  if (!overviewUrl) {
    throw new Error(
      `Glassdoor search returned no overview page for "${company}" (status ${searchResponse.status}) — likely bot-blocked or the company is not listed`
    );
  }

  await limiter.acquire();

  const overviewResponse = await axios.get(overviewUrl, {
    headers: {
      "User-Agent": USER_AGENT,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
    timeout: 15_000,
    maxRedirects: 5,
    validateStatus: (status) => status < 500,
  });

  if (overviewResponse.status >= 400) {
    throw new Error(`Glassdoor returned ${overviewResponse.status} — likely bot-blocked`);
  }

  const $ = cheerio.load(overviewResponse.data);

  // Parse company overview
  const name = $("[data-test='employer-name'], h1.employer-name, h1").first().text().trim() || company;

  // Rating
  let rating: number | null = null;
  const ratingText = $("[data-test='rating-info'] .rating, .ratingNum, [class*='rating'] .num, [class*='Rating'] span").first().text().trim();
  if (ratingText) {
    const parsed = parseFloat(ratingText);
    if (!isNaN(parsed)) rating = parsed;
  }

  // Company details from info section
  const industry = extractDetail($, "Industry", "Type");
  const size = extractDetail($, "Size", "Employees");
  const headquarters = extractDetail($, "Headquarters", "Location");
  const founded = extractDetail($, "Founded", "Year");
  const revenue = extractDetail($, "Revenue", "Annual");

  // Culture ratings
  const culture_ratings: Record<string, number> = {};
  $("[class*='culture'] [class*='rating-row'], [data-test*='culture'] div, .subRatings div").each((_i, el) => {
    try {
      const label = $(el).find("[class*='label'], span:first-child").first().text().trim();
      const val = $(el).find("[class*='value'], span:last-child").first().text().trim();
      if (label && val) {
        const num = parseFloat(val);
        if (!isNaN(num)) culture_ratings[label] = num;
      }
    } catch {
      // skip individual rating parse errors
    }
  });

  return {
    name,
    industry,
    size,
    rating,
    culture_ratings: Object.keys(culture_ratings).length > 0 ? culture_ratings : null,
    interview_process: null,
    headquarters,
    founded,
    revenue,
  };
}

/**
 * Get company overview information from Glassdoor (scraper, cached 24h).
 * Never throws — on failure `info` is null and the reason is in `meta`.
 */
export async function getGlassdoorCompanyInfo(
  company: string
): Promise<{ meta: SourceMeta; info: CompanyInfo | null }> {
  if (!SCRAPERS_ENABLED) {
    return { meta: { source: "Glassdoor", tier: "scraper", state: "skipped", detail: SCRAPERS_DISABLED_DETAIL }, info: null };
  }
  const res = await fetchWithCache<CompanyInfo>(
    "glassdoor-company",
    { company: company.toLowerCase().trim() },
    LOOKUP_TTL_MS,
    () => fetchCompanyInfo(company)
  );

  if (res.ok) {
    return {
      meta: { source: "Glassdoor", tier: "scraper", state: res.state, count: 1, ageMs: res.ageMs },
      info: res.value,
    };
  }
  return {
    meta: { source: "Glassdoor", tier: "scraper", state: "failed", detail: res.reason },
    info: null,
  };
}

function extractDetail($: cheerio.CheerioAPI, ...labels: string[]): string | null {
  for (const label of labels) {
    try {
      const el = $(`[class*='infoEntity']:contains("${label}"), dt:contains("${label}"), th:contains("${label}")`).first();
      if (el.length > 0) {
        const value = el.next("dd, td, span, [class*='value']").first().text().trim()
          || el.parent().find("[class*='value'], dd, td").first().text().trim();
        if (value) return value;
      }
    } catch {
      // skip
    }
  }
  return null;
}

/**
 * Fetch and parse Glassdoor salary search results. Throws when nothing
 * could be parsed so failures are never cached.
 */
async function fetchSalaries(role: string, company?: string): Promise<SalaryData[]> {
  const salaries: SalaryData[] = [];

  const searchQuery = company ? `${role} ${company}` : role;
  const searchUrl = `${GLASSDOOR_BASE_URL}/Salaries/know-your-worth.htm?keyword=${encodeURIComponent(searchQuery)}`;

  await limiter.acquire();

  const response = await axios.get(searchUrl, {
    headers: {
      "User-Agent": USER_AGENT,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
    timeout: 15_000,
    maxRedirects: 5,
    validateStatus: (status) => status < 500,
  });

  const $ = cheerio.load(response.data);

  // Parse salary results
  $("[data-test='salaries-list'] li, [class*='SalaryCard'], [class*='salary-card'], .salaryList .salary-row, table tbody tr").each((_index, element) => {
    try {
      const el = $(element);

      const roleText = el.find("[class*='title'], h3, td:first-child, [data-test='salary-title']").first().text().trim() || role;
      const companyText = el.find("[class*='company'], [data-test='company-name'], td:nth-child(2)").first().text().trim() || company || null;

      // Try to parse salary figures
      const payText = el.find("[class*='pay'], [class*='salary'], [data-test='salary-amount'], td:nth-child(3)").first().text().trim();
      const baseMatch = payText.match(/\$?([\d,]+)/);
      const base = baseMatch ? parseInt(baseMatch[1].replace(/,/g, ""), 10) : null;

      // Additional compensation components
      const bonusText = el.find("[class*='bonus'], [class*='additional']").first().text().trim();
      const bonusMatch = bonusText.match(/\$?([\d,]+)/);
      const bonus = bonusMatch ? parseInt(bonusMatch[1].replace(/,/g, ""), 10) : null;

      const total_comp = base && bonus ? base + bonus : base;

      if (roleText) {
        salaries.push({
          role: roleText,
          company: companyText,
          location: null,
          base,
          equity: null,
          bonus,
          total_comp,
          level: null,
          source: "glassdoor",
        });
      }
    } catch (innerErr) {
      console.error("Error parsing individual Glassdoor salary:", innerErr);
    }
  });

  // Entries with no compensation numbers at all are parse noise, not data.
  const withData = salaries.filter((s) => s.base !== null || s.total_comp !== null || s.bonus !== null);
  if (withData.length === 0) {
    throw new Error("no salary entries parsed — likely bot-blocked or the HTML structure changed");
  }

  return withData;
}

/**
 * Get salary data for a role from Glassdoor (scraper, cached 24h).
 * Never throws — failures land in meta.
 */
export async function getGlassdoorSalaries(
  role: string,
  company?: string
): Promise<SourceResult<SalaryData>> {
  if (!SCRAPERS_ENABLED) {
    return { meta: { source: "Glassdoor", tier: "scraper", state: "skipped", detail: SCRAPERS_DISABLED_DETAIL }, items: [] };
  }
  const res = await fetchWithCache(
    "glassdoor-salaries",
    { role: role.toLowerCase().trim(), company: company?.toLowerCase().trim() || null },
    LOOKUP_TTL_MS,
    () => fetchSalaries(role, company)
  );
  return toSourceResult("Glassdoor", "scraper", res);
}

/**
 * Fetch and parse Glassdoor interview experiences. Throws when nothing
 * could be parsed so failures are never cached.
 */
async function fetchInterviews(company: string, role?: string): Promise<InterviewExperience[]> {
  const experiences: InterviewExperience[] = [];

  const searchQuery = role ? `${company} ${role} interview` : `${company} interview`;
  const searchUrl = `${GLASSDOOR_BASE_URL}/Interview/index.htm?sc.keyword=${encodeURIComponent(searchQuery)}`;

  await limiter.acquire();

  const response = await axios.get(searchUrl, {
    headers: {
      "User-Agent": USER_AGENT,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
    timeout: 15_000,
    maxRedirects: 5,
    validateStatus: (status) => status < 500,
  });

  const $ = cheerio.load(response.data);

  // Parse interview experiences
  $("[class*='InterviewCard'], [class*='interview-card'], .interview, [data-test='interview-review']").each((_index, element) => {
    try {
      const el = $(element);

      const roleText = el.find("[class*='role'], [class*='title'], h3").first().text().trim() || role || null;

      // Difficulty
      const difficultyText = el.find("[class*='difficulty'], [data-test='difficulty']").first().text().trim();
      const difficulty = difficultyText || null;

      // Experience (positive/neutral/negative)
      const experienceText = el.find("[class*='experience'], [data-test='experience']").first().text().trim().toLowerCase();
      let experience: "positive" | "neutral" | "negative" | null = null;
      if (experienceText.includes("positive")) experience = "positive";
      else if (experienceText.includes("negative")) experience = "negative";
      else if (experienceText.includes("neutral") || experienceText.includes("mixed")) experience = "neutral";

      // Questions
      const questions: string[] = [];
      el.find("[class*='question'], li, [data-test='interview-question']").each((_qi, qEl) => {
        const q = $(qEl).text().trim();
        if (q && q.length > 10 && q.length < 500) {
          questions.push(q);
        }
      });

      // Process description
      const processText = el.find("[class*='process'], [class*='description'], [data-test='interview-process'], p").first().text().trim();
      const process = processText || null;

      // Offer status
      const offerText = el.find("[class*='offer'], [data-test='offer']").first().text().trim().toLowerCase();
      let offer: boolean | null = null;
      if (offerText.includes("accepted") || offerText.includes("received") || offerText.includes("yes")) offer = true;
      else if (/\b(declined|rejected|no)\b/.test(offerText)) offer = false;  // word match: "no" must not hit "know"/"not"

      // Date
      const dateText = el.find("[class*='date'], time").first().text().trim();
      const date = dateText || null;

      experiences.push({
        company,
        role: roleText,
        difficulty,
        experience,
        questions,
        process,
        offer,
        date,
      });
    } catch (innerErr) {
      console.error("Error parsing individual Glassdoor interview:", innerErr);
    }
  });

  if (experiences.length === 0) {
    throw new Error("no interview experiences parsed — likely bot-blocked or the company has no reviews");
  }

  return experiences;
}

/**
 * Get interview experiences from Glassdoor (scraper, cached 24h).
 * Never throws — failures land in meta.
 */
export async function getGlassdoorInterviews(
  company: string,
  role?: string
): Promise<SourceResult<InterviewExperience>> {
  if (!SCRAPERS_ENABLED) {
    return { meta: { source: "Glassdoor", tier: "scraper", state: "skipped", detail: SCRAPERS_DISABLED_DETAIL }, items: [] };
  }
  const res = await fetchWithCache(
    "glassdoor-interviews",
    { company: company.toLowerCase().trim(), role: role?.toLowerCase().trim() || null },
    LOOKUP_TTL_MS,
    () => fetchInterviews(company, role)
  );
  return toSourceResult("Glassdoor", "scraper", res);
}
