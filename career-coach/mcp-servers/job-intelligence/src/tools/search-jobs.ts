/**
 * job_search_jobs — API-first aggregation.
 *
 * Primary sources (queried in parallel): Remotive, RemoteOK (keyless
 * public APIs), Adzuna and USAJOBS (keyed; skipped with a note when env
 * keys are unset), plus the matching company's public Greenhouse/Lever
 * board when the query names a well-known company. The Indeed/TrueUp
 * scrapers are off unless JOB_INTEL_ENABLE_SCRAPERS=1, and even then run
 * only when the API tier didn't return enough results. Remote-only sources
 * ignore location, so for a non-remote location search their results don't
 * count toward "enough".
 */

import { z } from "zod";
import { searchJobsSchema } from "../schemas/inputs.js";
import { searchAdzunaJobs } from "../services/adzuna.js";
import { findKnownCompanyInQuery, getCompanyBoardJobs } from "../services/company-boards.js";
import { searchIndeedJobs } from "../services/indeed.js";
import { searchRemotiveJobs } from "../services/remotive.js";
import { searchRemoteOkJobs } from "../services/remoteok.js";
import { searchTrueUpJobs } from "../services/trueup.js";
import { searchUsaJobs } from "../services/usajobs.js";
import type { JobListing, SourceMeta, SourceResult } from "../types.js";
import { finalizeOutput, formatSourcesFooter } from "./sources-footer.js";

type SearchJobsInput = z.infer<typeof searchJobsSchema>;

const HOURS_PER_YEAR = 2080; // 40 hours/week * 52 weeks

/**
 * Best-effort parse of a salary string into an annualized USD maximum.
 * Handles K/M suffixes ("$150K"), ranges ("$120K - $180K" -> 180000), and
 * hourly rates ("$50 - $70 an hour" -> 70 * 2080). Returns null when no
 * number can be extracted.
 */
function parseAnnualSalaryMax(salary: string): number | null {
  let max: number | null = null;

  for (const match of salary.matchAll(/\$?(\d[\d,]*(?:\.\d+)?)\s*([kKmM])?/g)) {
    let value = parseFloat(match[1].replace(/,/g, ""));
    if (isNaN(value)) continue;

    const suffix = match[2]?.toLowerCase();
    if (suffix === "k") value *= 1_000;
    else if (suffix === "m") value *= 1_000_000;

    if (max === null || value > max) max = value;
  }

  if (max === null) return null;

  // Annualize hourly rates ("$50 an hour", "$35/hr", "hourly")
  if (/hour|\bhr\b/i.test(salary)) {
    max *= HOURS_PER_YEAR;
  }

  return max;
}

/**
 * Deduplicate job listings by company+title+location (case-insensitive), so
 * the same role in different cities is not collapsed.
 * Prefers listings with more data (salary, description).
 */
function deduplicateListings(listings: JobListing[]): JobListing[] {
  const seen = new Map<string, JobListing>();

  for (const listing of listings) {
    const key = `${listing.company.toLowerCase().trim()}|${listing.title.toLowerCase().trim()}|${listing.location.toLowerCase().trim()}`;
    const existing = seen.get(key);

    if (!existing) {
      seen.set(key, listing);
    } else {
      // Prefer listing with more data
      const existingScore = (existing.salary ? 1 : 0) + (existing.description.length > 50 ? 1 : 0) + (existing.posted_date ? 1 : 0);
      const newScore = (listing.salary ? 1 : 0) + (listing.description.length > 50 ? 1 : 0) + (listing.posted_date ? 1 : 0);
      if (newScore > existingScore) {
        seen.set(key, listing);
      }
    }
  }

  return Array.from(seen.values());
}

/**
 * Sort listings by relevance: exact title match first, then partial match, then the rest.
 */
function sortByRelevance(listings: JobListing[], query: string): JobListing[] {
  const queryLower = query.toLowerCase().trim();

  return listings.sort((a, b) => {
    const aTitle = a.title.toLowerCase();
    const bTitle = b.title.toLowerCase();

    const aExact = aTitle === queryLower ? 2 : aTitle.includes(queryLower) ? 1 : 0;
    const bExact = bTitle === queryLower ? 2 : bTitle.includes(queryLower) ? 1 : 0;

    if (aExact !== bExact) return bExact - aExact;

    // Secondary sort: prefer listings with salary info
    const aSalary = a.salary ? 1 : 0;
    const bSalary = b.salary ? 1 : 0;
    return bSalary - aSalary;
  });
}

// Remotive and RemoteOK list exclusively remote jobs; other sources need a
// text check when the user asks for remote-only results.
function isRemoteListing(listing: JobListing): boolean {
  if (listing.source === "remotive" || listing.source === "remoteok") return true;
  return /\bremote\b/i.test(`${listing.location} ${listing.title} ${listing.description}`);
}

/** Run an array of never-throwing source searches, mapping any unexpected rejection to a failed meta. */
async function runSources(
  calls: Array<{ name: string; tier: SourceMeta["tier"]; run: () => Promise<SourceResult<JobListing>> }>
): Promise<SourceResult<JobListing>[]> {
  const settled = await Promise.allSettled(calls.map((c) => c.run()));
  return settled.map((result, i) => {
    if (result.status === "fulfilled") return result.value;
    return {
      meta: {
        source: calls[i].name,
        tier: calls[i].tier,
        state: "failed" as const,
        detail: result.reason instanceof Error ? result.reason.message : String(result.reason),
      },
      items: [],
    };
  });
}

export async function handleSearchJobs(input: SearchJobsInput): Promise<string> {
  const { query, location, remote, salary_min, experience_level, limit } = input;

  // Experience-level keywords help the scrapers' full-page search but would
  // over-constrain the APIs' term matching, so only scrapers get them.
  let enhancedQuery = query;
  if (experience_level) {
    const levelMap: Record<string, string> = {
      entry: "entry level junior",
      mid: "mid level",
      senior: "senior",
      lead: "lead principal staff",
      executive: "executive director VP",
    };
    enhancedQuery = `${query} ${levelMap[experience_level] || ""}`.trim();
  }

  // ── Tier 1: API sources in parallel ──
  const apiCalls: Array<{ name: string; tier: SourceMeta["tier"]; run: () => Promise<SourceResult<JobListing>> }> = [
    { name: "Remotive", tier: "api", run: () => searchRemotiveJobs(query, limit) },
    { name: "RemoteOK", tier: "api", run: () => searchRemoteOkJobs(query, limit) },
    { name: "Adzuna", tier: "api", run: () => searchAdzunaJobs(query, location, salary_min, limit) },
    { name: "USAJOBS", tier: "api", run: () => searchUsaJobs(query, location, limit) },
  ];

  // If the query names a well-known company, also pull its public
  // Greenhouse/Lever board, filtering board titles by the non-company terms.
  const knownCompany = findKnownCompanyInQuery(query);
  if (knownCompany) {
    const filterTerms = query
      .toLowerCase()
      .split(/\s+/)
      .filter((t) => t && t !== knownCompany);
    apiCalls.push({
      name: "Company job board",
      tier: "api",
      run: () => getCompanyBoardJobs(knownCompany, { filterTerms, limit }),
    });
  }

  const apiResults = await runSources(apiCalls);

  let apiListings = apiResults.flatMap((r) => r.items);
  if (remote) {
    apiListings = apiListings.filter(isRemoteListing);
  }

  // ── Tier 2: scrapers, only when the APIs did not fill the request ──
  // For a specific (non-remote) location, remote-only listings can't satisfy
  // the request, so they don't count toward the limit.
  const wantsSpecificLocation = !!location && !remote && !/\bremote\b/i.test(location);
  const locationRelevant = wantsSpecificLocation
    ? apiListings.filter((l) => l.source !== "remotive" && l.source !== "remoteok")
    : apiListings;
  const scraperNames = ["Indeed", "TrueUp"];
  let scraperResults: SourceResult<JobListing>[];

  if (deduplicateListings(locationRelevant).length >= limit) {
    scraperResults = scraperNames.map((name) => ({
      meta: {
        source: name,
        tier: "scraper" as const,
        state: "skipped" as const,
        detail: "API sources already returned enough results",
      },
      items: [],
    }));
  } else {
    scraperResults = await runSources([
      { name: "Indeed", tier: "scraper", run: () => searchIndeedJobs(enhancedQuery, location, remote, limit) },
      { name: "TrueUp", tier: "scraper", run: () => searchTrueUpJobs(enhancedQuery, limit) },
    ]);
  }

  const allListings = [...apiListings, ...scraperResults.flatMap((r) => r.items)];

  // Deduplicate and sort
  let finalListings = deduplicateListings(allListings);
  finalListings = sortByRelevance(finalListings, query);
  if (wantsSpecificLocation) {
    // Stable partition: listings that can match the requested location first.
    finalListings = [
      ...finalListings.filter((l) => l.source !== "remotive" && l.source !== "remoteok"),
      ...finalListings.filter((l) => l.source === "remotive" || l.source === "remoteok"),
    ];
  }

  // Apply salary filter if specified
  if (salary_min) {
    finalListings = finalListings.filter((listing) => {
      if (!listing.salary) return true; // Keep listings without salary info
      const annualMax = parseAnnualSalaryMax(listing.salary);
      if (annualMax === null) return true; // Keep unparseable salary strings
      return annualMax >= salary_min;
    });
  }

  // Trim to requested limit
  finalListings = finalListings.slice(0, limit);

  // Format as markdown
  const lines: string[] = [
    `## Job Search Results: "${query}"`,
    "",
  ];

  if (location) lines.push(`**Location:** ${location}`);
  if (remote) lines.push(`**Remote:** Yes`);
  if (experience_level) lines.push(`**Experience Level:** ${experience_level}`);
  if (salary_min) lines.push(`**Minimum Salary:** $${salary_min.toLocaleString()}`);
  lines.push(`**Results:** ${finalListings.length} listings (deduplicated; see Sources below)`);
  lines.push("");

  const footerLines = formatSourcesFooter([
    ...apiResults.map((r) => r.meta),
    ...scraperResults.map((r) => r.meta),
  ]);

  if (finalListings.length === 0) {
    lines.push("No job listings found matching your criteria. Try broadening your search terms or removing filters. If all sources failed, fall back to WebSearch.");
    return finalizeOutput(lines, footerLines);
  }

  // Markdown table
  lines.push("| # | Title | Company | Location | Salary | Source |");
  lines.push("|---|-------|---------|----------|--------|--------|");

  for (let i = 0; i < finalListings.length; i++) {
    const job = finalListings[i];
    const title = job.url ? `[${job.title}](${job.url})` : job.title;
    const salary = job.salary || "Not listed";
    lines.push(`| ${i + 1} | ${title} | ${job.company} | ${job.location} | ${salary} | ${job.source} |`);
  }

  lines.push("");

  // Add detail sections for top results
  const detailCount = Math.min(5, finalListings.length);
  if (detailCount > 0) {
    lines.push("### Top Result Details");
    lines.push("");

    for (let i = 0; i < detailCount; i++) {
      const job = finalListings[i];
      lines.push(`**${i + 1}. ${job.title}** at ${job.company}`);
      if (job.description && !job.description.startsWith("View full description")) {
        const desc = job.description.length > 200 ? job.description.substring(0, 200) + "..." : job.description;
        lines.push(`> ${desc}`);
      }
      if (job.posted_date) lines.push(`*Posted: ${job.posted_date}*`);
      if (job.url) lines.push(`[View listing](${job.url})`);
      lines.push("");
    }
  }

  if (wantsSpecificLocation) {
    lines.push("*Remotive and RemoteOK list remote jobs only and ignore location; Adzuna (US) and USAJOBS filter by location when their keys are set. Listing snippets are short: open the listing URL for the full description.*");
  } else {
    lines.push("*Listing snippets are short: open the listing URL for the full description. Listings change quickly.*");
  }

  return finalizeOutput(lines, footerLines);
}
