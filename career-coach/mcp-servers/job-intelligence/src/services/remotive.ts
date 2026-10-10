/**
 * Remotive public API — keyless JSON, remote jobs only.
 * https://remotive.com/api/remote-jobs?search=<q>&limit=<n>
 *
 * Primary (API-tier) source for job_search_jobs. Remotive's docs block
 * clients that call more than twice a minute and advise fetching at most ~4
 * times a day, so we fetch the whole feed once and cache it for 6h, then
 * filter locally (every query term must appear in title/company/tags/
 * description). Remotive's own `search` matched loosely anyway. Listings link
 * back to Remotive and name it as the source, as its terms require.
 */

import axios from "axios";
import { API_USER_AGENT, RATE_LIMITS } from "../constants.js";
import type { JobListing, SourceResult } from "../types.js";
import { fetchWithCache, SEARCH_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";
import { stripHtml, truncate } from "./text-utils.js";

const limiter = new RateLimiter(RATE_LIMITS.remotive);

const REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs";

interface RemotiveJob {
  id?: number;
  url?: string;
  title?: string;
  company_name?: string;
  tags?: string[];
  candidate_required_location?: string;
  salary?: string;
  job_type?: string;
  publication_date?: string;
  description?: string;
}

function matchesAllTerms(job: RemotiveJob, terms: string[]): boolean {
  const haystack = [
    job.title,
    job.company_name,
    (job.tags || []).join(" "),
    job.description,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return terms.every((t) => haystack.includes(t));
}

async function fetchRemotiveFeed(): Promise<RemotiveJob[]> {
  await limiter.acquire();

  const response = await axios.get(REMOTIVE_API_URL, {
    headers: { "User-Agent": API_USER_AGENT, Accept: "application/json" },
    timeout: 15_000,
  });

  const jobs: unknown = response.data?.jobs;
  if (!Array.isArray(jobs)) {
    throw new Error("unexpected Remotive response shape (no jobs array)");
  }

  return jobs as RemotiveJob[];
}

function toListings(jobs: RemotiveJob[], query: string): JobListing[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const listings: JobListing[] = [];
  for (const raw of jobs) {
    if (!raw?.title || !raw.company_name) continue;
    if (!matchesAllTerms(raw, terms)) continue;
    listings.push({
      title: raw.title,
      company: raw.company_name,
      location: raw.candidate_required_location
        ? `Remote (${raw.candidate_required_location})`
        : "Remote",
      salary: raw.salary?.trim() || null,
      url: raw.url || "https://remotive.com",
      description: raw.description
        ? truncate(stripHtml(raw.description), 300)
        : "No description available",
      posted_date: raw.publication_date || null,
      source: "remotive",
    });
  }
  return listings;
}

/** Search Remotive remote jobs. Never throws — failures land in meta. */
export async function searchRemotiveJobs(
  query: string,
  limit: number = 10
): Promise<SourceResult<JobListing>> {
  const res = await fetchWithCache("remotive-feed", {}, SEARCH_TTL_MS, fetchRemotiveFeed);
  if (res.ok) {
    const items = toListings(res.value, query).slice(0, limit);
    return {
      meta: { source: "Remotive", tier: "api", state: res.state, count: items.length, ageMs: res.ageMs },
      items,
    };
  }
  return toSourceResult("Remotive", "api", res);
}
