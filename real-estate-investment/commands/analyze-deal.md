---
description: Analyze a real estate deal — interactive wizard that collects property details and produces comprehensive financial analysis
argument-hint: "[property address]"
---

# Analyze Real Estate Deal

Property to analyze (may be empty): $ARGUMENTS

## Instructions

When this command is invoked, perform a comprehensive real estate deal analysis:

### 1. Collect Property Information

If $ARGUMENTS contains a property address or identifier, use it as the subject property. Use AskUserQuestion to gather the following details (skip anything already provided in $ARGUMENTS):

- **Property type**: Single-family residential (SFR), multifamily, commercial, or short-term rental (STR)
- **Purchase price**: Total acquisition cost
- **Down payment**: Dollar amount or percentage
- **Monthly rent**: Expected gross rent (for STR: average daily rate and occupancy percentage)
- **Operating expenses**: Itemized if known, otherwise use industry benchmarks (30-40% for SFR/multifamily, 40-50% for commercial, 50-60% for STR)
- **Loan terms**: Interest rate, loan term (years), amortization period
- **Hold period**: Expected years before sale (default: 10 years)
- **Exit cap rate**: Expected cap rate at sale (default: current + 0.5%)

### 2. Acquire Market Data

Before relying on user-supplied assumptions, pull supporting data from the `real-estate-data` MCP server (tools surface as `mcp__real-estate-data__<name>`):

- `mcp__real-estate-data__estimate_rent` — validate the rent assumption with a Rentcast AVM estimate (requires `RENTCAST_API_KEY`; free tier, 50 requests/month)
- `mcp__real-estate-data__get_rentcast_market_data` — ZIP-level median rent and vacancy for sanity-checking assumptions (requires `RENTCAST_API_KEY`)
- `mcp__real-estate-data__get_attom_property` / `mcp__real-estate-data__get_attom_valuation` — property details and AVM value vs. purchase price (require `ATTOM_API_KEY`, paid)
- `mcp__real-estate-data__get_mashvisor_property` — STR/LTR income estimates and neighborhood score (requires `MASHVISOR_API_KEY`, paid)
- `mcp__real-estate-data__get_census_demographics` — area income, rent, and vacancy context (requires `CENSUS_API_KEY` — the key is free to obtain)
- `mcp__real-estate-data__get_redfin_market_data` — Redfin market tracker download URLs and column guide (no key needed)

**Fallback chain:** if a tool is unavailable or returns a missing-key error, fall back to WebSearch for the same data point; if that fails or the user prefers, ask the user for manual input via AskUserQuestion. Always tell the user which source each number came from.

### 3. Load Reference Material

Read the financial metrics reference:
the `references/financial-metrics.md` file from the `real-estate-investment` skill in this plugin

### 4. Build 10-Year Pro Forma

Calculate year-by-year projections including:
- Gross rental income (assume 2-3% annual growth)
- Operating expenses (assume 3% annual inflation)
- Net Operating Income (NOI)
- Debt service (monthly P&I payment)
- Cash flow (NOI - debt service)
- Cumulative cash flow and equity buildup

### 5. Calculate Key Metrics

Compute all critical investment metrics:
- **Cap Rate**: NOI ÷ Purchase Price
- **Cash-on-Cash Return**: Annual Cash Flow ÷ Total Cash Invested
- **Debt Service Coverage Ratio (DSCR)**: NOI ÷ Annual Debt Service
- **Internal Rate of Return (IRR)**: Time-weighted return over hold period
- **Equity Multiple**: Total Returns ÷ Total Investment
- **Return on Investment (ROI)**: Total profit ÷ Total investment

### 6. Sensitivity Analysis

Run three scenarios:
- **Bear**: -10% rent, +0.5% vacancy, +1% exit cap
- **Base**: Input assumptions
- **Bull**: +10% rent, -0.5% vacancy, -0.5% exit cap

### 7. Present Results

Format output as clean tables showing:
- Annual cash flow projections
- Key metrics comparison (bear/base/bull)
- Investment summary with go/no-go recommendation based on:
  - Minimum acceptable returns (CoC > 8%, IRR > 12%, DSCR > 1.25)
  - Risk factors identified
  - Sensitivity to assumptions

### 8. Offer Code Generation

Ask if user wants:
- Python script with full pro forma model
- Excel formulas for spreadsheet implementation
- Both

If requested, generate the code/formulas and save to working directory.

## Notes

- For STR properties, automatically load property-types.md reference for STR-specific expense guidance
- Flag any red flags: negative cash flow, DSCR < 1.0, cap rate compression risk
- Use clear, non-technical language in the recommendation summary
