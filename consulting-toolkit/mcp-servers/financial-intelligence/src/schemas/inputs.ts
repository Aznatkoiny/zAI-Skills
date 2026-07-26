import { z } from "zod";
import { METRIC_KEYS, FILING_SECTIONS } from "../constants.js";

const metricEnum = z.enum(METRIC_KEYS);

const companyFinancialsBase = z.object({
  ticker: z.string().optional().describe("Stock ticker symbol (e.g., AAPL, MSFT). Provide ticker or cik."),
  cik: z.string().optional().describe("SEC CIK number. Provide ticker or cik."),
  metrics: z
    .array(metricEnum)
    .optional()
    .default(["revenue", "net_income", "total_assets", "stockholders_equity"])
    .describe(
      "Financial metrics to retrieve. Options: revenue, net_income, ebitda, operating_income, total_assets, total_liabilities, stockholders_equity, cash, total_debt, depreciation, cost_of_revenue, gross_profit, eps, shares_outstanding"
    ),
  period: z
    .enum(["annual", "quarterly"])
    .optional()
    .default("annual")
    .describe("Reporting period type"),
  limit: z
    .number()
    .int()
    .min(1)
    .max(20)
    .optional()
    .default(5)
    .describe("Number of periods to retrieve (default 5)"),
});

export const companyFinancialsShape = companyFinancialsBase.shape;
export const companyFinancialsSchema = companyFinancialsBase.refine(
  (d) => Boolean(d.ticker || d.cik),
  { message: "Either ticker or cik must be provided." }
);

const filingTextBase = z.object({
  ticker: z.string().optional().describe("Stock ticker symbol. Provide ticker or cik."),
  cik: z.string().optional().describe("SEC CIK number. Provide ticker or cik."),
  filing_type: z
    .enum(["10-K", "10-Q", "8-K"])
    .describe("SEC filing type to retrieve"),
  limit: z
    .number()
    .int()
    .min(1)
    .max(5)
    .optional()
    .default(1)
    .describe("Number of most recent filings to retrieve (default 1)"),
});

export const filingTextShape = filingTextBase.shape;
export const filingTextSchema = filingTextBase.refine(
  (d) => Boolean(d.ticker || d.cik),
  { message: "Either ticker or cik must be provided." }
);

const filingSectionBase = z.object({
  ticker: z.string().optional().describe("Stock ticker symbol. Provide ticker or cik."),
  cik: z.string().optional().describe("SEC CIK number. Provide ticker or cik."),
  section: z
    .enum(FILING_SECTIONS)
    .describe(
      "Section to extract: risk_factors (Item 1A), mdna (Management's Discussion & Analysis), business (Item 1, 10-K only), legal_proceedings, financial_statements"
    ),
  filing_type: z
    .enum(["10-K", "10-Q"])
    .optional()
    .default("10-K")
    .describe("Filing to read the section from — the most recent filing of this type (default 10-K)"),
  page: z
    .number()
    .int()
    .min(1)
    .optional()
    .default(1)
    .describe(
      "Page of the section to return. Pages are up to 25,000 characters; each response's footer reports the total page count and the next page to request."
    ),
});

export const filingSectionShape = filingSectionBase.shape;
export const filingSectionSchema = filingSectionBase.refine(
  (d) => Boolean(d.ticker || d.cik),
  { message: "Either ticker or cik must be provided." }
);

const stockDataBase = z.object({
  ticker: z.string().describe("Stock ticker symbol (e.g., AAPL, MSFT)"),
  period: z
    .enum(["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"])
    .optional()
    .default("1y")
    .describe("Time period for historical data"),
  interval: z
    .enum(["1d", "1wk", "1mo"])
    .optional()
    .default("1d")
    .describe("Data interval (1d = daily, 1wk = weekly, 1mo = monthly)"),
});

export const stockDataShape = stockDataBase.shape;
export const stockDataSchema = stockDataBase;

const macroIndicatorsBase = z.object({
  series_id: z
    .string()
    .describe(
      'FRED series ID (e.g., "GDP", "CPIAUCSL", "FEDFUNDS", "UNRATE", "DGS10"). See https://fred.stlouisfed.org for all available series.'
    ),
  start_date: z
    .string()
    .optional()
    .describe("Start date in YYYY-MM-DD format"),
  end_date: z
    .string()
    .optional()
    .describe("End date in YYYY-MM-DD format"),
  limit: z
    .number()
    .int()
    .min(1)
    .max(1000)
    .optional()
    .default(20)
    .describe("Number of observations to return (default 20, most recent first)"),
});

export const macroIndicatorsShape = macroIndicatorsBase.shape;
export const macroIndicatorsSchema = macroIndicatorsBase;

const earningsTranscriptBase = z.object({
  ticker: z.string().optional().describe("Stock ticker symbol. Provide ticker or cik."),
  cik: z.string().optional().describe("SEC CIK number. Provide ticker or cik."),
  limit: z
    .number()
    .int()
    .min(1)
    .max(5)
    .optional()
    .default(1)
    .describe("Number of most recent earnings-related 8-K filings (default 1)"),
});

export const earningsTranscriptShape = earningsTranscriptBase.shape;
export const earningsTranscriptSchema = earningsTranscriptBase.refine(
  (d) => Boolean(d.ticker || d.cik),
  { message: "Either ticker or cik must be provided." }
);

const compareCompaniesBase = z.object({
  tickers: z
    .array(z.string())
    .min(2)
    .max(5)
    .describe("Array of 2-5 stock ticker symbols to compare"),
  metrics: z
    .array(metricEnum)
    .optional()
    .default(["revenue", "net_income", "total_assets"])
    .describe("Financial metrics to compare"),
  period: z
    .enum(["annual", "quarterly"])
    .optional()
    .default("annual")
    .describe("Reporting period type"),
});

export const compareCompaniesShape = compareCompaniesBase.shape;
export const compareCompaniesSchema = compareCompaniesBase;

const industryBenchmarksBase = z.object({
  sic_code: z
    .string()
    .regex(/^\d{4}$/, "sic_code must be a 4-digit SIC code (e.g., 7372)")
    .optional()
    .describe("SIC industry code (e.g., 7372 for software). Provide sic_code or ticker."),
  ticker: z
    .string()
    .optional()
    .describe("Ticker to look up SIC code from. Provide sic_code or ticker."),
  metrics: z
    .array(metricEnum)
    .optional()
    .default(["revenue", "net_income", "total_assets"])
    .describe("Financial metrics to benchmark"),
});

export const industryBenchmarksShape = industryBenchmarksBase.shape;
export const industryBenchmarksSchema = industryBenchmarksBase.refine(
  (d) => Boolean(d.sic_code || d.ticker),
  { message: "Either sic_code or ticker must be provided." }
);
