#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  companyFinancialsShape,
  companyFinancialsSchema,
  filingTextShape,
  filingTextSchema,
  filingSectionShape,
  filingSectionSchema,
  stockDataShape,
  stockDataSchema,
  macroIndicatorsShape,
  macroIndicatorsSchema,
  earningsTranscriptShape,
  earningsTranscriptSchema,
  compareCompaniesShape,
  compareCompaniesSchema,
  industryBenchmarksShape,
  industryBenchmarksSchema,
} from "./schemas/inputs.js";
import { handleCompanyFinancials } from "./tools/company-financials.js";
import { handleFilingText } from "./tools/filing-text.js";
import { handleFilingSection } from "./tools/filing-section.js";
import { handleStockData } from "./tools/stock-data.js";
import { handleMacroIndicators } from "./tools/macro-indicators.js";
import { handleEarningsTranscript } from "./tools/earnings-transcript.js";
import { handleCompareCompanies } from "./tools/compare-companies.js";
import { handleIndustryBenchmarks } from "./tools/industry-benchmarks.js";

const server = new McpServer({
  name: "financial-intelligence",
  version: "1.0.0",
});

// ── Tool Registration ──

function formatError(err: unknown): string {
  if (err instanceof z.ZodError) {
    return err.issues
      .map((issue) => (issue.path.length ? `${issue.path.join(".")}: ${issue.message}` : issue.message))
      .join("; ");
  }
  return err instanceof Error ? err.message : String(err);
}

/**
 * Registers a tool with the shared parse/format/error boilerplate.
 *
 * The raw shape is advertised to clients as the tool's input schema; the full
 * schema (which may carry cross-field refinements, e.g. "ticker or cik") is
 * re-parsed in the handler so those refinements are enforced too.
 */
function registerFinTool<Schema extends z.ZodTypeAny>(
  name: string,
  description: string,
  shape: z.ZodRawShape,
  schema: Schema,
  handler: (input: z.output<Schema>) => Promise<string>
): void {
  server.registerTool(name, { description, inputSchema: shape }, async (args: unknown) => {
    try {
      const input = schema.parse(args);
      const text = await handler(input);
      return { content: [{ type: "text" as const, text }] };
    } catch (err) {
      return {
        content: [{ type: "text" as const, text: `Error: ${formatError(err)}` }],
        isError: true,
      };
    }
  });
}

registerFinTool(
  "fin_get_company_financials",
  "Retrieve financial metrics (revenue, EBITDA, margins, growth rates) for a public company from SEC EDGAR XBRL data. Supports annual and quarterly periods.",
  companyFinancialsShape,
  companyFinancialsSchema,
  handleCompanyFinancials
);

registerFinTool(
  "fin_get_filing_text",
  "Retrieve the full text of SEC filings (10-K, 10-Q, 8-K) for qualitative analysis. Returns cleaned text from the primary filing document.",
  filingTextShape,
  filingTextSchema,
  handleFilingText
);

registerFinTool(
  "fin_get_filing_section",
  "Extract a specific section from a company's most recent 10-K or 10-Q (SEC EDGAR): risk_factors (Item 1A), mdna (Management's Discussion & Analysis), business (Item 1, 10-K only), legal_proceedings, or financial_statements. Locates item-heading boundaries in the filing text and returns the section in pages of up to 25,000 characters with a pagination footer (pass page to continue). Boundary detection is heuristic; the tool reports failure instead of returning unrelated text.",
  filingSectionShape,
  filingSectionSchema,
  handleFilingSection
);

registerFinTool(
  "fin_get_stock_data",
  "Get stock price data from the Yahoo Finance chart endpoint (current price, daily change, 52-week range, average volume, OHLCV history) plus computed fundamentals from SEC EDGAR XBRL: market cap (EDGAR-reported shares outstanding × latest chart close) and last-fiscal-year EPS with a derived P/E — each labeled with its derivation and as-of dates.",
  stockDataShape,
  stockDataSchema,
  handleStockData
);

registerFinTool(
  "fin_get_macro_indicators",
  "Fetch macroeconomic indicators from FRED (Federal Reserve). Supports GDP, CPI, interest rates, unemployment, and thousands of other series.",
  macroIndicatorsShape,
  macroIndicatorsSchema,
  handleMacroIndicators
);

registerFinTool(
  "fin_get_earnings_transcript",
  "Extract earnings-related 8-K filings (Item 2.02) as a proxy for earnings call transcripts. Best-effort from public SEC data.",
  earningsTranscriptShape,
  earningsTranscriptSchema,
  handleEarningsTranscript
);

registerFinTool(
  "fin_compare_companies",
  "Side-by-side financial comparison of 2-5 public companies with rankings. Uses SEC EDGAR data.",
  compareCompaniesShape,
  compareCompaniesSchema,
  handleCompareCompanies
);

registerFinTool(
  "fin_get_industry_benchmarks",
  "Compute industry benchmark statistics (median, mean, quartiles) by SIC code using SEC EDGAR data from peer companies.",
  industryBenchmarksShape,
  industryBenchmarksSchema,
  handleIndustryBenchmarks
);

// ── Server Startup ──

async function main(): Promise<void> {
  if (!process.env.EDGAR_USER_AGENT) {
    console.error(
      [
        "".padEnd(72, "="),
        "WARNING: EDGAR_USER_AGENT is not set.",
        "",
        "The SEC's fair-access policy requires a real contact in the User-Agent",
        "header of every EDGAR request. Set the EDGAR_USER_AGENT environment",
        'variable to your name and email, e.g. "Jane Doe jane.doe@example.com".',
        "Until then, requests fall back to a placeholder and may be blocked or",
        "throttled by the SEC.",
        "".padEnd(72, "="),
      ].join("\n")
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Financial Intelligence MCP Server started (stdio transport)");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
