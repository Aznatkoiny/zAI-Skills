/**
 * Adzuna jobs API — keyed JSON (free tier available).
 * https://api.adzuna.com/v1/api/jobs/us/search/1?app_id=..&app_key=..
 *
 * Requires ADZUNA_APP_ID and ADZUNA_APP_KEY in the environment; when unset
 * the source is skipped entirely with an honest note in the Sources footer.
 * Results are cached for 6h (cache keys never include the credentials).
 */

import axios from "axios";
import { API_USER_AGENT, RATE_LIMITS } from "../constants.js";
import type { JobListing, SourceResult } from "../types.js";
import { fetchWithCache, SEARCH_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";
import { formatSalaryRange, stripHtml, truncate } from "./text-utils.js";

const limiter = new RateLimiter(RATE_LIMITS.adzuna);

const ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1";

interface AdzunaResult {
  title?: string;
  description?: string;
  created?: string;
  company?: { display_name?: string };
  location?: { display_name?: string };
  salary_min?: number;
  salary_max?: number;
  redirect_url?: string;
}

async function fetchAdzunaJobs(
  appId: string,
  appKey: string,
  query: string,
  location: string | undefined,
  salaryMin: number | undefined,
  limit: number
): Promise<JobListing[]> {
  await limiter.acquire();

  const params: Record<string, string | number> = {
    app_id: appId,
    app_key: appKey,
    what: query,
    results_per_page: limit,
    "content-type": "application/json",
  };
  if (location) params.where = location;
  if (salaryMin) params.salary_min = salaryMin;

  const response = await axios.get(ADZUNA_API_URL, {
    params,
    headers: { "User-Agent": API_USER_AGENT, Accept: "application/json" },
    timeout: 15_000,
  });

  const results: unknown = response.data?.results;
  if (!Array.isArray(results)) {
    throw new Error("unexpected Adzuna response shape (no results array)");
  }

  const listings: JobListing[] = [];
  for (const raw of results as AdzunaResult[]) {
    if (!raw?.title) continue;
    listings.push({
      title: stripHtml(raw.title), // Adzuna may embed <strong> match markers
      company: raw.company?.display_name || "Unknown company",
      location: raw.location?.display_name || "Not specified",
      salary: formatSalaryRange(raw.salary_min, raw.salary_max),
      url: raw.redirect_url || "https://www.adzuna.com",
      description: raw.description
        ? truncate(stripHtml(raw.description), 300)
        : "No description available",
      posted_date: raw.created || null,
      source: "adzuna",
    });
  }
  return listings;
}

/**
 * Search Adzuna (US index). Never throws — failures land in meta, and the
 * source reports "skipped" when no API credentials are configured.
 */
export async function searchAdzunaJobs(
  query: string,
  location: string | undefined,
  salaryMin: number | undefined,
  limit: number = 10
): Promise<SourceResult<JobListing>> {
  const appId = process.env.ADZUNA_APP_ID?.trim();
  const appKey = process.env.ADZUNA_APP_KEY?.trim();

  if (!appId || !appKey) {
    return {
      meta: {
        source: "Adzuna",
        tier: "api",
        state: "skipped",
        detail: "no API key — set ADZUNA_APP_ID and ADZUNA_APP_KEY to enable",
      },
      items: [],
    };
  }

  const res = await fetchWithCache(
    "adzuna",
    // Credentials are deliberately excluded from the cache key.
    { query: query.toLowerCase().trim(), location: location || null, salaryMin: salaryMin || null, limit },
    SEARCH_TTL_MS,
    () => fetchAdzunaJobs(appId, appKey, query, location, salaryMin, limit)
  );
  return toSourceResult("Adzuna", "api", res);
}
