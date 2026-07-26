/**
 * Company ATS board lookup — routes a company name to its public
 * Greenhouse or Lever job board.
 *
 * Strategy: consult a small static map of well-known board slugs first;
 * otherwise slugify the company name and try Greenhouse, then Lever,
 * heuristically. Everything fails soft — a miss is reported in SourceMeta,
 * never thrown.
 *
 * The static map is best-effort: companies migrate ATS vendors, so entries
 * may drift. A wrong entry only costs one soft-failing request.
 */

import type { JobListing, SourceResult } from "../types.js";
import { getGreenhouseBoardJobs } from "./greenhouse.js";
import { getLeverBoardJobs } from "./lever.js";
import type { CachedFetchResult } from "./cache.js";

type BoardProvider = "greenhouse" | "lever";

interface BoardRef {
  provider: BoardProvider;
  slug: string;
}

// ~30 well-known companies with public Greenhouse/Lever boards (best-effort,
// verified at time of writing; keyed by lowercase company name).
const KNOWN_BOARDS: Record<string, BoardRef> = {
  stripe: { provider: "greenhouse", slug: "stripe" },
  airbnb: { provider: "greenhouse", slug: "airbnb" },
  coinbase: { provider: "greenhouse", slug: "coinbase" },
  dropbox: { provider: "greenhouse", slug: "dropbox" },
  gitlab: { provider: "greenhouse", slug: "gitlab" },
  doordash: { provider: "greenhouse", slug: "doordash" },
  instacart: { provider: "greenhouse", slug: "instacart" },
  reddit: { provider: "greenhouse", slug: "reddit" },
  pinterest: { provider: "greenhouse", slug: "pinterest" },
  databricks: { provider: "greenhouse", slug: "databricks" },
  figma: { provider: "greenhouse", slug: "figma" },
  brex: { provider: "greenhouse", slug: "brex" },
  gusto: { provider: "greenhouse", slug: "gusto" },
  robinhood: { provider: "greenhouse", slug: "robinhood" },
  lyft: { provider: "greenhouse", slug: "lyft" },
  asana: { provider: "greenhouse", slug: "asana" },
  anthropic: { provider: "greenhouse", slug: "anthropic" },
  cloudflare: { provider: "greenhouse", slug: "cloudflare" },
  datadog: { provider: "greenhouse", slug: "datadog" },
  mongodb: { provider: "greenhouse", slug: "mongodb" },
  okta: { provider: "greenhouse", slug: "okta" },
  hashicorp: { provider: "greenhouse", slug: "hashicorp" },
  vercel: { provider: "greenhouse", slug: "vercel" },
  discord: { provider: "greenhouse", slug: "discord" },
  duolingo: { provider: "greenhouse", slug: "duolingo" },
  affirm: { provider: "greenhouse", slug: "affirm" },
  flexport: { provider: "greenhouse", slug: "flexport" },
  checkr: { provider: "greenhouse", slug: "checkr" },
  netflix: { provider: "lever", slug: "netflix" },
  palantir: { provider: "lever", slug: "palantir" },
  plaid: { provider: "lever", slug: "plaid" },
  ramp: { provider: "lever", slug: "ramp" },
  attentive: { provider: "lever", slug: "attentive" },
};

/** Lowercase a company name into an ATS-style slug ("Scale AI" -> "scaleai"). */
function slugify(company: string): string {
  return company.toLowerCase().replace(/[^a-z0-9]+/g, "");
}

/**
 * Scan a free-text search query for a known company name (word-boundary
 * match against the static map). Returns the matched map key, or null.
 */
export function findKnownCompanyInQuery(query: string): string | null {
  const q = query.toLowerCase();
  for (const name of Object.keys(KNOWN_BOARDS)) {
    if (new RegExp(`\\b${name}\\b`).test(q)) return name;
  }
  return null;
}

function providerLabel(provider: BoardProvider, slug: string): string {
  return provider === "greenhouse" ? `Greenhouse board (${slug})` : `Lever board (${slug})`;
}

/**
 * Fetch open roles from a company's public ATS board, failing soft.
 *
 * opts.filterTerms: keep only jobs whose title contains every term
 * (used by job_search_jobs so a board query respects the role part of
 * the search). opts.limit trims the result count.
 */
export async function getCompanyBoardJobs(
  company: string,
  opts: { filterTerms?: string[]; limit?: number } = {}
): Promise<SourceResult<JobListing>> {
  const normalized = company.toLowerCase().trim();
  const known = KNOWN_BOARDS[normalized];

  const candidates: BoardRef[] = known
    ? [known]
    : [
        { provider: "greenhouse", slug: slugify(company) },
        { provider: "lever", slug: slugify(company) },
      ];

  const failures: string[] = [];

  for (const candidate of candidates) {
    if (!candidate.slug) continue;

    const res: CachedFetchResult<JobListing[]> =
      candidate.provider === "greenhouse"
        ? await getGreenhouseBoardJobs(candidate.slug, company)
        : await getLeverBoardJobs(candidate.slug, company);

    if (res.ok) {
      let items = res.value;
      const terms = (opts.filterTerms || []).map((t) => t.toLowerCase()).filter(Boolean);
      if (terms.length > 0) {
        items = items.filter((job) => {
          const title = job.title.toLowerCase();
          return terms.every((t) => title.includes(t));
        });
      }
      if (typeof opts.limit === "number") items = items.slice(0, opts.limit);

      return {
        meta: {
          source: providerLabel(candidate.provider, candidate.slug),
          tier: "api",
          state: res.state,
          count: items.length,
          ageMs: res.ageMs,
        },
        items,
      };
    }
    failures.push(res.reason);
  }

  return {
    meta: {
      source: "Company job board",
      tier: "api",
      state: "failed",
      detail: `no public Greenhouse/Lever board found for "${company}" (${failures.join("; ")})`,
    },
    items: [],
  };
}
