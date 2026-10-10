/**
 * job_get_salary_data — Levels.fyi total compensation (markdown routes, on by
 * default) plus Glassdoor base pay (HTML scraper, only when
 * JOB_INTEL_ENABLE_SCRAPERS=1). The two measure different things (total comp
 * vs base pay), so summary statistics are reported per source, never mixed.
 * Cached 24h; the response ends with an honest Sources footer.
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
    getLevelsSalaryData(role, company),
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

  // Summary statistics per source: Levels.fyi reports total compensation and
  // Glassdoor reports base pay, so pooling them would describe neither.
  const statLines = (label: string, values: number[]) => {
    const sorted = [...values].sort((a, b) => a - b);
    const median = sorted.length % 2 === 0
      ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
      : sorted[Math.floor(sorted.length / 2)];
    lines.push(`**${label}** (${values.length} figures): median ${formatDollar(median)}, range ${formatDollar(sorted[0])} - ${formatDollar(sorted[sorted.length - 1])}`);
  };
  // Levels.fyi rows are already medians (per level, or percentiles), so its
  // headline figure is the median it reports, not a statistic over the rows.
  const levelsMedian = allSalaries.find(
    (s) => s.source === "levelsfyi" && /^(All levels \(median\)|Median, all companies)$/.test(s.level ?? "")
  );
  const glassdoorBases = allSalaries.filter((s) => s.source === "glassdoor").map((s) => s.base).filter((b): b is number => b !== null);
  if (levelsMedian || glassdoorBases.length >= 2) {
    lines.push("### Summary by source");
    lines.push("");
    if (levelsMedian?.total_comp != null) {
      lines.push(`**Levels.fyi median total compensation** (${levelsMedian.level}): ${formatDollar(levelsMedian.total_comp)}`);
    }
    if (glassdoorBases.length >= 2) statLines("Glassdoor base pay", glassdoorBases);
    lines.push("");
  }

  if (location) {
    lines.push(`*Levels.fyi figures are US-wide (its pages have no city filter), so they don't reflect ${location} specifically.*`);
  }
  lines.push("*Data source: Levels.fyi (https://www.levels.fyi) for total compensation; Glassdoor for base pay when enabled. Figures are self-reported and may not reflect current offers. Cached up to 24h.*");

  return finalizeOutput(lines, footerLines);
}
