/**
 * RemoteOK public API — keyless JSON feed of remote jobs.
 * https://remoteok.com/api
 *
 * The API returns the full recent-jobs feed (no search parameter), so we
 * cache the whole feed for 6h and filter client-side per query. RemoteOK
 * rejects generic/empty user agents and asks integrators to identify
 * themselves, hence the honest API_USER_AGENT.
 */

import axios from "axios";
import { API_USER_AGENT, RATE_LIMITS } from "../constants.js";
import type { JobListing, SourceResult } from "../types.js";
import { fetchWithCache, SEARCH_TTL_MS, toSourceResult } from "./cache.js";
import { RateLimiter } from "./rate-limiter.js";
import { formatSalaryRange, stripHtml, truncate } from "./text-utils.js";

const limiter = new RateLimiter(RATE_LIMITS.remoteok);

const REMOTEOK_API_URL = "https://remoteok.com/api";

interface RemoteOkPost {
  legal?: string; // first feed element is a legal notice, not a job
  id?: string | number;
  position?: string;
  company?: string;
  tags?: string[];
  description?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  url?: string;
  date?: string;
}

async function fetchRemoteOkFeed(): Promise<RemoteOkPost[]> {
  await limiter.acquire();

  const response = await axios.get(REMOTEOK_API_URL, {
    headers: { "User-Agent": API_USER_AGENT, Accept: "application/json" },
    timeout: 15_000,
  });

  if (!Array.isArray(response.data)) {
    throw new Error("unexpected RemoteOK response shape (not an array)");
  }
  // Drop the leading legal-notice element and anything without a position.
  return (response.data as RemoteOkPost[]).filter((p) => p?.position && p.company);
}

function toListing(post: RemoteOkPost): JobListing {
  return {
    title: post.position || "Unknown role",
    company: post.company || "Unknown company",
    location: post.location?.trim() || "Remote",
    salary: formatSalaryRange(post.salary_min, post.salary_max),
    url: post.url || "https://remoteok.com",
    description: post.description
      ? truncate(stripHtml(post.description), 300)
      : "No description available",
    posted_date: post.date || null,
    source: "remoteok",
  };
}

/**
 * Search RemoteOK by filtering the cached feed: a post matches when every
 * query term appears in its position/company/tags/location/description.
 * Never throws — failures land in meta.
 */
export async function searchRemoteOkJobs(
  query: string,
  limit: number = 10
): Promise<SourceResult<JobListing>> {
  const res = await fetchWithCache("remoteok", { feed: "all" }, SEARCH_TTL_MS, fetchRemoteOkFeed);

  if (!res.ok) {
    return { meta: { source: "RemoteOK", tier: "api", state: "failed", detail: res.reason }, items: [] };
  }

  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const items = res.value
    .filter((post) => {
      const haystack = [
        post.position,
        post.company,
        (post.tags || []).join(" "),
        post.location,
        post.description,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return terms.every((t) => haystack.includes(t));
    })
    .slice(0, limit)
    .map(toListing);

  return {
    meta: { source: "RemoteOK", tier: "api", state: res.state, count: items.length, ageMs: res.ageMs },
    items,
  };
}
