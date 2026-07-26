// SEC EDGAR API — No key required, User-Agent with email required
export const EDGAR_BASE_URL = "https://data.sec.gov";
export const EDGAR_EFTS_URL = "https://efts.sec.gov/LATEST";
export const EDGAR_XBRL_URL = `${EDGAR_BASE_URL}/api/xbrl/companyfacts`;
export const EDGAR_SUBMISSIONS_URL = `${EDGAR_BASE_URL}/submissions`;

// FRED API — Requires FRED_API_KEY env var
export const FRED_BASE_URL = "https://api.stlouisfed.org/fred";

// Rate limits (requests per second)
export const RATE_LIMITS = {
  edgar: 10,    // SEC official limit: 10 req/s
  fred: 2,      // Conservative (undocumented, ~120/min practical)
  yahoo: 0.1,   // Very conservative (~6/min safe)
} as const;

// Response limits
export const MAX_FILING_TEXT_LENGTH = 30_000;
export const MAX_INDUSTRY_PEERS = 15;

// Known financial metric keys (the XBRL tag map below must cover every key)
export const METRIC_KEYS = [
  "revenue",
  "net_income",
  "ebitda",
  "operating_income",
  "total_assets",
  "total_liabilities",
  "stockholders_equity",
  "cash",
  "total_debt",
  "depreciation",
  "cost_of_revenue",
  "gross_profit",
  "eps",
  "shares_outstanding",
] as const;
export type MetricKey = (typeof METRIC_KEYS)[number];

// Common XBRL taxonomy tags for financial metrics
export const XBRL_METRIC_TAGS: Record<MetricKey, string[]> = {
  revenue: [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
  ],
  net_income: [
    "NetIncomeLoss",
    "ProfitLoss",
    "NetIncomeLossAvailableToCommonStockholdersBasic",
  ],
  ebitda: [], // Computed: operating_income + depreciation_amortization
  operating_income: [
    "OperatingIncomeLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
  ],
  total_assets: ["Assets"],
  total_liabilities: ["Liabilities"],
  stockholders_equity: [
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
  ],
  cash: [
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsAndShortTermInvestments",
  ],
  total_debt: [
    "LongTermDebt",
    "LongTermDebtAndCapitalLeaseObligations",
    "DebtCurrent",
  ],
  depreciation: [
    "DepreciationDepletionAndAmortization",
    "DepreciationAndAmortization",
    "Depreciation",
  ],
  cost_of_revenue: [
    "CostOfRevenue",
    "CostOfGoodsAndServicesSold",
    "CostOfGoodsSold",
  ],
  gross_profit: ["GrossProfit"],
  eps: [
    "EarningsPerShareBasic",
    "EarningsPerShareDiluted",
  ],
  shares_outstanding: [
    "CommonStockSharesOutstanding",
    "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
    "EntityCommonStockSharesOutstanding",
  ],
};

// Common FRED series IDs for quick reference
export const COMMON_FRED_SERIES: Record<string, string> = {
  GDP: "GDP",
  REAL_GDP: "GDPC1",
  CPI: "CPIAUCSL",
  CORE_CPI: "CPILFESL",
  FED_FUNDS: "FEDFUNDS",
  UNEMPLOYMENT: "UNRATE",
  "10Y_TREASURY": "DGS10",
  "2Y_TREASURY": "DGS2",
  SP500: "SP500",
  VIX: "VIXCLS",
  HOUSING_STARTS: "HOUST",
  INDUSTRIAL_PRODUCTION: "INDPRO",
};
