/**
 * job_get_company_info — live open roles from the company's public
 * Greenhouse/Lever board when one exists (API, always on), plus the Glassdoor
 * company profile (HTML scraper, only with JOB_INTEL_ENABLE_SCRAPERS=1). Each
 * source degrades independently and the response ends with a Sources footer.
 */

import { z } from "zod";
import { companyInfoSchema } from "../schemas/inputs.js";
import { getCompanyBoardJobs } from "../services/company-boards.js";
import { getGlassdoorCompanyInfo } from "../services/glassdoor.js";
import { finalizeOutput, formatSourcesFooter } from "./sources-footer.js";

type CompanyInfoInput = z.infer<typeof companyInfoSchema>;

const MAX_OPEN_ROLES_SHOWN = 10;

export async function handleCompanyInfo(input: CompanyInfoInput): Promise<string> {
  const { company_name } = input;

  // Glassdoor scraper and ATS board API in parallel — each fails soft.
  const [glassdoor, board] = await Promise.all([
    getGlassdoorCompanyInfo(company_name),
    getCompanyBoardJobs(company_name),
  ]);

  const info = glassdoor.info;

  const lines: string[] = [
    `## Company Profile: ${info?.name || company_name}`,
    "",
  ];

  const footerLines = formatSourcesFooter([board.meta, glassdoor.meta]);

  if (info) {
    // Overview section
    lines.push("### Overview");
    lines.push("");
    lines.push("| Detail | Value |");
    lines.push("|--------|-------|");
    lines.push(`| Company | ${info.name} |`);
    lines.push(`| Industry | ${info.industry || "Not available"} |`);
    lines.push(`| Size | ${info.size || "Not available"} |`);
    lines.push(`| Headquarters | ${info.headquarters || "Not available"} |`);
    lines.push(`| Founded | ${info.founded || "Not available"} |`);
    lines.push(`| Revenue | ${info.revenue || "Not available"} |`);
    lines.push("");

    // Ratings section
    lines.push("### Ratings");
    lines.push("");

    if (info.rating !== null) {
      lines.push(`**Overall Rating:** ${info.rating.toFixed(1)} / 5.0`);
      lines.push("");

      // Visual rating bar
      const filledStars = Math.round(info.rating);
      const emptyStars = 5 - filledStars;
      lines.push(`Rating: ${"*".repeat(filledStars)}${"_".repeat(emptyStars)}`);
      lines.push("");
    } else {
      lines.push("Overall rating not available.");
      lines.push("");
    }

    if (info.culture_ratings && Object.keys(info.culture_ratings).length > 0) {
      lines.push("#### Culture & Values Ratings");
      lines.push("");
      lines.push("| Category | Rating |");
      lines.push("|----------|--------|");

      for (const [category, rating] of Object.entries(info.culture_ratings)) {
        lines.push(`| ${category} | ${rating.toFixed(1)} / 5.0 |`);
      }
      lines.push("");
    }

  } else if (glassdoor.meta.state === "skipped") {
    lines.push("Ratings and company details come from Glassdoor. This source is a website scraper, which is off by default because the site restricts automated access. Use WebSearch instead; the user can opt in by setting JOB_INTEL_ENABLE_SCRAPERS=1 (after checking the site's terms) and restarting Claude Code.");
    lines.push("");
  } else {
    lines.push(`No Glassdoor profile could be retrieved for "${company_name}" (see Sources below). Use WebSearch for company background.`);
    lines.push("");
  }

  // Open roles from the company's public ATS board (Greenhouse/Lever).
  if (board.items.length > 0) {
    const total = board.items.length;
    lines.push(`### Open Roles (${board.meta.source})`);
    lines.push("");
    lines.push(`${total} open role${total === 1 ? "" : "s"} on the company's public job board:`);
    lines.push("");

    for (const job of board.items.slice(0, MAX_OPEN_ROLES_SHOWN)) {
      lines.push(`- [${job.title}](${job.url}) — ${job.location}`);
    }
    if (total > MAX_OPEN_ROLES_SHOWN) {
      lines.push(`- ...and ${total - MAX_OPEN_ROLES_SHOWN} more (use job_search_jobs with the company name to explore)`);
    }
    lines.push("");
  }

  lines.push("*Ratings/culture data come from Glassdoor and may lag; open roles come from the company's own job board. See Sources for per-source status.*");

  return finalizeOutput(lines, footerLines);
}
