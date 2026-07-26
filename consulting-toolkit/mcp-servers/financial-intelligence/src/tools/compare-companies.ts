import { z } from "zod";
import { compareCompaniesSchema } from "../schemas/inputs.js";
import { getFinancialMetrics } from "../services/edgar.js";

type CompareInput = z.infer<typeof compareCompaniesSchema>;

// Metrics where a lower value is better; every other metric ranks highest first
const LOWER_IS_BETTER = new Set(["total_debt", "total_liabilities", "cost_of_revenue"]);

function formatValue(value: number | null): string {
  if (value === null) return "—";
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

export async function handleCompareCompanies(input: CompareInput): Promise<string> {
  const { tickers, metrics, period } = input;

  // Fetch financials for all companies
  const results = await Promise.all(
    tickers.map(async (ticker) => {
      try {
        return await getFinancialMetrics(ticker, metrics, period, 1);
      } catch (err) {
        return { error: ticker, message: err instanceof Error ? err.message : "Unknown error" };
      }
    })
  );

  const lines: string[] = [
    `## Company Comparison`,
    "",
    `**Companies:** ${tickers.join(", ")}`,
    `**Period:** Most recent ${period}`,
    "",
  ];

  // Identify failed lookups
  const errors = results.filter((r) => "error" in r);
  const successes = results.filter((r) => !("error" in r));

  if (errors.length > 0) {
    lines.push("### Warnings");
    for (const e of errors as { error: string; message: string }[]) {
      lines.push(`- **${e.error}**: ${e.message}`);
    }
    lines.push("");
  }

  if (successes.length === 0) {
    lines.push("*No financial data could be retrieved for any of the specified companies.*");
    return lines.join("\n");
  }

  // Build comparison table
  const companyData = successes as Awaited<ReturnType<typeof getFinancialMetrics>>[];
  const companyHeaders = companyData.map((c) => `${c.company.ticker}`);

  lines.push("### Financial Comparison");
  lines.push("");
  lines.push(`| Metric | ${companyHeaders.join(" | ")} |`);
  lines.push(`|--------|${companyHeaders.map(() => "-------").join("|")}|`);

  // Company info rows
  lines.push(`| **Name** | ${companyData.map((c) => c.company.name).join(" | ")} |`);
  lines.push(`| **SIC** | ${companyData.map((c) => `${c.company.sic}`).join(" | ")} |`);

  // Metric rows
  for (const metricName of metrics) {
    const values: (number | null)[] = companyData.map((c) => {
      const metric = c.metrics.find((m) => m.metric === metricName);
      return metric?.periods[0]?.value ?? null;
    });

    const formatted = values.map(formatValue);
    lines.push(`| **${metricName}** | ${formatted.join(" | ")} |`);
  }

  // Derived metric rows
  const derivedNames = new Set<string>();
  for (const c of companyData) {
    for (const d of c.derived) derivedNames.add(d.metric);
  }

  for (const derivedName of derivedNames) {
    const values = companyData.map((c) => {
      const d = c.derived.find((dm) => dm.metric === derivedName);
      const val = d?.periods[0]?.value ?? null;
      if (val === null) return "—";
      if (derivedName.includes("pct") || derivedName.includes("margin") || derivedName.includes("growth")) {
        return `${val.toFixed(1)}%`;
      }
      return formatValue(val);
    });
    lines.push(`| **${derivedName}** | ${values.join(" | ")} |`);
  }

  // Rankings for each metric
  lines.push("");
  lines.push("### Rankings (rank 1 = best)");
  lines.push("");
  lines.push("*Rank 1 is the highest value, except for metrics marked \"lower is better\" (debt and cost metrics), where rank 1 is the lowest value.*");
  lines.push("");
  lines.push(`| Metric | ${companyHeaders.join(" | ")} |`);
  lines.push(`|--------|${companyHeaders.map(() => "-------").join("|")}|`);

  for (const metricName of metrics) {
    const values: { ticker: string; value: number | null }[] = companyData.map((c) => {
      const metric = c.metrics.find((m) => m.metric === metricName);
      return { ticker: c.company.ticker, value: metric?.periods[0]?.value ?? null };
    });

    // Sort best-first per metric direction, nulls excluded
    const lowerIsBetter = LOWER_IS_BETTER.has(metricName);
    const sorted = [...values]
      .filter((v) => v.value !== null)
      .sort((a, b) =>
        lowerIsBetter
          ? (a.value as number) - (b.value as number)
          : (b.value as number) - (a.value as number)
      );

    const rankings = companyData.map((c) => {
      const rank = sorted.findIndex((s) => s.ticker === c.company.ticker);
      return rank >= 0 ? `#${rank + 1}` : "—";
    });

    const label = lowerIsBetter ? `**${metricName}** (lower is better)` : `**${metricName}**`;
    lines.push(`| ${label} | ${rankings.join(" | ")} |`);
  }

  lines.push("");
  lines.push(`*Data source: SEC EDGAR XBRL | ${companyData.length} companies compared*`);

  return lines.join("\n");
}
