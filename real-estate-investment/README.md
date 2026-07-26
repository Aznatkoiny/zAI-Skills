# Real Estate Investment — Claude Code Plugin

Comprehensive real estate investment analysis plugin for Claude Code. Covers deal screening through financial modeling to investor-ready output: pro formas, IRR/NPV, BRRRR, short-term rentals, syndication waterfalls, Monte Carlo simulation, market comparison, exit planning, portfolio tracking, and tax-aware structuring. Ships a library of tested Python analysis scripts (pro forma, waterfall, Monte Carlo, sensitivity) plus a Python MCP server for live market data from Census, Redfin, FRED, Rentcast, Mashvisor, AirDNA, and ATTOM.

## Prerequisites

- **Claude Code** CLI
- **Python 3.10+** on PATH (for the MCP server; the `mcp` package requires 3.10+)
- **Optional:** `numpy` and `numpy-financial` for running the bundled analysis scripts (`pip install numpy numpy-financial`); `pandas` for spreadsheet-style output

No manual server setup is needed: the MCP server launches through `run.sh`, which on first run creates a local virtualenv next to the server and installs its single dependency (`mcp>=1.0.0`) from `requirements.txt`. Later runs reuse the venv.

## Installation

```bash
# Add the marketplace
/plugin marketplace add Aznatkoiny/zAI-Skills

# Install the plugin
/plugin install real-estate-investment@zAI-Skills
```

Then restart Claude Code.

## API Keys

The MCP server reads six API keys from environment variables (configured in `plugin.json`). Every tool degrades gracefully — if its key is missing, the tool returns a JSON error with sign-up guidance instead of crashing. The two Redfin tools require no key at all.

| Env Variable | Provider | Pricing | Tools that need it |
|--------------|----------|---------|--------------------|
| `CENSUS_API_KEY` | Census Bureau | Free ([sign up](https://api.census.gov/data/key_signup.html)) | `get_census_demographics`, `get_census_housing_stats` |
| `FRED_API_KEY` | FRED (St. Louis Fed) | Free ([sign up](https://fred.stlouisfed.org/docs/api/api_key.html)) | `get_fred_series` |
| `RENTCAST_API_KEY` | Rentcast | Free tier: 50 requests/month | `estimate_rent`, `get_rentcast_market_data` |
| `MASHVISOR_API_KEY` | Mashvisor | Paid | `get_mashvisor_property`, `get_mashvisor_neighborhood` |
| `AIRDNA_API_KEY` | AirDNA | Paid | `get_airdna_rentalizer`, `get_airdna_market_stats` |
| `ATTOM_API_KEY` | ATTOM | Paid | `get_attom_property`, `get_attom_valuation` |

With no keys configured, you still get both Redfin market-data tools plus everything that does not touch the MCP server: all agents, commands, the skill, its reference library, and the analysis scripts.

## Quick Start

1. **Analyze a deal** — `/analyze-deal` or just describe the property: "Analyze this rental: $450k purchase, 4 units, $1,800/mo each, 25% down, 7% interest."
2. **Compare markets** — `/compare-markets Austin, Phoenix, Nashville` scores markets on demographic, economic, and rental data.
3. **Model a syndication** — `/waterfall` walks through GP/LP splits across IRR hurdles.
4. **Generate a model** — `/pro-forma python` runs the bundled pro forma script with your assumptions: IRR, NPV, DSCR, and year-by-year cash flows.
5. **Screen a list** — `/screen deals.csv` batch-checks `address,price,rent` rows against the 1% rule, 50% rule, DSCR, and cap rate.
6. **Track your portfolio** — `/portfolio` maintains a `portfolio.json` in your project and runs the portfolio-reviewer agent against it; `/exit-analysis` compares hold vs. sale vs. 1031 vs. cash-out refi for any holding.
7. **Pick an output style** — activate **Investor Report** for formal memos or **Quick Screen** for rapid pass/fail screening.

## Components

### Agents (4)

| Agent | Model | Role |
|-------|-------|------|
| `deal-analyzer` | sonnet | Builds full pro formas and return metrics from property details, with go/no-go recommendations |
| `market-researcher` | sonnet | Compares and scores rental markets, trends, and submarkets |
| `portfolio-reviewer` | opus | Aggregate multi-property portfolio analysis, risk, and optimization opportunities |
| `tax-optimizer` | opus | Depreciation schedules, cost segregation, 1031 exchanges, entity structure selection |

Model tiering: `deal-analyzer` and `market-researcher` run structured, formula-driven workflows and use Sonnet; `tax-optimizer` and `portfolio-reviewer` make judgment-heavy recommendations (tax strategy, disposition/refinance priorities) and use Opus. Each agent's frontmatter whitelists only the built-in and `mcp__real-estate-data__*` tools it needs.

### Commands (9)

| Command | Description |
|---------|-------------|
| `/analyze-deal [address]` | Interactive wizard that collects property details and produces comprehensive financial analysis |
| `/brrrr [address\|quick]` | BRRRR strategy calculator — Buy, Rehab, Rent, Refinance, Repeat analysis |
| `/compare-markets [markets]` | Compare and score real estate markets using demographic, economic, and rental data |
| `/exit-analysis [property]` | Compare exit paths — hold, taxable sale, 1031 exchange, cash-out refi — with after-tax proceeds and forward IRR |
| `/portfolio [add\|update\|remove\|review]` | Create/update `portfolio.json` in the working directory and run the portfolio-reviewer agent against it |
| `/pro-forma [python\|excel\|both]` | Run the canonical pro forma script on a property (Excel formulas optional) |
| `/screen [csv\|list]` | Batch quick-screen `address,price,rent` rows — 1% rule, 50% rule, DSCR, cap rate — in the Quick Screen format |
| `/str-revenue [address\|market]` | Short-term rental revenue projection with seasonal modeling |
| `/waterfall [american\|european]` | Syndication waterfall calculator — GP/LP profit splits across IRR hurdles |

### Skill + References + Scripts

The **real-estate-investment** skill routes analysis by property type and methodology, then loads the right reference:

| Reference | Contents |
|-----------|----------|
| `financial-metrics.md` | 12 core metrics with formulas, Python functions, and Excel equivalents; pro forma construction; amortization schedules |
| `advanced-analysis.md` | Sensitivity methodology, Monte Carlo distributions, waterfall tier mechanics, syndication LP/GP economics |
| `property-types.md` | BRRRR, house hacking, commercial underwriting, STR revenue modeling, land development feasibility |
| `market-analysis.md` | Market scoring with 15+ indicators, API integration patterns, comp adjustment methodology |
| `tax-strategy.md` | Depreciation, cost segregation, 1031 exchanges, bonus depreciation (2025-2030), opportunity zones, entity comparison |

The canonical implementations live as tested, runnable modules in `skills/real-estate-investment/scripts/` (all JSON-in/JSON-out with argparse CLIs; requirements: `numpy`, `numpy-financial`):

| Script | What it does |
|--------|--------------|
| `pro_forma.py` | Full `RealEstateProForma` model: year-by-year projection, exit sale, IRR / equity multiple / NPV / cap rate / CoC / DSCR |
| `waterfall.py` | Incremental-tier, dated-cash-flow syndication waterfall with IRR hurdles (plus `--mode simple` pref + catch-up split) |
| `monte_carlo.py` | Monte Carlo IRR/NPV distribution: normal/triangular draws, percentiles, VaR, P(IRR ≥ target) |
| `sensitivity.py` | Purchase-price × interest-rate grid over the pro forma model, rendered as a markdown table |

Each script prints its own input template via `--sample-input`; `/pro-forma` and `/waterfall` drive them automatically.

### Templates

`templates/portfolio-template.json` — documented schema (see its `_schema` block) for the `portfolio.json` file that `/portfolio` maintains in your working directory and that the portfolio-reviewer agent and `/exit-analysis` read.

### Output Styles (2)

| Style | Format |
|-------|--------|
| **Investor Report** | Formal investment memorandum: executive summary, financial tables, risk assessment |
| **Quick Screen** | Ultra-concise screening: compact metrics table, pass/fail indicators, one-line verdict |

### Hook

**Tax Disclaimer** — PostToolUse hook on `Write` that scans written content for tax topics (depreciation, 1031, cost segregation, opportunity zones, entity structure) and reminds that analysis is educational, recommending a CPA or tax attorney.

### MCP Server — Real Estate Data (13 tools)

The server is registered as `real-estate-data`, so its tools surface in Claude Code as `mcp__real-estate-data__<tool>` (e.g., `mcp__real-estate-data__estimate_rent`).

| Tool | Provider | Description |
|------|----------|-------------|
| `get_census_demographics` | Census Bureau | Population, income, rent, and housing statistics by state/county/tract |
| `get_census_housing_stats` | Census Bureau | Median home value and housing age distribution |
| `get_redfin_market_snapshot` | Redfin Data Center | Parsed market snapshot for a metro/city: median sale price, inventory, days on market, months of supply (no key needed) |
| `get_redfin_market_data` | Redfin Data Center | Market tracker file URLs, column guide, and usage guidance for bulk analysis (no key needed) |
| `get_fred_series` | FRED (St. Louis Fed) | Economic time series — e.g., `MORTGAGE30US` current mortgage rates, unemployment, CPI (free key) |
| `estimate_rent` | Rentcast | Rent estimate with comparable rentals and confidence score |
| `get_rentcast_market_data` | Rentcast | ZIP-code rental market statistics |
| `get_mashvisor_property` | Mashvisor | Property details with STR/LTR income estimates |
| `get_mashvisor_neighborhood` | Mashvisor | Neighborhood investment analysis (score, CoC, cap rate) |
| `get_airdna_rentalizer` | AirDNA | STR revenue projection: ADR, occupancy, RevPAR |
| `get_airdna_market_stats` | AirDNA | Market-level STR statistics |
| `get_attom_property` | ATTOM | Detailed property data: lot, building, year built, beds/baths |
| `get_attom_valuation` | ATTOM | AVM estimate with confidence score and comps |

## License

MIT
