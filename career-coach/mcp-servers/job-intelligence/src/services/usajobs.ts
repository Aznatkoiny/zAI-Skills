/**
 * USAJOBS search API — keyed JSON (free API key; US federal jobs).
 * https://data.usajobs.gov/api/search?Keyword=<q>
 *
 * Requires USAJOBS_API_KEY (Authorization-Key header) and USAJOBS_EMAIL
 * (User-Agent header — USAJOBS requires the registered email there). When
 * either is unset the source is skipped with an honest note. Results are
 * cached for 6h (cache keys never include the credentials).
 */

import axios from "axios";
import { RATE_LIMITS } from "../constants.js";
import type { JobListing, SourceResult } from "../types.js";
import { fetchWithCache, SEARCH_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";
import { stripHtml, truncate } from "./text-utils.js";

const limiter = new RateLimiter(RATE_LIMITS.usajobs);

const USAJOBS_API_URL = "https://data.usajobs.gov/api/search";

interface UsaJobsRemuneration {
  MinimumRange?: string;
  MaximumRange?: string;
  RateIntervalCode?: string; // "PA" per annum, "PH" per hour
}

interface UsaJobsDescriptor {
  PositionTitle?: string;
  OrganizationName?: string;
  PositionLocationDisplay?: string;
  PositionURI?: string;
  PublicationStartDate?: string;
  PositionRemuneration?: UsaJobsRemuneration[];
  UserArea?: { Details?: { JobSummary?: string } };
}

function formatRemuneration(rem: UsaJobsRemuneration | undefined): string | null {
  if (!rem) return null;
  const min = parseFloat(rem.MinimumRange || "");
  const max = parseFloat(rem.MaximumRange || "");
  if (isNaN(min) && isNaN(max)) return null;

  const fmt = (n: number) => `$${Math.round(n).toLocaleString()}`;
  let range: string;
  if (!isNaN(min) && !isNaN(max) && max !== min) range = `${fmt(min)} - ${fmt(max)}`;
  else range = fmt(!isNaN(max) ? max : min);

  // Mark hourly rates so the salary filter's annualization logic triggers.
  if (rem.RateIntervalCode === "PH") return `${range} an hour`;
  return range;
}

async function fetchUsaJobs(
  apiKey: string,
  email: string,
  query: string,
  location: string | undefined,
  limit: number
): Promise<JobListing[]> {
  await limiter.acquire();

  const params: Record<string, string | number> = {
    Keyword: query,
    ResultsPerPage: limit,
  };
  if (location) params.LocationName = location;

  const response = await axios.get(USAJOBS_API_URL, {
    params,
    headers: {
      "Authorization-Key": apiKey,
      // USAJOBS requires the registered email address as the User-Agent.
      "User-Agent": email,
      Accept: "application/json",
    },
    timeout: 15_000,
  });

  const items: unknown = response.data?.SearchResult?.SearchResultItems;
  if (!Array.isArray(items)) {
    throw new Error("unexpected USAJOBS response shape (no SearchResultItems)");
  }

  const listings: JobListing[] = [];
  for (const item of items as Array<{ MatchedObjectDescriptor?: UsaJobsDescriptor }>) {
    const d = item?.MatchedObjectDescriptor;
    if (!d?.PositionTitle) continue;
    listings.push({
      title: d.PositionTitle,
      company: d.OrganizationName || "US Federal Government",
      location: d.PositionLocationDisplay || "Not specified",
      salary: formatRemuneration(d.PositionRemuneration?.[0]),
      url: d.PositionURI || "https://www.usajobs.gov",
      description: d.UserArea?.Details?.JobSummary
        ? truncate(stripHtml(d.UserArea.Details.JobSummary), 300)
        : "View full description on USAJOBS",
      posted_date: d.PublicationStartDate || null,
      source: "usajobs",
    });
  }
  return listings;
}

/**
 * Search USAJOBS (US federal listings). Never throws — failures land in
 * meta, and the source reports "skipped" when credentials are missing.
 */
export async function searchUsaJobs(
  query: string,
  location: string | undefined,
  limit: number = 10
): Promise<SourceResult<JobListing>> {
  const apiKey = process.env.USAJOBS_API_KEY?.trim();
  const email = process.env.USAJOBS_EMAIL?.trim();

  if (!apiKey || !email) {
    return {
      meta: {
        source: "USAJOBS",
        tier: "api",
        state: "skipped",
        detail: "no API key — set USAJOBS_API_KEY and USAJOBS_EMAIL to enable",
      },
      items: [],
    };
  }

  const res = await fetchWithCache(
    "usajobs",
    // Credentials are deliberately excluded from the cache key.
    { query: query.toLowerCase().trim(), location: location || null, limit },
    SEARCH_TTL_MS,
    () => fetchUsaJobs(apiKey, email, query, location, limit)
  );
  return toSourceResult("USAJOBS", "api", res);
}
