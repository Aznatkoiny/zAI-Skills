# real-estate-investment

For individual real estate investors and analysts: run the numbers on a rental or commercial deal, screen listings, model BRRRR and short-term rentals, compare markets, track a portfolio, plan a sale or 1031 exchange, and understand the tax side. The numbers come from tested Python scripts, and a bundled data server pulls live market data (Redfin needs no key).

## Install

```
/plugin marketplace add Aznatkoiny/zAI-Skills
/plugin install real-estate-investment@zAI-Skills
```

Restart Claude Code after installing.

## Try it

```
/analyze-deal 4-plex in Columbus OH, $520k, $1,450/unit, 25% down
```

You get a Go / Conditional / Pass verdict, the assumptions it used (so you can correct them), cap rate, cash flow, cash-on-cash, DSCR, IRR, and bear/base/bull scenarios. It asks only for what it can't default (price, rent, financing). Then:

```
/screen listings.csv                         # batch-screen address,price,rent rows
/compare-markets Austin, Nashville, Raleigh  # score markets on one rubric (Redfin prices need no key)
/brrrr quick $120k buy, $45k rehab, $230k ARV, $1,750 rent, 75% LTV
/exit-analysis duplex worth $640k, owe $310k at 3.5%, NOI $38k, bought for $410k in 2017
```

You can also just describe a deal in chat ("is a 6.2% cap rate good for a fourplex in Columbus?").

## What it needs

| | |
|---|---|
| **Required** | **Python 3.10+** on your PATH. The first time the plugin's data server starts, it creates its own virtual environment inside the plugin and installs `mcp`, `numpy` and `numpy-financial` there (nothing goes into your system Python). The calculation scripts run with that environment. |
| No key needed | Redfin housing-market data (prices, inventory, days on market, months of supply for national, state, metro, county, city and ZIP). The first call for a level downloads Redfin's file for it (metro ~46 MB, county ~150 MB, city or ZIP over 1 GB), so it can take a minute or more; results are cached for 24 hours. |
| Optional: `CENSUS_API_KEY` | Free ([sign up](https://api.census.gov/data/key_signup.html)). Area rents, incomes, vacancy, home values. |
| Optional: `FRED_API_KEY` | Free ([sign up](https://fred.stlouisfed.org/docs/api/api_key.html)). Current mortgage rates for default financing; without it, Claude looks the rate up on the web. |
| Optional: `RENTCAST_API_KEY` | 50 free calls a month ([sign up](https://app.rentcast.io/app/api)). Rent estimates for a property. Rentcast bills calls beyond 50, so the server stops at 50 unless you set `RENTCAST_ALLOW_OVERAGE=1`. |
| Optional, paid: `ATTOM_API_KEY`, `MASHVISOR_API_KEY`, `AIRDNA_API_KEY` | Property records and valuations (ATTOM), neighborhood data (Mashvisor), short-term rental revenue (AirDNA, issued by AirDNA's sales team). These integrations follow the providers' docs but haven't been tested with live keys. |

Set keys in your shell profile (`export CENSUS_API_KEY=...`) or under `env` in `~/.claude/settings.json`, then restart Claude Code. Without keys, commands fall back to web search for the same figures and say where each number came from.

## Commands

| Command | Does |
|---|---|
| `/analyze-deal <deal>` | Full analysis of one deal: pro forma, scenarios, Go / Conditional / Pass |
| `/pro-forma <deal> [excel]` | The pro forma itself, as a table and JSON you can edit and re-run; optional Excel formulas |
| `/screen <csv or rows>` | Batch screen: 1% rule, 50%-rule cash flow, DSCR, cap rate, a verdict per row |
| `/brrrr [quick] <deal>` | Buy-rehab-rent-refinance: cash invested, cash out, capital recycled, post-refi cash flow, low-appraisal check |
| `/str-revenue <property or market>` | Short-term rental revenue by month, fees and expenses, STR vs long-term rental with break-even occupancy |
| `/compare-markets <markets>` | Scores and ranks 2-5 markets on jobs, population, rents, prices, vacancy and supply |
| `/waterfall <structure>` | Syndication LP/GP distributions through IRR hurdles, or a simple pref + catch-up |
| `/portfolio [add\|update\|remove\|review]` | Keeps `portfolio.json` in your project and reviews the portfolio |
| `/exit-analysis <property>` | Hold vs taxable sale vs 1031 vs cash-out refinance, with after-tax proceeds and forward IRR |

## Agents

Claude uses these on its own when a request fits; they use whatever model your session runs.

| Agent | Does |
|---|---|
| `deal-analyzer` | One deal from its numbers to a verdict, using the pro forma script |
| `market-researcher` | Researches and ranks markets with the same rubric as `/compare-markets` |
| `portfolio-reviewer` | Portfolio-level leverage, cash flow, concentration and refinance priorities from `portfolio.json` |
| `tax-optimizer` | Depreciation, cost segregation, 1031 and recapture, opportunity zones, entity choice; checks current tax figures on the web |

## Skill, references and scripts

The **real-estate-investment** skill routes a question to the right method, data tool and reference:

| Reference | Contents |
|---|---|
| `benchmarks.md` | The plugin's one set of default assumptions, expense ratios, scenarios and Go / Conditional / Pass thresholds |
| `financial-metrics.md` | Metric formulas, pro forma structure, Excel equivalents |
| `property-types.md` | BRRRR, house hacking, commercial, short-term rental, land and development |
| `advanced-analysis.md` | Sensitivity, Monte Carlo, waterfall mechanics, LP/GP economics |
| `market-analysis.md` | Market scoring rubric, data tools, comparables, submarkets |
| `tax-strategy.md` | Depreciation, cost segregation, 1031, bonus depreciation, opportunity zones, entities, passive-loss rules, with a dated key-figures table |

Scripts in `skills/real-estate-investment/scripts/` (JSON in, JSON or table out; `--sample-input` prints the schema):

| Script | Does |
|---|---|
| `pro_forma.py` | Year-by-year projection with closing costs, monthly amortization and exit; IRR, equity multiple, NPV, cap rate, CoC, DSCR |
| `sensitivity.py` | Price × interest-rate grid of IRR, CoC or DSCR |
| `monte_carlo.py` | IRR/NPV distribution and probability of hitting a target |
| `waterfall.py` | IRR-hurdle syndication waterfall, or `--mode simple` pref + catch-up |

## Output styles, hook and template

- **Output styles**: *Investor Report* (formal memo) and *Quick Screen* (compact screening). Both apply to delivered analyses; follow-up questions get normal answers.
- **Tax reminder hook**: when Claude writes or edits content mentioning real estate tax topics, it's reminded once per session to add a one-line "confirm with a CPA" note if the content is tax guidance. It writes nothing into your project.
- **`templates/portfolio-template.json`**: the documented schema for the `portfolio.json` that `/portfolio` maintains.

## Data server (13 tools)

| Tool | Source | Returns |
|---|---|---|
| `get_redfin_market_snapshot` | Redfin | Monthly (or rolling 3-month) median sale price and YoY change, $/sq ft, homes sold, new listings, inventory, months of supply, days on market, sale-to-list, for one or several regions. No key. |
| `get_redfin_market_data` | Redfin | Download URL and column guide for a whole Redfin file. No key. |
| `get_census_demographics` | Census ACS | Population, income, median gross rent, housing units, vacancy, tenure |
| `get_census_housing_stats` | Census ACS | Median home value, housing units by year built |
| `get_fred_series` | FRED | Any FRED series (mortgage rates, Treasury yields, rental vacancy) |
| `estimate_rent` | Rentcast | Rent estimate with a low-high range and comparable listings |
| `get_rentcast_market_data` | Rentcast | ZIP sale and rental listing statistics |
| `get_attom_property` | ATTOM | Property facts |
| `get_attom_valuation` | ATTOM | AVM value, range and confidence score |
| `get_mashvisor_property` | Mashvisor | Property record |
| `get_mashvisor_neighborhood` | Mashvisor | City neighborhood list and a neighborhood's overview |
| `get_airdna_rentalizer` | AirDNA | STR revenue estimate for a property |
| `get_airdna_market_stats` | AirDNA | Market occupancy, ADR and average revenue |

Server details, caching and tests: [`mcp-servers/real-estate-data/README.md`](mcp-servers/real-estate-data/README.md).

## License

MIT
