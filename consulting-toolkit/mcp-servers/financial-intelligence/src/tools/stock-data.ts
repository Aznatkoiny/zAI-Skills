import { z } from "zod";
import { stockDataSchema } from "../schemas/inputs.js";
import { getStockData } from "../services/yahoo.js";

type StockInput = z.infer<typeof stockDataSchema>;

export async function handleStockData(input: StockInput): Promise<string> {
  const { ticker, period, interval } = input;
  const data = await getStockData(ticker, period, interval);
  const { quote, history } = data;

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
  lines.push(`*Data source: Yahoo Finance | Period: ${period} | Interval: ${interval}*`);

  return lines.join("\n");
}
