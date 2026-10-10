/**
 * Indeed HTML scraper — best-effort fallback source (scraper tier).
 * Indeed frequently bot-blocks; failures are reported honestly via
 * SourceMeta and successful results are cached for 6h.
 */

import axios from "axios";
import * as cheerio from "cheerio";
import { RATE_LIMITS, SCRAPERS_DISABLED_DETAIL, SCRAPERS_ENABLED, USER_AGENT } from "../constants.js";
import type { JobListing, SourceResult } from "../types.js";
import { fetchWithCache, SEARCH_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.indeed);

const INDEED_BASE_URL = "https://www.indeed.com/jobs";

// Indeed paginates with `start` offsets in increments of 10
const INDEED_PAGE_SIZE = 10;

function buildIndeedUrl(query: string, location?: string, remote?: boolean, start: number = 0): string {
  const params = new URLSearchParams();
  params.set("q", query);
  if (location) {
    params.set("l", location);
  }
  if (remote) {
    params.set("remotejob", "032b3046-06a3-4876-8dfd-474eb5e7ed11");
  }
  params.set("start", start.toString());
  return `${INDEED_BASE_URL}?${params.toString()}`;
}

function parseIndeedListings($: cheerio.CheerioAPI): JobListing[] {
  const listings: JobListing[] = [];

  try {
    $(".job_seen_beacon, .jobsearch-ResultsList .result, .resultContent").each((_index, element) => {
      try {
        const el = $(element);

        const titleEl = el.find("h2.jobTitle a, .jobTitle > a, a[data-jk]").first();
        const title = titleEl.text().trim();
        const relativeUrl = titleEl.attr("href") || "";
        const url = relativeUrl.startsWith("http") ? relativeUrl : `https://www.indeed.com${relativeUrl}`;

        const company = el.find("[data-testid='company-name'], .companyName, .company").first().text().trim();
        const location = el.find("[data-testid='text-location'], .companyLocation, .location").first().text().trim();

        const salaryEl = el.find(".salary-snippet-container, .salaryText, [data-testid='attribute_snippet_testid']").first();
        const salary = salaryEl.length > 0 ? salaryEl.text().trim() : null;

        const description = el.find(".job-snippet, .summary, [data-testid='jobDescriptionText']").first().text().trim();
        const dateEl = el.find(".date, .visually-hidden-date, span.css-qvloho").first();
        const posted_date = dateEl.length > 0 ? dateEl.text().trim() : null;

        if (title && company) {
          listings.push({
            title,
            company,
            location: location || "Not specified",
            salary,
            url,
            description: description || "No description available",
            posted_date,
            source: "indeed",
          });
        }
      } catch (innerErr) {
        console.error("Error parsing individual Indeed listing:", innerErr);
      }
    });
  } catch (err) {
    console.error("Error parsing Indeed results page:", err);
  }

  return listings;
}

/**
 * Fetch and parse Indeed result pages. Throws when nothing could be
 * fetched/parsed (bot-block or markup drift) so failures are never cached.
 */
async function fetchIndeedJobs(
  query: string,
  location: string | undefined,
  remote: boolean | undefined,
  limit: number
): Promise<JobListing[]> {
  const allListings: JobListing[] = [];

  // Fetch up to 2 pages if needed
  const pagesToFetch = Math.ceil(limit / INDEED_PAGE_SIZE);
  const maxPages = Math.min(pagesToFetch, 2);

  for (let page = 0; page < maxPages; page++) {
    if (allListings.length >= limit) break;

    const url = buildIndeedUrl(query, location, remote, page * INDEED_PAGE_SIZE);
    await limiter.acquire();

    try {
      const response = await axios.get(url, {
        headers: {
          "User-Agent": USER_AGENT,
          Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.9",
          "Accept-Encoding": "gzip, deflate, br",
        },
        timeout: 15_000,
        maxRedirects: 5,
      });

      const $ = cheerio.load(response.data);
      const pageListings = parseIndeedListings($);

      if (pageListings.length === 0) break;
      allListings.push(...pageListings);
    } catch (err) {
      // Keep partial results from earlier pages; fail only if we have nothing.
      if (allListings.length > 0) break;
      const message = err instanceof Error ? err.message : String(err);
      throw new Error(`${message} — Indeed may be blocking automated requests`);
    }
  }

  if (allListings.length === 0) {
    throw new Error("no listings parsed — likely bot-blocked or the HTML structure changed");
  }

  return allListings.slice(0, limit);
}

/** Search Indeed (scraper, cached 6h). Never throws — failures land in meta. */
export async function searchIndeedJobs(
  query: string,
  location?: string,
  remote?: boolean,
  limit: number = 10
): Promise<SourceResult<JobListing>> {
  if (!SCRAPERS_ENABLED) {
    return { meta: { source: "Indeed", tier: "scraper", state: "skipped", detail: SCRAPERS_DISABLED_DETAIL }, items: [] };
  }
  const res = await fetchWithCache(
    "indeed",
    { query: query.toLowerCase().trim(), location: location || null, remote: !!remote, limit },
    SEARCH_TTL_MS,
    () => fetchIndeedJobs(query, location, remote, limit)
  );
  return toSourceResult("Indeed", "scraper", res);
}
