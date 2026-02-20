import { z } from "zod";
import { searchJobsSchema } from "../schemas/inputs.js";
import { searchIndeedJobs } from "../services/indeed.js";
import { searchLinkedInJobs } from "../services/linkedin.js";
import { searchTrueUpJobs } from "../services/trueup.js";
import type { JobListing } from "../types.js";
import { CHARACTER_LIMIT } from "../constants.js";

type SearchJobsInput = z.infer<typeof searchJobsSchema>;

/**
 * Deduplicate job listings by company+title (case-insensitive).
 * Prefers listings with more data (salary, description).
 */
function deduplicateListings(listings: JobListing[]): JobListing[] {
  const seen = new Map<string, JobListing>();

  for (const listing of listings) {
    const key = `${listing.company.toLowerCase().trim()}|${listing.title.toLowerCase().trim()}`;
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

export async function handleSearchJobs(input: SearchJobsInput): Promise<string> {
  const { query, location, remote, salary_min, experience_level, limit } = input;

  // Build experience level query modifier
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

  // Query all 3 sources in parallel
  const results = await Promise.allSettled([
    searchIndeedJobs(enhancedQuery, location, remote, limit),
    searchLinkedInJobs(enhancedQuery, location, remote, limit),
    searchTrueUpJobs(enhancedQuery, limit),
  ]);

  const allListings: JobListing[] = [];
  const sourceStatus: string[] = [];

  // Collect results from each source
  const sourceNames = ["Indeed", "LinkedIn", "TrueUp"];
  for (let i = 0; i < results.length; i++) {
    const result = results[i];
    if (result.status === "fulfilled") {
      const listings = result.value;
      const errorListings = listings.filter((l) => l.title.startsWith("["));
      const validListings = listings.filter((l) => !l.title.startsWith("["));

      if (validListings.length > 0) {
        allListings.push(...validListings);
        sourceStatus.push(`${sourceNames[i]}: ${validListings.length} results`);
      } else if (errorListings.length > 0) {
        sourceStatus.push(`${sourceNames[i]}: error (see notes)`);
      } else {
        sourceStatus.push(`${sourceNames[i]}: 0 results`);
      }
    } else {
      sourceStatus.push(`${sourceNames[i]}: failed (${result.reason})`);
    }
  }

  // Deduplicate and sort
  let finalListings = deduplicateListings(allListings);
  finalListings = sortByRelevance(finalListings, query);

  // Apply salary filter if specified
  if (salary_min) {
    finalListings = finalListings.filter((listing) => {
      if (!listing.salary) return true; // Keep listings without salary info
      const salaryMatch = listing.salary.match(/\$?([\d,]+)/);
      if (!salaryMatch) return true;
      const salaryNum = parseInt(salaryMatch[1].replace(/,/g, ""), 10);
      return salaryNum >= salary_min;
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
  lines.push(`**Sources:** ${sourceStatus.join(" | ")}`);
  lines.push(`**Results:** ${finalListings.length} listings (deduplicated)`);
  lines.push("");

  if (finalListings.length === 0) {
    lines.push("No job listings found matching your criteria. Try broadening your search terms or removing filters.");
    return lines.join("\n");
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
      if (job.description && job.description !== "View full description on LinkedIn" && job.description !== "View full description on TrueUp") {
        const desc = job.description.length > 200 ? job.description.substring(0, 200) + "..." : job.description;
        lines.push(`> ${desc}`);
      }
      if (job.posted_date) lines.push(`*Posted: ${job.posted_date}*`);
      if (job.url) lines.push(`[View listing](${job.url})`);
      lines.push("");
    }
  }

  lines.push("*Data aggregated from Indeed, LinkedIn, and TrueUp. Listings may change rapidly.*");

  // Truncate if over character limit
  let result = lines.join("\n");
  if (result.length > CHARACTER_LIMIT) {
    result = result.substring(0, CHARACTER_LIMIT - 50) + "\n\n*[Output truncated due to length]*";
  }

  return result;
}
