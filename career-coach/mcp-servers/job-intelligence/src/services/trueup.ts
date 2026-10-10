/**
 * TrueUp HTML scraper — best-effort fallback source (scraper tier) for job
 * search and the only source for trending roles. Failures are reported
 * honestly via SourceMeta; job searches are cached 6h, trending roles 6h.
 */

import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, SCRAPERS_DISABLED_DETAIL, SCRAPERS_ENABLED, USER_AGENT } from "../constants.js";
import type { JobListing, SourceResult, TrendingRole } from "../types.js";
import { fetchWithCache, SEARCH_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.trueup);

const TRUEUP_BASE_URL = "https://www.trueup.io";
const TRUEUP_SEARCH_URL = `${TRUEUP_BASE_URL}/jobs`;
const TRUEUP_TRENDING_URL = `${TRUEUP_BASE_URL}/trending`;

/** Fetch and parse TrueUp job search. Throws when nothing could be parsed. */
async function fetchTrueUpJobs(query: string, limit: number): Promise<JobListing[]> {
  const listings: JobListing[] = [];

  const params = new URLSearchParams();
  params.set("search", query);
  const url = `${TRUEUP_SEARCH_URL}?${params.toString()}`;

  await limiter.acquire();

  const response = await axios.get(url, {
    headers: {
      "User-Agent": USER_AGENT,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
    timeout: 15_000,
    maxRedirects: 5,
  });

  const $ = cheerio.load(response.data);

  // TrueUp job cards
  $("[class*='job-card'], [class*='JobCard'], .job-listing, tr[class*='job'], a[href*='/jobs/']").each((_index, element) => {
    if (listings.length >= limit) return;

    try {
      const el = $(element);

      const titleEl = el.find("h3, h4, [class*='title'], [class*='Title']").first();
      const title = titleEl.text().trim() || el.find("a").first().text().trim();

      const companyEl = el.find("[class*='company'], [class*='Company'], span:first-child").first();
      const company = companyEl.text().trim();

      const locationEl = el.find("[class*='location'], [class*='Location']").first();
      const location = locationEl.text().trim();

      const linkEl = el.is("a") ? el : el.find("a[href*='/jobs/']").first();
      const relativeUrl = linkEl.attr("href") || "";
      const jobUrl = relativeUrl.startsWith("http") ? relativeUrl : `${TRUEUP_BASE_URL}${relativeUrl}`;

      const salaryEl = el.find("[class*='salary'], [class*='Salary'], [class*='comp']").first();
      const salary = salaryEl.length > 0 ? salaryEl.text().trim() : null;

      if (title && company) {
        listings.push({
          title,
          company,
          location: location || "Not specified",
          salary,
          url: jobUrl,
          description: "View full description on TrueUp",
          posted_date: null,
          source: "trueup",
        });
      }
    } catch (innerErr) {
      console.error("Error parsing individual TrueUp listing:", innerErr);
    }
  });

  if (listings.length === 0) {
    throw new Error("no listings parsed — the site structure may have changed");
  }

  return listings.slice(0, limit);
}

/** Search TrueUp jobs (scraper, cached 6h). Never throws — failures land in meta. */
export async function searchTrueUpJobs(
  query: string,
  limit: number = 10
): Promise<SourceResult<JobListing>> {
  if (!SCRAPERS_ENABLED) {
    return { meta: { source: "TrueUp", tier: "scraper", state: "skipped", detail: SCRAPERS_DISABLED_DETAIL }, items: [] };
  }
  const res = await fetchWithCache(
    "trueup-jobs",
    { query: query.toLowerCase().trim(), limit },
    SEARCH_TTL_MS,
    () => fetchTrueUpJobs(query, limit)
  );
  return toSourceResult("TrueUp", "scraper", res);
}

/** Fetch and parse TrueUp trending roles. Throws when nothing could be parsed. */
async function fetchTrendingRoles(industry?: string): Promise<TrendingRole[]> {
  const roles: TrendingRole[] = [];

  const url = industry
    ? `${TRUEUP_TRENDING_URL}?industry=${encodeURIComponent(industry)}`
    : TRUEUP_TRENDING_URL;

  await limiter.acquire();

  const response = await axios.get(url, {
    headers: {
      "User-Agent": USER_AGENT,
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
    timeout: 15_000,
    maxRedirects: 5,
  });

  const $ = cheerio.load(response.data);

  // Parse trending role cards/rows
  $("[class*='trending'], [class*='Trending'], [class*='role-card'], table tbody tr, .card").each((_index, element) => {
    try {
      const el = $(element);

      const titleEl = el.find("h3, h4, td:first-child, [class*='title'], [class*='role']").first();
      const title = titleEl.text().trim();

      // Parse companies hiring
      const companiesText = el.find("[class*='companies'], [class*='Companies'], td:nth-child(2)").first().text().trim();
      const companies_hiring = companiesText
        ? companiesText.split(/[,|]/).map((c: string) => c.trim()).filter(Boolean)
        : [];

      const growthEl = el.find("[class*='growth'], [class*='Growth'], td:nth-child(3)").first();
      const growth_rate = growthEl.length > 0 ? growthEl.text().trim() : null;

      const salaryEl = el.find("[class*='salary'], [class*='Salary'], [class*='comp'], td:nth-child(4)").first();
      const avg_salary = salaryEl.length > 0 ? salaryEl.text().trim() : null;

      const demandEl = el.find("[class*='demand'], [class*='Demand'], td:nth-child(5)").first();
      const demandText = demandEl.text().trim().toLowerCase();
      let demand_level: "high" | "medium" | "low" | null = null;
      if (demandText.includes("high")) demand_level = "high";
      else if (demandText.includes("medium") || demandText.includes("moderate")) demand_level = "medium";
      else if (demandText.includes("low")) demand_level = "low";

      if (title) {
        roles.push({
          title,
          companies_hiring,
          growth_rate,
          avg_salary,
          demand_level,
        });
      }
    } catch (innerErr) {
      console.error("Error parsing individual TrueUp trending role:", innerErr);
    }
  });

  if (roles.length === 0) {
    throw new Error("no trending roles parsed — the site may be unavailable or its structure changed");
  }

  return roles;
}

/** Get TrueUp trending roles (scraper, cached 6h). Never throws — failures land in meta. */
export async function getTrueUpTrendingRoles(
  industry?: string
): Promise<SourceResult<TrendingRole>> {
  if (!SCRAPERS_ENABLED) {
    return { meta: { source: "TrueUp", tier: "scraper", state: "skipped", detail: SCRAPERS_DISABLED_DETAIL }, items: [] };
  }
  const res = await fetchWithCache(
    "trueup-trending",
    { industry: industry?.toLowerCase().trim() || null },
    SEARCH_TTL_MS,
    () => fetchTrendingRoles(industry)
  );
  return toSourceResult("TrueUp", "scraper", res);
}
