# Benchmarks, Defaults and Verdicts

The one place this plugin defines its default assumptions, operating-expense benchmarks, scenarios and go/no-go thresholds. Commands and agents point here instead of restating numbers, so the same deal gets the same answer whichever way the user asks. These are starting points for an estimate, not market facts: replace any default with property or market data when you have it, and say which inputs are defaults.

## Default Assumptions

Use these when the user hasn't given a figure, and list every default you used at the top of the results.

| Input | Default | Notes |
|---|---|---|
| Down payment / LTV | 25% down (75% LTV) | Investor loans; FHA house hacks 3.5% down |
| Interest rate | Latest Freddie Mac 30-year rate + 0.75 pt | `get_fred_series("MORTGAGE30US")`; without a FRED key, WebSearch the latest PMMS rate and cite the date. Investor loans usually price 0.5-1.0 pt above it. |
| Amortization | 30 years | Commercial loans: 25 years |
| Closing costs (purchase) | 3% of price | Typical range 2-5% |
| Vacancy and credit loss | 6% | Use Census rental vacancy for the area when available |
| Other income | 0% (1-4 units), 3% (5+ units) | Laundry, parking, fees |
| Operating expenses | Ratio by property type, below | Excludes debt service and capex reserves |
| Capex reserve | 5% of EGI | 8-10% for properties built before 1980 |
| Rent growth | 3% / year | |
| Expense growth | 3% / year | Insurance and taxes have run hotter in many markets; check |
| Hold period | 10 years | |
| Exit cap rate | Going-in cap rate + 0.5 pt | |
| Selling costs | 6% (1-4 units), 3% (5+ units and commercial) | Use the same figure across every exit path being compared |
| STR platform fee | 15.5% of booking revenue | Airbnb host-only fee; 3% only if the user confirms they're still on split fees |

## Operating Expense Ratios

As a share of effective gross income (EGI), excluding debt service and capex reserves.

| Property Type | OpEx Ratio | Default | Management Fee |
|---|---|---|---|
| Single-family rental | 35-45% | 40% | 8-10% |
| Small multifamily (2-4) | 35-45% | 40% | 8-10% |
| Large multifamily (5+) | 35-45% | 40% | 5-8% |
| Office | 35-55% | 45% | 3-5% |
| Retail (NNN) | 15-25% | 20% | 3-5% |
| Retail (gross lease) | 60-80% | 70% | 3-5% |
| Industrial | 15-25% | 20% | 3-5% |
| Short-term rental | 50-60% of revenue after platform fees | 55% | 20-25% (included) |

The **50% rule** (operating expenses plus capex ≈ 50% of gross rent) is a screening shortcut, used by `/screen`, not an underwriting assumption.

## Scenarios

Run the base case with the user's inputs (or the defaults above), then re-run the pro forma with these changes. Report IRR, Year-1 CoC and DSCR for all three.

| Change from base | Bear | Bull |
|---|---|---|
| Year-1 rent (STR: revenue) | -10% (STR: -15%) | +5% |
| Vacancy | +3 pts | -1 pt |
| Operating expenses | +10% | no change |
| Rent growth | 1% / year | base + 1 pt |
| Exit cap rate | base + 1.0 pt | base - 0.25 pt |

For a price × rate grid, run `scripts/sensitivity.py`; for a probability distribution, run `scripts/monte_carlo.py`.

## Verdicts: Go / Conditional / Pass

The plugin uses one recommendation vocabulary everywhere:

- **Go**: meets every threshold below in the base case and stays cash-flow positive in the bear case.
- **Conditional**: worth pursuing only if named conditions hold (a lower price, a rate below X, rents confirmed at Y). State each condition as a number.
- **Pass**: fails a threshold in the base case, or the bear case has DSCR below 1.0.

| Metric (base case) | Go | Conditional | Pass |
|---|---|---|---|
| Year-1 DSCR | ≥ 1.25x | 1.10-1.25x | < 1.10x |
| Year-1 cash-on-cash | ≥ 8% | 4-8% | < 4% |
| Levered IRR (10-year hold) | ≥ 12% | 8-12% | < 8% |
| Year-1 cash flow | positive | breakeven | negative |

The user's own hurdle rates replace these when given. For appreciation-focused buyers, say plainly when a deal only works on appreciation.

### Strategy-specific checks

| Strategy | Check | Target |
|---|---|---|
| Batch screen (`/screen`) | 1% rule (monthly rent / price) | ≥ 1.0% |
| | DSCR on 50%-rule NOI | ≥ 1.25x |
| | Cap rate on 50%-rule NOI | ≥ 6% (adjust to the market and say so) |
| | Screen verdict | **Go** (worth a full analysis): DSCR ≥ 1.25 and positive cash flow; **Conditional**: DSCR 1.0-1.25 or one rule fails; **Pass**: DSCR < 1.0 or negative cash flow |
| BRRRR | 70% rule: price + rehab ≤ 70% of ARV | pass |
| | Cash left in the deal after refinance | ≤ 25% of cash invested (0% = all capital recycled) |
| | Post-refinance DSCR | ≥ 1.25x |
| | CoC on cash left in | ≥ 15% (infinite if none left) |
| STR | Projected occupancy vs. break-even occupancy (to beat LTR) | at least 10 pts of cushion |
| Portfolio | Portfolio LTV | ≤ 65% |
| | Portfolio DSCR | ≥ 1.25x |
| | Single market / single property type | ≤ 40% / ≤ 50% of value |
| | Loans maturing or resetting | flag within 24 months |

## Waterfall

The typical IRR-hurdle structure is the default in `scripts/waterfall.py`: 100% to LPs until an 8% IRR, then 80/20 to 12%, 70/30 to 18%, and 60/40 above. Details and alternatives: `references/advanced-analysis.md` §Waterfall.

## Market Scoring

The single market-scoring rubric (weights and buckets) is in `references/market-analysis.md` §Weighted Scoring Model.
