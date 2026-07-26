/**
 * job_get_salary_data — aggregates Glassdoor and Levels.fyi (both scraper
 * tier, cached 24h). Each source degrades independently and the response
 * ends with an honest Sources footer.
 */

import { z } from "zod";
import { salaryDataSchema } from "../schemas/inputs.js";
import { getGlassdoorSalaries } from "../services/glassdoor.js";
import { getLevelsSalaryData } from "../services/levelsfyi.js";
import type { SalaryData } from "../types.js";
import { MAX_SALARY_COMPARISONS } from "../constants.js";
import { finalizeOutput, formatSourcesFooter } from "./sources-footer.js";

type SalaryDataInput = z.infer<typeof salaryDataSchema>;

function formatDollar(amount: number | null): string {
  if (amount === null) return "N/A";
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`;
  return `$${amount.toLocaleString()}`;
}

export async function handleSalaryData(input: SalaryDataInput): Promise<string> {
  const { role, company, location } = input;

  // Query both sources in parallel — services never throw; failures land in meta.
  const [glassdoor, levels] = await Promise.all([
    getGlassdoorSalaries(role, company),
    getLevelsSalaryData(role, company, location),
  ]);

  const allSalaries: SalaryData[] = [...glassdoor.items, ...levels.items];
  const footerLines = formatSourcesFooter([glassdoor.meta, levels.meta]);

  // Trim to max comparisons
  const displaySalaries = allSalaries.slice(0, MAX_SALARY_COMPARISONS);

  // Format as markdown
  const lines: string[] = [
    `## Salary Data: ${role}`,
    "",
  ];

  if (company) lines.push(`**Company:** ${company}`);
  if (location) lines.push(`**Location:** ${location}`);
  lines.push(`**Entries:** ${allSalaries.length} total (see Sources below)`);
  lines.push("");

  if (displaySalaries.length === 0) {
    lines.push(`No salary data found for "${role}"${company ? ` at ${company}` : ""}. Try broadening your search (e.g., remove the company filter or use a more common role title), or fall back to WebSearch.`);
    return finalizeOutput(lines, footerLines);
  }

  // Comparison table
  lines.push("### Compensation Breakdown");
  lines.push("");
  lines.push("| # | Role | Company | Base | Equity | Bonus | Total Comp | Level | Source |");
  lines.push("|---|------|---------|------|--------|-------|------------|-------|--------|");

  for (let i = 0; i < displaySalaries.length; i++) {
    const s = displaySalaries[i];
    lines.push(
      `| ${i + 1} | ${s.role} | ${s.company || "N/A"} | ${formatDollar(s.base)} | ${formatDollar(s.equity)} | ${formatDollar(s.bonus)} | ${formatDollar(s.total_comp)} | ${s.level || "N/A"} | ${s.source} |`
    );
  }
  lines.push("");

  // Summary statistics if we have enough data
  const validTotals = allSalaries.map((s) => s.total_comp).filter((t): t is number => t !== null);
  const validBases = allSalaries.map((s) => s.base).filter((b): b is number => b !== null);

  if (validTotals.length >= 2 || validBases.length >= 2) {
    lines.push("### Summary Statistics");
    lines.push("");

    if (validTotals.length >= 2) {
      const sortedTotals = validTotals.sort((a, b) => a - b);
      const median = sortedTotals.length % 2 === 0
        ? (sortedTotals[sortedTotals.length / 2 - 1] + sortedTotals[sortedTotals.length / 2]) / 2
        : sortedTotals[Math.floor(sortedTotals.length / 2)];
      const avg = validTotals.reduce((sum, v) => sum + v, 0) / validTotals.length;

      lines.push("**Total Compensation:**");
      lines.push(`- Median: ${formatDollar(median)}`);
      lines.push(`- Average: ${formatDollar(Math.round(avg))}`);
      lines.push(`- Range: ${formatDollar(sortedTotals[0])} - ${formatDollar(sortedTotals[sortedTotals.length - 1])}`);
      lines.push("");
    }

    if (validBases.length >= 2) {
      const sortedBases = validBases.sort((a, b) => a - b);
      const median = sortedBases.length % 2 === 0
        ? (sortedBases[sortedBases.length / 2 - 1] + sortedBases[sortedBases.length / 2]) / 2
        : sortedBases[Math.floor(sortedBases.length / 2)];
      const avg = validBases.reduce((sum, v) => sum + v, 0) / validBases.length;

      lines.push("**Base Salary:**");
      lines.push(`- Median: ${formatDollar(median)}`);
      lines.push(`- Average: ${formatDollar(Math.round(avg))}`);
      lines.push(`- Range: ${formatDollar(sortedBases[0])} - ${formatDollar(sortedBases[sortedBases.length - 1])}`);
      lines.push("");
    }
  }

  lines.push("*Data aggregated from Glassdoor and Levels.fyi (scraper-backed, cached up to 24h). Compensation figures are self-reported and may not reflect current offers.*");

  return finalizeOutput(lines, footerLines);
}
