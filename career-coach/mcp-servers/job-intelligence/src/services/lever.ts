/**
 * Lever public postings API — keyless JSON.
 * https://api.lever.co/v0/postings/<company>?mode=json
 *
 * Used when a specific company is queried (job_get_company_info, or a
 * job_search_jobs query that names a known company). Postings are cached
 * for 6h. A 404 means no public board under that slug — callers fail soft.
 */

import axios from "axios";
import { API_USER_AGENT, RATE_LIMITS } from "../constants.js";
import type { JobListing } from "../types.js";
import { type CachedFetchResult, fetchWithCache, SEARCH_TTL_MS } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";
import { truncate } from "./text-utils.js";

const limiter = new RateLimiter(RATE_LIMITS.lever);

interface LeverPosting {
  text?: string; // job title
  hostedUrl?: string;
  categories?: { location?: string; team?: string; commitment?: string };
  createdAt?: number; // epoch ms
  descriptionPlain?: string;
  workplaceType?: string;
}

async function fetchPostings(companySlug: string, companyName: string): Promise<JobListing[]> {
  await limiter.acquire();

  const url = `https://api.lever.co/v0/postings/${encodeURIComponent(companySlug)}?mode=json`;
  const response = await axios.get(url, {
    headers: { "User-Agent": API_USER_AGENT, Accept: "application/json" },
    timeout: 15_000,
    validateStatus: (status) => status === 200 || status === 404,
  });

  if (response.status === 404) {
    throw new Error(`no public Lever board named "${companySlug}"`);
  }

  if (!Array.isArray(response.data)) {
    throw new Error("unexpected Lever response shape (not an array)");
  }

  const listings: JobListing[] = [];
  for (const raw of response.data as LeverPosting[]) {
    if (!raw?.text) continue;
    const location = raw.categories?.location?.trim();
    listings.push({
      title: raw.text,
      company: companyName,
      location:
        location ||
        (raw.workplaceType === "remote" ? "Remote" : "Not specified"),
      salary: null, // postings API does not expose compensation
      url: raw.hostedUrl || `https://jobs.lever.co/${companySlug}`,
      description: raw.descriptionPlain
        ? truncate(raw.descriptionPlain.replace(/\s+/g, " ").trim(), 300)
        : "View full description on the company's Lever board",
      posted_date: raw.createdAt ? new Date(raw.createdAt).toISOString().slice(0, 10) : null,
      source: "lever",
    });
  }
  return listings;
}

/**
 * Fetch all open postings on a company's public Lever board (cached 6h).
 * Rejects via CachedFetchResult.ok=false when the board does not exist.
 */
export async function getLeverBoardJobs(
  companySlug: string,
  companyName: string
): Promise<CachedFetchResult<JobListing[]>> {
  return fetchWithCache("lever", { board: companySlug }, SEARCH_TTL_MS, () =>
    fetchPostings(companySlug, companyName)
  );
}
