/**
 * Greenhouse public job-board API — keyless JSON.
 * https://boards-api.greenhouse.io/v1/boards/<board>/jobs
 *
 * Used when a specific company is queried (job_get_company_info, or a
 * job_search_jobs query that names a known company). Boards are cached for
 * 6h. A 404 means no public board under that slug — callers fail soft.
 */

import axios from "axios";
import { API_USER_AGENT, RATE_LIMITS } from "../constants.js";
import type { JobListing } from "../types.js";
import { type CachedFetchResult, fetchWithCache, SEARCH_TTL_MS } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";

const limiter = new RateLimiter(RATE_LIMITS.greenhouse);

interface GreenhouseJob {
  absolute_url?: string;
  title?: string;
  location?: { name?: string };
  updated_at?: string;
}

async function fetchBoardJobs(boardSlug: string, companyName: string): Promise<JobListing[]> {
  await limiter.acquire();

  const url = `https://boards-api.greenhouse.io/v1/boards/${encodeURIComponent(boardSlug)}/jobs`;
  const response = await axios.get(url, {
    headers: { "User-Agent": API_USER_AGENT, Accept: "application/json" },
    timeout: 15_000,
    validateStatus: (status) => status === 200 || status === 404,
  });

  if (response.status === 404) {
    throw new Error(`no public Greenhouse board named "${boardSlug}"`);
  }

  const jobs: unknown = response.data?.jobs;
  if (!Array.isArray(jobs)) {
    throw new Error("unexpected Greenhouse response shape (no jobs array)");
  }

  const listings: JobListing[] = [];
  for (const raw of jobs as GreenhouseJob[]) {
    if (!raw?.title) continue;
    listings.push({
      title: raw.title,
      company: companyName,
      location: raw.location?.name?.trim() || "Not specified",
      salary: null, // board API does not expose compensation
      url: raw.absolute_url || `https://boards.greenhouse.io/${boardSlug}`,
      description: "View full description on the company's Greenhouse board",
      posted_date: raw.updated_at || null,
      source: "greenhouse",
    });
  }
  return listings;
}

/**
 * Fetch all open roles on a company's public Greenhouse board (cached 6h).
 * Rejects via CachedFetchResult.ok=false when the board does not exist.
 */
export async function getGreenhouseBoardJobs(
  boardSlug: string,
  companyName: string
): Promise<CachedFetchResult<JobListing[]>> {
  return fetchWithCache("greenhouse", { board: boardSlug }, SEARCH_TTL_MS, () =>
    fetchBoardJobs(boardSlug, companyName)
  );
}
