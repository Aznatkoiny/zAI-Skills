/**
 * LinkedIn guest-search HTML scraper — best-effort fallback source
 * (scraper tier). LinkedIn aggressively bot-blocks; failures are reported
 * honestly via SourceMeta and successful results are cached for 6h.
 */

import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, USER_AGENT } from "../constants.js";
import type { JobListing, SourceResult } from "../types.js";
import { fetchWithCache, SEARCH_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.linkedin);

// LinkedIn guest job search — no auth required
const LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search";

function buildLinkedInUrl(query: string, location?: string, remote?: boolean, start: number = 0): string {
  const params = new URLSearchParams();
  params.set("keywords", query);
  if (location) {
    params.set("location", location);
  }
  if (remote) {
    // LinkedIn remote filter: f_WT=2 means remote
    params.set("f_WT", "2");
  }
  params.set("start", start.toString());
  params.set("sortBy", "R"); // Relevance
  return `${LINKEDIN_JOBS_URL}?${params.toString()}`;
}

function parseLinkedInListings($: cheerio.CheerioAPI): JobListing[] {
  const listings: JobListing[] = [];

  try {
    $("li, .base-card, .job-search-card").each((_index, element) => {
      try {
        const el = $(element);

        const titleEl = el.find("h3.base-search-card__title, .job-search-card__title, h3 a").first();
        const title = titleEl.text().trim();

        const linkEl = el.find("a.base-card__full-link, a[data-tracking-control-name]").first();
        const url = linkEl.attr("href") || "";

        const company = el.find("h4.base-search-card__subtitle a, .base-search-card__subtitle, .job-search-card__company-name").first().text().trim();
        const location = el.find(".job-search-card__location, .base-search-card__metadata span").first().text().trim();

        const salaryEl = el.find(".job-search-card__salary-info, .salary-info").first();
        const salary = salaryEl.length > 0 ? salaryEl.text().trim() : null;

        const dateEl = el.find("time, .job-search-card__listdate").first();
        const posted_date = dateEl.attr("datetime") || dateEl.text().trim() || null;

        if (title && company) {
          listings.push({
            title,
            company,
            location: location || "Not specified",
            salary,
            url: url.startsWith("http") ? url.split("?")[0] : `https://www.linkedin.com${url.split("?")[0]}`,
            description: "View full description on LinkedIn",
            posted_date,
            source: "linkedin",
          });
        }
      } catch (innerErr) {
        console.error("Error parsing individual LinkedIn listing:", innerErr);
      }
    });
  } catch (err) {
    console.error("Error parsing LinkedIn results page:", err);
  }

  return listings;
}

/**
 * Fetch and parse LinkedIn guest-search pages. Throws when nothing could
 * be fetched/parsed so failures are never cached.
 */
async function fetchLinkedInJobs(
  query: string,
  location: string | undefined,
  remote: boolean | undefined,
  limit: number
): Promise<JobListing[]> {
  const allListings: JobListing[] = [];

  // LinkedIn guest API returns ~25 results per request
  const pagesToFetch = Math.ceil(limit / 25);
  const maxPages = Math.min(pagesToFetch, 2);

  for (let page = 0; page < maxPages; page++) {
    if (allListings.length >= limit) break;

    const url = buildLinkedInUrl(query, location, remote, page * 25);
    await limiter.acquire();

    try {
      const response = await axios.get(url, {
        headers: {
          "User-Agent": USER_AGENT,
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.9",
          "Sec-Fetch-Mode": "navigate",
        },
        timeout: 15_000,
        maxRedirects: 5,
      });

      const $ = cheerio.load(response.data);
      const pageListings = parseLinkedInListings($);

      if (pageListings.length === 0) break;
      allListings.push(...pageListings);
    } catch (err) {
      // Keep partial results from earlier pages; fail only if we have nothing.
      if (allListings.length > 0) break;
      const message = err instanceof Error ? err.message : String(err);
      throw new Error(`${message} — LinkedIn aggressively blocks automated requests`);
    }
  }

  if (allListings.length === 0) {
    throw new Error("no listings parsed — likely bot-blocked or the HTML structure changed");
  }

  return allListings.slice(0, limit);
}

/** Search LinkedIn (scraper, cached 6h). Never throws — failures land in meta. */
export async function searchLinkedInJobs(
  query: string,
  location?: string,
  remote?: boolean,
  limit: number = 10
): Promise<SourceResult<JobListing>> {
  const res = await fetchWithCache(
    "linkedin",
    { query: query.toLowerCase().trim(), location: location || null, remote: !!remote, limit },
    SEARCH_TTL_MS,
    () => fetchLinkedInJobs(query, location, remote, limit)
  );
  return toSourceResult("LinkedIn", "scraper", res);
}
