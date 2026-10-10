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
  "Financial metrics for a US-listed company from SEC EDGAR XBRL (10-K/10-Q filers using US GAAP; foreign 20-F/40-F filers usually return no data). Annual periods are 12-month fiscal years labeled by the year they end (FY2024); quarterly periods are 3-month quarters labeled by end date (fiscal Q4 is usually only in the annual report, so it is often missing). Returns the requested metrics plus derived year-over-year revenue growth and gross/net margin, with a period-end date row for citations. EBITDA is computed as operating income + D&A, not company-reported.",
  companyFinancialsShape,
  companyFinancialsSchema,
  handleCompanyFinancials
);

registerFinTool(
  "fin_get_filing_text",
  "Return the first ~30,000 characters of cleaned text from a company's recent SEC filings (10-K, 10-Q, 8-K), from the primary document. Long 10-Ks are truncated well before the end, so for a specific part of a 10-K or 10-Q (risk factors, MD&A, business, legal proceedings, financial statements) use fin_get_filing_section instead.",
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
  "Stock price summary from Yahoo Finance's public chart endpoint (current price, daily change, 52-week range, average volume, period high/low/return, and the last 10 daily bars, not the full history), plus computed fundamentals from SEC EDGAR XBRL: market cap (shares outstanding × latest close) and last-fiscal-year EPS with a derived P/E, each labeled with its derivation and dates. The Yahoo endpoint is unofficial and can change or block requests without notice.",
  stockDataShape,
  stockDataSchema,
  handleStockData
);

registerFinTool(
  "fin_get_macro_indicators",
  "Fetch economic time series from FRED (St. Louis Fed): GDP, CPI, interest rates, unemployment, and thousands of other series by ID. Requires the user's free FRED_API_KEY; without it the tool returns a message explaining how to get one.",
  macroIndicatorsShape,
  macroIndicatorsSchema,
  handleMacroIndicators
);

registerFinTool(
  "fin_get_earnings_transcript",
  "Return recent earnings press releases: the Exhibit 99.1 text from 8-K filings under Item 2.02 (first ~30,000 characters each). These are the company's written results announcements, not earnings-call transcripts; call transcripts aren't available from public SEC data.",
  earningsTranscriptShape,
  earningsTranscriptSchema,
  handleEarningsTranscript
);

registerFinTool(
  "fin_compare_companies",
  "Side-by-side comparison of 2-5 US-listed companies on their most recent annual or quarterly period from SEC EDGAR XBRL, with each company's period-end date (fiscal years differ between companies) and per-metric rankings.",
  compareCompaniesShape,
  compareCompaniesSchema,
  handleCompareCompanies
);

registerFinTool(
  "fin_get_industry_benchmarks",
  "Median, mean and quartiles of financial metrics across up to 15 companies that share a SIC code, from SEC EDGAR XBRL. The peers are the first companies EDGAR lists for that code, not a size-matched or curated set, so treat results as a rough sample; for a deliberate peer set, use fin_compare_companies.",
  industryBenchmarksShape,
  industryBenchmarksSchema,
  handleIndustryBenchmarks
);

// ── Server Startup ──

async function main(): Promise<void> {
  if (!process.env.EDGAR_USER_AGENT || process.env.EDGAR_USER_AGENT.startsWith("${")) {
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
