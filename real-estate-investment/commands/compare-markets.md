---
description: Compare and score real estate markets using demographic, economic, and rental data
argument-hint: "[market1, market2, ...]"
---

# Compare Real Estate Markets

Markets to compare (may be empty): $ARGUMENTS

## Instructions

When this command is invoked, perform a comparative market analysis:

### 1. Collect Market List

If $ARGUMENTS contains a comma-separated list of markets (e.g., "Austin, Phoenix, Nashville"), use those. Otherwise use AskUserQuestion to gather 2-5 markets to compare:
- City or metro area names
- Example: "Austin, TX", "Phoenix Metro", "Nashville-Davidson"

### 2. Load Reference Material

Read the market analysis reference:
the `references/market-analysis.md` file from the `real-estate-investment` skill in this plugin

### 3. Gather Market Data

For each market, collect the following data points:

**Economic Indicators:**
- Job growth rate (past 3 years, YoY)
- Major employers and industry diversity
- Unemployment rate
- Median household income

**Demographic Trends:**
- Population growth rate (past 5 years)
- Net migration (domestic and international)
- Age demographics (working-age population %)

**Real Estate Metrics:**
- Median home price and rent
- Rent-to-price ratio
- Vacancy rate
- Rent growth rate (past 3 years)
- Supply pipeline (units under construction per 1,000 population)
- Days on market

**Data Collection Method:**

Pull data from the `real-estate-data` MCP server first (tools surface as `mcp__real-estate-data__<name>`):

- `mcp__real-estate-data__get_census_demographics` — population, median income, median rent, vacancy rate, owner/renter split by state/county/tract (requires `CENSUS_API_KEY` — the key is free to obtain)
- `mcp__real-estate-data__get_census_housing_stats` — median home value and housing-stock age distribution (requires `CENSUS_API_KEY`)
- `mcp__real-estate-data__get_redfin_market_data` — download URLs and column guide for Redfin market tracker TSVs: median sale price, inventory, days on market, months of supply (no key needed; download and filter with Bash)
- `mcp__real-estate-data__get_rentcast_market_data` — ZIP-level median rent, rent growth, and vacancy (requires `RENTCAST_API_KEY`; free tier, 50 requests/month)
- `mcp__real-estate-data__get_mashvisor_neighborhood` — neighborhood investment score, cash-on-cash, cap rate (requires `MASHVISOR_API_KEY`, paid)
- `mcp__real-estate-data__get_airdna_market_stats` — market-level STR ADR/occupancy if comparing STR markets (requires `AIRDNA_API_KEY`, paid)

**Fallback chain:** MCP tool → WebSearch for publicly available data (BLS job growth, Census QuickFacts, market reports) → ask the user to manually input key metrics. Label each metric with its source.

### 4. Score Each Market

Apply weighted scoring system (0-100 scale):
- **Job Growth** (20%): >3% = 100, 2-3% = 75, 1-2% = 50, <1% = 25
- **Population Growth** (15%): >2% = 100, 1-2% = 75, 0.5-1% = 50, <0.5% = 25
- **Rent Growth** (20%): >5% = 100, 3-5% = 75, 1-3% = 50, <1% = 25
- **Vacancy Rate** (15%): <5% = 100, 5-7% = 75, 7-10% = 50, >10% = 25
- **Affordability** (15%): Rent-to-price ratio >0.8% = 100, 0.6-0.8% = 75, 0.4-0.6% = 50, <0.4% = 25
- **Supply Risk** (15%): Low pipeline = 100, moderate = 75, high = 50, oversupply = 25

### 5. Present Comparison

Generate a side-by-side comparison table with:
- All raw metrics for each market
- Individual category scores
- **Total weighted score** (0-100)
- Rank order (1st, 2nd, 3rd, etc.)

### 6. Provide Recommendation

Recommend the top 1-2 markets with detailed reasoning including:
- Strongest advantages of the recommended market(s)
- Key risk factors to monitor
- Best property types for this market
- Neighborhood-level guidance (where to focus within the metro)

## Notes

- Flag markets with warning signs: declining population, rising vacancy, oversupply
- Consider investor profile: cash flow vs appreciation focus
- Mention regulatory environment (rent control, landlord-tenant laws) if known
