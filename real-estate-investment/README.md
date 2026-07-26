# Real Estate Investment — Claude Code Plugin

Comprehensive real estate investment analysis plugin for Claude Code. Covers deal screening through financial modeling to investor-ready output: pro formas, IRR/NPV, BRRRR, short-term rentals, syndication waterfalls, Monte Carlo simulation, market comparison, and tax-aware structuring. Includes a Python MCP server for live market data from Census, Redfin, Rentcast, Mashvisor, AirDNA, and ATTOM.

## Prerequisites

- **Claude Code** CLI
- **Python 3.10+** on PATH (for the MCP server; the `mcp` package requires 3.10+)
- **Optional:** `numpy-financial` and `pandas` for running the generated pro forma / Monte Carlo / waterfall models locally

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

The MCP server reads five API keys from environment variables (configured in `plugin.json`). Every tool degrades gracefully — if its key is missing, the tool returns a JSON error with sign-up guidance instead of crashing. The Redfin tool requires no key at all.

| Env Variable | Provider | Pricing | Tools that need it |
|--------------|----------|---------|--------------------|
| `CENSUS_API_KEY` | Census Bureau | Free ([sign up](https://api.census.gov/data/key_signup.html)) | `get_census_demographics`, `get_census_housing_stats` |
| `RENTCAST_API_KEY` | Rentcast | Free tier: 50 requests/month | `estimate_rent`, `get_rentcast_market_data` |
| `MASHVISOR_API_KEY` | Mashvisor | Paid | `get_mashvisor_property`, `get_mashvisor_neighborhood` |
| `AIRDNA_API_KEY` | AirDNA | Paid | `get_airdna_rentalizer`, `get_airdna_market_stats` |
| `ATTOM_API_KEY` | ATTOM | Paid | `get_attom_property`, `get_attom_valuation` |

With no keys configured, you still get the Redfin market-data tool plus everything that does not touch the MCP server: all agents, commands, the skill, and its reference library.

## Quick Start

1. **Analyze a deal** — `/analyze-deal` or just describe the property: "Analyze this rental: $450k purchase, 4 units, $1,800/mo each, 25% down, 7% interest."
2. **Compare markets** — `/compare-markets Austin, Phoenix, Nashville` scores markets on demographic, economic, and rental data.
3. **Model a syndication** — `/waterfall` walks through GP/LP splits across IRR hurdles.
4. **Generate a model** — `/pro-forma python` produces a complete runnable pro forma with IRR, NPV, DSCR, and amortization schedule.
5. **Pick an output style** — activate **Investor Report** for formal memos or **Quick Screen** for rapid pass/fail screening.

## Components

### Agents (4)

| Agent | Model | Role |
|-------|-------|------|
| `deal-analyzer` | sonnet | Builds full pro formas and return metrics from property details, with go/no-go recommendations |
| `market-researcher` | sonnet | Compares and scores rental markets, trends, and submarkets |
| `portfolio-reviewer` | opus | Aggregate multi-property portfolio analysis, risk, and optimization opportunities |
| `tax-optimizer` | opus | Depreciation schedules, cost segregation, 1031 exchanges, entity structure selection |

Model tiering: `deal-analyzer` and `market-researcher` run structured, formula-driven workflows and use Sonnet; `tax-optimizer` and `portfolio-reviewer` make judgment-heavy recommendations (tax strategy, disposition/refinance priorities) and use Opus. Each agent's frontmatter whitelists only the built-in and `mcp__real-estate-data__*` tools it needs.

### Commands (6)

| Command | Description |
|---------|-------------|
| `/analyze-deal [address]` | Interactive wizard that collects property details and produces comprehensive financial analysis |
| `/brrrr [address\|quick]` | BRRRR strategy calculator — Buy, Rehab, Rent, Refinance, Repeat analysis |
| `/compare-markets [markets]` | Compare and score real estate markets using demographic, economic, and rental data |
| `/pro-forma [python\|excel\|both]` | Generate a real estate pro forma model in Python or Excel format |
| `/str-revenue [address\|market]` | Short-term rental revenue projection with seasonal modeling |
| `/waterfall [american\|european]` | Syndication waterfall calculator — GP/LP profit splits across IRR hurdles |

### Skill + References

The **real-estate-investment** skill routes analysis by property type and methodology, then loads the right reference:

| Reference | Contents |
|-----------|----------|
| `financial-metrics.md` | 12 core metrics with formulas, Python functions, and Excel equivalents; complete `RealEstateProForma` class; amortization schedules |
| `advanced-analysis.md` | Sensitivity tables, Monte Carlo simulation, IRR-hurdle waterfall calculator, syndication LP/GP mechanics |
| `property-types.md` | BRRRR, house hacking, commercial underwriting, STR revenue modeling, land development feasibility |
| `market-analysis.md` | Market scoring with 15+ indicators, API integration patterns, comp adjustment methodology |
| `tax-strategy.md` | Depreciation, cost segregation, 1031 exchanges, bonus depreciation (2025-2030), opportunity zones, entity comparison |

### Output Styles (2)

| Style | Format |
|-------|--------|
| **Investor Report** | Formal investment memorandum: executive summary, financial tables, risk assessment |
| **Quick Screen** | Ultra-concise screening: compact metrics table, pass/fail indicators, one-line verdict |

### Hook

**Tax Disclaimer** — PostToolUse hook on `Write` that scans written content for tax topics (depreciation, 1031, cost segregation, opportunity zones, entity structure) and reminds that analysis is educational, recommending a CPA or tax attorney.

### MCP Server — Real Estate Data (11 tools)

The server is registered as `real-estate-data`, so its tools surface in Claude Code as `mcp__real-estate-data__<tool>` (e.g., `mcp__real-estate-data__estimate_rent`).

| Tool | Provider | Description |
|------|----------|-------------|
| `get_census_demographics` | Census Bureau | Population, income, rent, and housing statistics by state/county/tract |
| `get_census_housing_stats` | Census Bureau | Median home value and housing age distribution |
| `get_redfin_market_data` | Redfin Data Center | Market tracker file URLs, column guide, and usage guidance (no key needed) |
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
