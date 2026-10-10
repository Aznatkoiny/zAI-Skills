// ── SEC EDGAR Types ──

export interface EdgarCompanyInfo {
  cik: string;
  ticker: string;
  name: string;
  sic: string;
  sicDescription: string;
  exchanges: string[];
}

export interface EdgarXBRLFact {
  start?: string;     // Period start date for duration facts (absent for balance-sheet instants)
  end: string;        // Period end date (YYYY-MM-DD)
  val: number;
  accn: string;       // Accession number
  fy: number;         // Fiscal year
  fp: string;         // Fiscal period (FY, Q1, Q2, Q3, Q4)
  form: string;       // Filing form (10-K, 10-Q)
  filed: string;      // Date filed
  frame?: string;     // Reporting frame (e.g., CY2023Q1)
}

export interface FinancialMetric {
  metric: string;
  periods: FinancialPeriod[];
}

export interface FinancialPeriod {
  period: string;          // e.g., "FY2023" or "Q1 2024"
  endDate: string;
  value: number;
  form: string;
  filed: string;
}

export interface CompanyFinancials {
  company: EdgarCompanyInfo;
  metrics: FinancialMetric[];
  derivedMetrics: DerivedMetric[];
  currency: string;
  dataSource: string;
}

export interface DerivedMetric {
  metric: string;
  periods: { period: string; value: number | null }[];
}

// ── Filing Types ──

export interface FilingInfo {
  accessionNumber: string;
  filingDate: string;
  reportDate: string;
  form: string;
  primaryDocument: string;
  primaryDocDescription: string;
  items: string;
}

export interface FilingText {
  company: EdgarCompanyInfo;
  filing: FilingInfo;
  text: string;
  truncated: boolean;
}

// ── Stock Data Types ──

export interface StockQuote {
  ticker: string;
  name: string;
  price: number;
  change: number | null; // null when no previous close is available
  changePercent: number | null;
  fiftyTwoWeekHigh: number;
  fiftyTwoWeekLow: number;
  avgVolume: number;
  avgVolumeBars: number; // number of most-recent history bars averaged for avgVolume
}

export interface StockPricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockData {
  quote: StockQuote;
  history: StockPricePoint[];
  period: string;
  interval: string;
}

// ── Equity Fundamentals (EDGAR-derived, for fin_get_stock_data) ──

export interface ShareCountFact {
  value: number;
  asOf: string; // period end / cover date the share count was reported for
  form: string; // filing form it came from (10-K, 10-Q, 8-K)
  tag: string;  // XBRL tag, e.g. "dei:EntityCommonStockSharesOutstanding"
  note: string; // caveat on what the single selected fact covers (share classes)
}

export interface EpsFact {
  value: number;
  periodEnd: string; // fiscal year end date the EPS covers
  fiscalYear: number;
  form: string;
  tag: string; // e.g. "us-gaap:EarningsPerShareDiluted"
}

export interface EquityFundamentals {
  cik: string;
  entityName: string;
  sharesOutstanding: ShareCountFact | null;
  epsAnnual: EpsFact | null;
}

// ── FRED Types ──

export interface FredSeriesInfo {
  id: string;
  title: string;
  units: string;
  frequency: string;
  seasonalAdjustment: string;
  lastUpdated: string;
  notes: string;
}

export interface FredObservation {
  date: string;
  value: number | null;
}

export interface MacroIndicatorData {
  series: FredSeriesInfo;
  observations: FredObservation[];
}

// ── Comparison Types ──

export interface CompanyComparison {
  companies: string[];
  metrics: ComparisonMetric[];
  period: string;
}

export interface ComparisonMetric {
  metric: string;
  values: { ticker: string; value: number | null }[];
  rankings: { ticker: string; rank: number }[];
}

// ── Industry Benchmark Types ──

export interface IndustryBenchmarks {
  sicCode: string;
  sicDescription: string;
  peerCount: number;
  peers: string[];
  benchmarks: BenchmarkMetric[];
}

export interface BenchmarkMetric {
  metric: string;
  median: number | null;
  mean: number | null;
  p25: number | null;
  p75: number | null;
  min: number | null;
  max: number | null;
}
