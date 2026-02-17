---
name: real-estate-investment
description: >
  End-to-end real estate investment analysis skill. Use when users ask to analyze a property deal,
  run the numbers on a rental, evaluate real estate investments, build a pro forma, compare markets,
  calculate cap rate, cash-on-cash return, IRR, NOI, DSCR, equity multiple, or GRM. Also triggers on:
  BRRRR analysis, house hack evaluation, short-term rental (STR/Airbnb) analysis, commercial underwriting,
  multifamily deal analysis, syndication waterfall modeling, Monte Carlo simulation for real estate,
  sensitivity analysis on a deal, 1031 exchange planning, cost segregation analysis, depreciation
  calculations, real estate tax strategy, market comparison and scoring, rental property screening,
  deal screening, investor report generation, real estate financial modeling, property type comparison,
  rent-to-price analysis, development feasibility, land analysis, value-add underwriting,
  API integration for real estate data (Zillow, Redfin, AirDNA, Mashvisor, ATTOM, Rentcast, Census),
  or any real estate investment financial analysis task.
---

# Real Estate Investment Analysis

Comprehensive real estate investment analysis — from deal screening through financial modeling to investor-ready output. Covers all property types, standard and advanced metrics, code generation, and tax-aware structuring.

## Analysis Workflow

Follow this 6-step process for any deal or market analysis:

1. **Define scope** — Identify property type, investment strategy, and target output format
2. **Gather data** — Collect property financials, market data, and comps (use API reference if automating)
3. **Build pro forma** — Construct income statement: Gross Rent → Vacancy → EGI → OpEx → NOI → Debt Service → Cash Flow
4. **Calculate returns** — Apply appropriate metrics (see Quick Reference below)
5. **Stress test** — Run sensitivity analysis, scenarios, or Monte Carlo simulation
6. **Report** — Generate investor-ready output with recommendations

## Quick Reference — Core Metrics

| Metric | Formula | Typical Range |
|--------|---------|---------------|
| **NOI** | Effective Gross Income - Operating Expenses | Varies by asset |
| **Cap Rate** | NOI / Property Value | 4-10% (market-dependent) |
| **Cash-on-Cash** | Annual Pre-Tax Cash Flow / Total Cash Invested | 8-12% target |
| **DSCR** | NOI / Annual Debt Service | 1.2x+ (lender minimum) |
| **IRR** | Discount rate zeroing NPV of all cash flows | 15-20% target |
| **Equity Multiple** | Total Distributions / Total Capital Invested | 2.0x+ over hold |
| **GRM** | Property Price / Annual Gross Rent | 8-15 (lower = better) |
| **Break-even Occ.** | (OpEx + Debt Service) / Potential Gross Income | <85% preferred |

For complete formulas, Python code, and Excel equivalents → load `references/financial-metrics.md`

## Property Type Router

Select the analysis framework based on property type:

| Property Type | Key Metrics | Rules of Thumb | Reference |
|--------------|-------------|----------------|-----------|
| **SFR / Small Multi (1-4)** | CoC, Cap Rate, DSCR | 1% rule, 50% rule, 70% rule | `references/property-types.md` §Residential |
| **BRRRR** | ARV, Rehab ROI, Refi LTV | 70% rule: Max buy = 70% ARV - repairs | `references/property-types.md` §Residential |
| **House Hack** | Effective housing cost, FHA terms | 3.5% down FHA, self-sufficiency test | `references/property-types.md` §Residential |
| **Large Multifamily (5+)** | Per-unit metrics, NOI, Cap Rate | OpEx ratio 35-45% | `references/property-types.md` §Commercial |
| **Commercial (Office/Retail)** | Per-SF metrics, lease analysis | NNN vs Gross lease impact | `references/property-types.md` §Commercial |
| **Short-Term Rental** | RevPAR, ADR, Occupancy | Revenue = ADR x Occ x 365 - fees | `references/property-types.md` §STR |
| **Land / Development** | Absorption rate, dev pro forma | Total cost vs projected value | `references/property-types.md` §Land |

## Analysis Type Router

Select the analysis methodology based on what the user needs:

| Need | Method | Reference File |
|------|--------|----------------|
| Run the numbers on a deal | Pro forma + core metrics | `references/financial-metrics.md` |
| Stress test assumptions | Sensitivity analysis (bear/base/bull) | `references/advanced-analysis.md` §Sensitivity |
| Model uncertainty/risk | Monte Carlo simulation | `references/advanced-analysis.md` §MonteCarlo |
| Syndication distributions | Waterfall modeling (GP/LP splits) | `references/advanced-analysis.md` §Waterfall |
| Compare/score markets | Market scoring framework | `references/market-analysis.md` §Scoring |
| Pull market data via API | API integration patterns | `references/market-analysis.md` §APIs |
| Find and adjust comps | Comparable analysis | `references/market-analysis.md` §Comps |
| Optimize tax impact | Depreciation, cost seg, 1031 | `references/tax-strategy.md` |
| Choose entity structure | LLC, LP, S-Corp comparison | `references/tax-strategy.md` §Entity |

## Output Format Selection

Adapt output to the user's request:

**Spreadsheet-ready** — Generate formatted tables with formulas. Use pandas DataFrames exported to CSV/Excel. Include Excel formula equivalents for each calculation.

**Decision framework** — Provide structured narrative analysis with go/no-go recommendation. Include risk factors, key assumptions, and sensitivity ranges.

**Code generation** — Produce Python scripts using numpy-financial and pandas. Include complete, runnable pro forma models, Monte Carlo simulators, or waterfall calculators.

**Investor report** — Combine all three: executive summary, financial tables, risk analysis, and appendix with methodology.

## Operating Expense Benchmarks by Property Type

| Property Type | OpEx Ratio (% of EGI) | Management Fee |
|--------------|----------------------|----------------|
| Single-Family Rental | 35-50% | 8-10% |
| Small Multifamily (2-4) | 35-45% | 8-10% |
| Large Multifamily (5+) | 35-45% | 5-8% |
| Office | 35-55% | 3-5% |
| Retail (NNN) | 15-25% | 3-5% |
| Retail (Gross) | 60-80% | 3-5% |
| Industrial | 15-25% | 3-5% |
| Short-Term Rental | 50-65% | 20-25% |

## Key Tax Thresholds (2025-2026)

| Strategy | Key Detail |
|----------|------------|
| **Depreciation** | Residential: 27.5yr, Commercial: 39yr (straight-line) |
| **Bonus Depreciation** | 100% for property placed in service Jan 20, 2025 – Dec 31, 2030 |
| **Cost Segregation** | Reclassify 15-40% of building into 5/7/15-yr assets |
| **Section 179** | $2.5M max deduction (2025), phase-out at $4M |
| **1031 Exchange** | 45-day ID period, 180-day closing, like-kind real property only |
| **Opportunity Zones** | Made permanent (2025), 10-year gain exclusion on QOF investment |

For complete tax analysis with IRS code references → load `references/tax-strategy.md`

## API Quick Reference

| Provider | Best For | Pricing | Auth |
|----------|----------|---------|------|
| **Mashvisor** | STR + LTR rental data | $30-$120/mo | x-api-key header |
| **AirDNA** | STR performance data | $12-$599/mo | Bearer token |
| **ATTOM** | Deep property data (155M+ properties) | $850-$2K/mo | apikey param |
| **Rentcast** | Rental estimates | Free-$449/mo (50 free/mo) | X-Api-Key header |
| **Census Bureau** | Demographics, housing | Free (API key required) | key param |
| **Redfin Data Center** | Market trends | Free (CSV download) | None |

For endpoint URLs, Python examples, and integration patterns → load `references/market-analysis.md`

## Waterfall Distribution Quick Reference

Standard syndication tiers:

| Tier | IRR Hurdle | LP Share | GP Share |
|------|-----------|----------|----------|
| 1 (Return of Capital + Pref) | 0-8% | 100% | 0% |
| 2 (First Promote) | 8-12% | 90% | 10% |
| 3 (Second Promote) | 12-18% | 80% | 20% |
| 4 (Final Split) | 18%+ | 60% | 40% |

Market data: 8% pref in 40% of deals, 10% pref in 30% of deals. 85% of waterfalls use IRR hurdles.

For complete waterfall mechanics, catch-up provisions, and Python calculator → load `references/advanced-analysis.md`

## Reference File Index

Load the appropriate reference file based on the analysis need:

| File | Contents | When to Load |
|------|----------|-------------|
| `references/financial-metrics.md` | 12 metrics with formulas, Python functions, Excel formulas, complete RealEstateProForma class, amortization schedules | Building a pro forma, calculating returns, generating Python/Excel models |
| `references/advanced-analysis.md` | Sensitivity tables, Monte Carlo simulation (Python), waterfall calculator, syndication LP/GP mechanics | Stress testing deals, modeling risk, syndication analysis |
| `references/property-types.md` | BRRRR framework, house hack analysis, commercial underwriting, STR revenue modeling, land development feasibility | Analyzing a specific property type with tailored frameworks |
| `references/market-analysis.md` | Market scoring with 15+ indicators, 6 API integrations with Python code, comp adjustment methodology, submarket signals | Comparing markets, pulling data via APIs, running comps |
| `references/tax-strategy.md` | Depreciation schedules, cost segregation savings, 1031 exchange rules, bonus depreciation (2025-2030), opportunity zones, entity structure comparison | Tax-optimizing a deal, choosing entity structure, planning exchanges |

## Audience Adaptation

- **Beginner investors**: Explain metric meanings, recommend starting with the 1% rule and cash-on-cash return, walk through pro forma line by line
- **Experienced investors**: Skip basics, lead with IRR and equity multiple, provide code/spreadsheet output, focus on sensitivity analysis and tax optimization
- Default to **expert-level analysis** unless context suggests otherwise
