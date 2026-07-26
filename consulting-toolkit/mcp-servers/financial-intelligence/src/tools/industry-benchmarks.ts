import { z } from "zod";
import { industryBenchmarksSchema } from "../schemas/inputs.js";
import {
  getCompanyInfo,
  getCompaniesBySic,
  getFinancialMetrics,
} from "../services/edgar.js";
import { MAX_INDUSTRY_PEERS } from "../constants.js";
import type { BenchmarkMetric } from "../types.js";

type BenchmarkInput = z.infer<typeof industryBenchmarksSchema>;

function isRatioMetric(name: string): boolean {
  return name.includes("pct") || name.includes("margin") || name.includes("growth");
}

function computeStats(values: number[]): Omit<BenchmarkMetric, "metric"> {
  if (values.length === 0) {
    return { median: null, mean: null, p25: null, p75: null, min: null, max: null };
  }

  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;

  const mean = sorted.reduce((sum, v) => sum + v, 0) / n;
  const median = n % 2 === 0 ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2 : sorted[Math.floor(n / 2)];
  const p25 = sorted[Math.floor(n * 0.25)];
  const p75 = sorted[Math.floor(n * 0.75)];

  return {
    median,
    mean,
    p25,
    p75,
    min: sorted[0],
    max: sorted[n - 1],
  };
}

function formatValue(value: number | null): string {
  if (value === null) return "—";
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

export async function handleIndustryBenchmarks(input: BenchmarkInput): Promise<string> {
  let sicCode: string;
  let sicDescription: string;

  if (input.sic_code) {
    sicCode = input.sic_code;
    sicDescription = "";
  } else if (input.ticker) {
    const info = await getCompanyInfo(input.ticker);
    sicCode = info.sic;
    sicDescription = info.sicDescription;
  } else {
    throw new Error("Either sic_code or ticker must be provided.");
  }

  const lines: string[] = [
    `## Industry Benchmarks — SIC ${sicCode}${sicDescription ? ` (${sicDescription})` : ""}`,
    "",
  ];

  // Find peer companies
  let peers;
  let searchNote: string | undefined;
  try {
    const result = await getCompaniesBySic(sicCode, MAX_INDUSTRY_PEERS);
    peers = result.companies;
    searchNote = result.note;
  } catch (err) {
    lines.push(`*Error finding peer companies: ${err instanceof Error ? err.message : "Unknown error"}*`);
    return lines.join("\n");
  }

  if (peers.length === 0) {
    lines.push("*No peer companies found for this SIC code.*");
    if (searchNote) {
      lines.push("");
      lines.push(`*${searchNote}*`);
    }
    return lines.join("\n");
  }

  lines.push(`**Peer companies found:** ${peers.length}`);
  lines.push(`**Peers:** ${peers.map((p) => p.ticker || p.name).join(", ")}`);
  if (searchNote) {
    lines.push("");
    lines.push(`*${searchNote}*`);
  }
  lines.push("");

  // Fetch financials for each peer (2 periods so growth rates can be derived)
  const peerData = await Promise.all(
    peers.map(async (peer) => {
      try {
        return await getFinancialMetrics(
          peer.cik,
          input.metrics,
          "annual",
          2
        );
      } catch {
        return null;
      }
    })
  );

  const validPeers = peerData.filter((p) => p !== null);

  if (validPeers.length === 0) {
    lines.push("*Could not retrieve financial data for any peer companies.*");
    return lines.join("\n");
  }

  // Split metrics: ratios are true benchmarks; absolute dollar values only
  // describe the size mix of the sampled peers.
  const derivedNames = new Set<string>();
  for (const peer of validPeers) {
    for (const d of peer.derived) derivedNames.add(d.metric);
  }
  const ratioDerived = [...derivedNames].filter(isRatioMetric);
  const absoluteDerived = [...derivedNames].filter((n) => !isRatioMetric(n));

  const tableHeader = [
    `| Metric | Median | Mean | P25 | P75 | Min | Max |`,
    `|--------|--------|------|-----|-----|-----|-----|`,
  ];

  const requestedValuesFor = (metricName: string): number[] => {
    const values: number[] = [];
    for (const peer of validPeers) {
      const metric = peer.metrics.find((m) => m.metric === metricName);
      if (metric && metric.periods.length > 0) {
        values.push(metric.periods[0].value);
      }
    }
    return values;
  };

  const derivedValuesFor = (derivedName: string): number[] => {
    const values: number[] = [];
    for (const peer of validPeers) {
      const d = peer.derived.find((dm) => dm.metric === derivedName);
      if (d && d.periods.length > 0 && d.periods[0].value !== null) {
        values.push(d.periods[0].value);
      }
    }
    return values;
  };

  if (ratioDerived.length > 0) {
    lines.push(`### Benchmark Statistics — Ratios (${validPeers.length} peers with data)`);
    lines.push("");
    lines.push(...tableHeader);
    for (const derivedName of ratioDerived) {
      const stats = computeStats(derivedValuesFor(derivedName));
      const fmt = (v: number | null) => (v === null ? "—" : `${v.toFixed(1)}%`);
      lines.push(
        `| **${derivedName}** | ${fmt(stats.median)} | ${fmt(stats.mean)} | ${fmt(stats.p25)} | ${fmt(stats.p75)} | ${fmt(stats.min)} | ${fmt(stats.max)} |`
      );
    }
    lines.push("");
  }

  lines.push(`### Peer Size Context — Absolute Values (${validPeers.length} peers with data)`);
  lines.push("");
  lines.push("*Absolute dollar figures reflect the size mix of the sampled peers — use them for scale context, not as performance benchmarks. Only the ratio statistics above are directly comparable across companies.*");
  lines.push("");
  lines.push(...tableHeader);

  for (const metricName of input.metrics) {
    const stats = computeStats(requestedValuesFor(metricName));
    lines.push(
      `| **${metricName}** | ${formatValue(stats.median)} | ${formatValue(stats.mean)} | ${formatValue(stats.p25)} | ${formatValue(stats.p75)} | ${formatValue(stats.min)} | ${formatValue(stats.max)} |`
    );
  }

  for (const derivedName of absoluteDerived) {
    const stats = computeStats(derivedValuesFor(derivedName));
    lines.push(
      `| **${derivedName}** | ${formatValue(stats.median)} | ${formatValue(stats.mean)} | ${formatValue(stats.p25)} | ${formatValue(stats.p75)} | ${formatValue(stats.min)} | ${formatValue(stats.max)} |`
    );
  }

  lines.push("");
  lines.push(`*Data source: SEC EDGAR XBRL | SIC ${sicCode} | ${validPeers.length} peers analyzed*`);
  lines.push("*Note: Benchmarks are based on most recent annual filings from public companies in this SIC code.*");

  return lines.join("\n");
}
