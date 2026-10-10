import { z } from "zod";
import { companyFinancialsSchema } from "../schemas/inputs.js";
import { getFinancialMetrics } from "../services/edgar.js";

type FinancialsInput = z.infer<typeof companyFinancialsSchema>;

function formatValue(value: number, metric = ""): string {
  // Share counts aren't money; EPS is money per share and stays unscaled.
  const unit = metric.includes("shares") ? "" : "$";
  if (metric.includes("eps")) return `$${value.toFixed(2)}`;
  if (Math.abs(value) >= 1e9) return `${unit}${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `${unit}${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e3) return `${unit}${(value / 1e3).toFixed(2)}K`;
  return `${unit}${value.toFixed(2)}`;
}

export async function handleCompanyFinancials(input: FinancialsInput): Promise<string> {
  const identifier = input.ticker || input.cik;
  if (!identifier) {
    throw new Error("Either ticker or cik must be provided.");
  }

  const { company, metrics, derived } = await getFinancialMetrics(
    identifier,
    input.metrics,
    input.period,
    input.limit
  );

  const lines: string[] = [
    `## ${company.name} (${company.ticker})`,
    "",
    `| Field | Value |`,
    `|-------|-------|`,
    `| CIK | ${company.cik} |`,
    `| SIC | ${company.sic} — ${company.sicDescription} |`,
    `| Exchange(s) | ${company.exchanges.join(", ") || "N/A"} |`,
    "",
  ];

  // Financial metrics table
  if (metrics.length > 0) {
    // Collect all unique periods across metrics
    const allPeriods = new Set<string>();
    for (const m of metrics) {
      for (const p of m.periods) allPeriods.add(p.period);
    }
    const periods = Array.from(allPeriods).sort().reverse();

    if (periods.length > 0) {
      lines.push(`### Financial Metrics (${input.period})`);
      lines.push("");
      lines.push(`| Metric | ${periods.join(" | ")} |`);
      lines.push(`|--------|${periods.map(() => "-------").join("|")}|`);
      // Period end dates, so each figure can be cited precisely.
      const endFor = (label: string) => {
        for (const m of metrics) {
          const hit = m.periods.find((mp) => mp.period === label);
          if (hit) return hit.endDate;
        }
        return "—";
      };
      lines.push(`| period end | ${periods.map(endFor).join(" | ")} |`);

      for (const m of metrics) {
        const values = periods.map((p) => {
          const match = m.periods.find((mp) => mp.period === p);
          return match ? formatValue(match.value, m.metric) : "—";
        });
        lines.push(`| ${m.metric} | ${values.join(" | ")} |`);
      }

      // Derived metrics
      for (const d of derived) {
        const values = periods.map((p) => {
          const match = d.periods.find((dp) => dp.period === p);
          if (!match || match.value === null) return "—";
          if (d.metric.includes("pct") || d.metric.includes("margin") || d.metric.includes("growth")) {
            return `${match.value.toFixed(1)}%`;
          }
          return formatValue(match.value);
        });
        lines.push(`| ${d.metric} | ${values.join(" | ")} |`);
      }
    }
  }

  if (metrics.every((m) => m.periods.length === 0) && derived.length === 0) {
    lines.push("*No financial data found for the requested metrics. The company may use non-standard XBRL tags.*");
  }

  lines.push("");
  lines.push(`*Data source: SEC EDGAR XBRL (as reported in 10-K/10-Q filings) | ${input.period} periods: ${input.period === "annual" ? "12-month fiscal years" : "3-month quarters (year-to-date totals excluded)"} | last ${input.limit} periods. EBITDA, when shown, is computed as operating income + D&A, not company-reported.*`);

  return lines.join("\n");
}
