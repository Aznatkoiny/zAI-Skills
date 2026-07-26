import { z } from "zod";
import { stockDataSchema } from "../schemas/inputs.js";
import { getStockData } from "../services/yahoo.js";
import { getEquityFundamentals } from "../services/edgar.js";
import type { EquityFundamentals } from "../types.js";

type StockInput = z.infer<typeof stockDataSchema>;

function formatLarge(value: number): string {
  if (Math.abs(value) >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${Math.round(value).toLocaleString()}`;
}

export async function handleStockData(input: StockInput): Promise<string> {
  const { ticker, period, interval } = input;
  const data = await getStockData(ticker, period, interval);
  const { quote, history } = data;

  // EDGAR fundamentals are best-effort: a ticker missing from EDGAR (foreign
  // listings, ETFs, indices) must not break the price data.
  let fundamentals: EquityFundamentals | null = null;
  let fundamentalsError: string | null = null;
  try {
    fundamentals = await getEquityFundamentals(ticker);
  } catch (err) {
    fundamentalsError = err instanceof Error ? err.message : String(err);
  }

  const avgVolumeRow =
    quote.avgVolumeBars > 0
      ? `| Avg Volume (last ${quote.avgVolumeBars} ${interval} bars) | ${quote.avgVolume.toLocaleString()} |`
      : `| Avg Volume | N/A |`;

  const changeRow =
    quote.change !== null && quote.changePercent !== null
      ? `| Change | ${quote.change >= 0 ? "+" : ""}${quote.change.toFixed(2)} (${quote.changePercent >= 0 ? "+" : ""}${quote.changePercent.toFixed(2)}%) |`
      : `| Change | N/A |`;

  const lines: string[] = [
    `## ${quote.name} (${quote.ticker})`,
    "",
    `### Current Quote`,
    "",
    `| Metric | Value |`,
    `|--------|-------|`,
    `| Price | $${quote.price.toFixed(2)} |`,
    changeRow,
    `| 52W High | $${quote.fiftyTwoWeekHigh.toFixed(2)} |`,
    `| 52W Low | $${quote.fiftyTwoWeekLow.toFixed(2)} |`,
    avgVolumeRow,
    "",
  ];

  // ── Computed fundamentals (EDGAR-derived, clearly labeled) ──
  const lastBar = history.length > 0 ? history[history.length - 1] : null;
  const closePrice = lastBar ? lastBar.close : quote.price;
  const closeLabel = lastBar
    ? `$${lastBar.close.toFixed(2)} close on ${lastBar.date}`
    : `$${quote.price.toFixed(2)} latest quote price`;

  lines.push("### Computed Fundamentals (EDGAR-derived)");
  lines.push("");
  if (fundamentals && (fundamentals.sharesOutstanding || fundamentals.epsAnnual)) {
    const shares = fundamentals.sharesOutstanding;
    const eps = fundamentals.epsAnnual;
    const derivations: string[] = [];

    lines.push(`| Metric | Value |`);
    lines.push(`|--------|-------|`);

    if (shares && closePrice > 0) {
      const marketCap = shares.value * closePrice;
      lines.push(`| Market Cap (computed) | ${formatLarge(marketCap)} |`);
      derivations.push(
        `*Market cap = ${shares.value.toLocaleString()} shares outstanding ` +
          `(${shares.tag} as of ${shares.asOf}, reported in ${shares.form}) × ${closeLabel} (Yahoo chart). ` +
          `Share count and price are from different dates; this is a computed estimate, not an exchange-reported figure. ` +
          `${shares.note}*`
      );
    }

    if (eps) {
      const epsKind = eps.tag.includes("Diluted") ? "diluted" : "basic";
      lines.push(`| EPS (FY${eps.fiscalYear}, ${epsKind}) | $${eps.value.toFixed(2)} |`);
      derivations.push(
        `*EPS = ${eps.tag} for the fiscal year ended ${eps.periodEnd} (${eps.form}); ` +
          `last reported full fiscal year, not trailing-twelve-month.*`
      );
      if (closePrice > 0) {
        if (eps.value > 0) {
          lines.push(`| P/E (computed) | ${(closePrice / eps.value).toFixed(1)} |`);
          derivations.push(
            `*P/E = ${closeLabel} ÷ FY${eps.fiscalYear} ${epsKind} EPS $${eps.value.toFixed(2)}.*`
          );
        } else {
          lines.push(`| P/E (computed) | N/A (non-positive EPS) |`);
        }
      }
    }

    lines.push("");
    lines.push(...derivations);
  } else if (fundamentalsError) {
    lines.push(
      `*EDGAR fundamentals unavailable for ${ticker.toUpperCase()} (${fundamentalsError}). Market cap and P/E are omitted rather than estimated.*`
    );
  } else {
    lines.push(
      `*No shares-outstanding or EPS facts found in EDGAR XBRL for ${ticker.toUpperCase()}. Market cap and P/E are omitted rather than estimated.*`
    );
  }
  lines.push("");

  if (history.length > 0) {
    // Show summary stats for the period
    const closes = history.map((h) => h.close);
    const periodHigh = Math.max(...closes);
    const periodLow = Math.min(...closes);
    const firstClose = closes[0];
    const lastClose = closes[closes.length - 1];
    const periodReturn = ((lastClose - firstClose) / firstClose) * 100;

    lines.push(`### Price History (${period}, ${interval} interval)`);
    lines.push("");
    lines.push(`| Metric | Value |`);
    lines.push(`|--------|-------|`);
    lines.push(`| Period High | $${periodHigh.toFixed(2)} |`);
    lines.push(`| Period Low | $${periodLow.toFixed(2)} |`);
    lines.push(`| Period Return | ${periodReturn >= 0 ? "+" : ""}${periodReturn.toFixed(2)}% |`);
    lines.push(`| Data Points | ${history.length} |`);
    lines.push("");

    // Show last 10 data points as sample
    const sample = history.slice(-10);
    lines.push(`### Recent Price Data (last ${sample.length} points)`);
    lines.push("");
    lines.push(`| Date | Open | High | Low | Close | Volume |`);
    lines.push(`|------|------|------|-----|-------|--------|`);
    for (const h of sample) {
      lines.push(
        `| ${h.date} | $${h.open.toFixed(2)} | $${h.high.toFixed(2)} | $${h.low.toFixed(2)} | $${h.close.toFixed(2)} | ${h.volume.toLocaleString()} |`
      );
    }
  }

  lines.push("");
  lines.push(
    `*Data sources: Yahoo Finance chart (price/volume history) + SEC EDGAR XBRL (shares outstanding, EPS) | Period: ${period} | Interval: ${interval}*`
  );

  return lines.join("\n");
}
