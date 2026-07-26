# Consulting Toolkit

A multi-agent consulting system for Claude Code that replicates the structure and quality standards of a top-tier strategy consulting engagement.

## What It Does

The **/engagement** command is the entry point for complex briefs. It orchestrates from the main conversation (Claude Code subagents cannot spawn other subagents): it decomposes the brief into MECE workstreams, delegates each to a specialist subagent, runs the **Engagement Manager** agent (opus) as the quality gate over every output, and synthesizes an answer-first recommendation. For quick-turn tasks, 16 further slash commands (17 total) provide direct access to consulting methodologies.

## Components

### Agents (5)

| Agent | Model | Role |
|-------|-------|------|
| `engagement-manager` | opus | Quality gate, cross-workstream consistency, synthesis |
| `research-analyst` | sonnet | Market research, competitive intelligence, company profiling |
| `financial-modeler` | opus | Financial models, business cases, NPV/ROI, sensitivity analysis |
| `deck-builder` | sonnet | Presentation storylines, pyramid principle, slide decks |
| `due-diligence` | sonnet | Target screening, risk assessment, DD checklists |

Models are deliberately tiered: quality-gate judgment (`engagement-manager`) and quantitative modeling (`financial-modeler`) run on opus; the research, deck, and DD specialists run on sonnet.

### Slash Commands (17)

**Orchestration**
- `/engagement` — Full multi-workstream engagement: decompose, delegate to specialists, quality-gate, synthesize

**Research**
- `/market-size` — Structured market sizing (top-down + bottom-up)
- `/competitive-landscape` — Competitive landscape mapping
- `/company-profile` — One-page company profile from public sources

**Structured Thinking**
- `/issue-tree` — MECE issue tree decomposition
- `/hypothesis` — Hypothesis generation and testing plan
- `/so-what` — Extract strategic implications from analysis
- `/size-the-prize` — Financial impact sizing

**Deliverables**
- `/storyline` — Pyramid-principle slide storyline
- `/exec-summary` — SCR executive summary
- `/steerco-update` — Steering committee status update

**Quality Gate**
- `/partner-review` — Grade a deliverable against the Engagement Manager's quality bars (answer-first, MECE, [Source, Date] citations, so-whats, action titles, risk ratings) with a pass/revise verdict and concrete rewrites

**Engagement Management**
- `/workplan` — Structured workplan with workstreams and timeline
- `/business-case` — Full business case scaffold
- `/raci` — RACI matrix generation
- `/risk-log` — Risk and issue log
- `/benchmark` — Benchmarking analysis

### Skills (1)

- **consulting-frameworks** — Core consulting thinking frameworks (MECE, Pyramid Principle, SCR, Porter's Five Forces, TAM/SAM/SOM, and more), organized as seven reference files: structuring, communication, strategy, financial, operational, plus two deal- and pricing-focused references:
  - **ma-and-dd** — Synergy sizing and phasing (revenue vs. cost, realization curves), valuation triangulation (DCF vs. trading comps vs. precedent transactions), integration cost benchmarks, a red-flag taxonomy mapped to the DD agent's risk register, and deal-breaker vs. price-chip framing
  - **pricing** — Price-volume-mix decomposition, Van Westendorp, conjoint basics, EDLP vs. Hi-Lo, price-elasticity estimation from transaction data, and the B2B discount waterfall

### Deliverable Templates (`templates/`)

Six skeletons the agents and commands start from, each prewiring the structure the quality gate checks for:

| Template | Used by | Prewires |
|----------|---------|----------|
| `dd-memo.md` | due-diligence agent | Risk register with Critical/Material/Minor ratings, deal-breaker vs. price-chip classification |
| `market-sizing.md` | `/market-size`, research-analyst | Top-down/bottom-up chains, TAM/SAM/SOM table, assumptions table with source column |
| `storyline.md` | `/storyline`, deck-builder | Pyramid: governing thought, key line, support; title-only read-through |
| `steerco-update.md` | `/steerco-update` | Progress / decisions-needed / risks / next-period |
| `financial-model-narrative.md` | financial-modeler, `/business-case` | Assumptions, drivers, scenarios, sensitivities |
| `competitive-landscape.md` | `/competitive-landscape`, research-analyst | 2x2 positioning map, capability table |

`templates/engagement-state.schema.json` remains the schema for `/engagement`'s state file.

### Hooks (1)

- **Citation lint** (`hooks/check-citations.sh`, PostToolUse on Write/Edit/MultiEdit) — when a consulting deliverable (memo/sizing/profile files, or anything under `deliverables/`) is written with quantitative claim lines lacking a bracketed `[Source, Date]` citation, it surfaces up to 5 offending lines and suggests `/partner-review` before the deliverable goes out. Matching is conservative (code fences, headers, TOCs, and labeled assumptions are skipped) and it fires at most once per session.

## Installation

```bash
# Add the marketplace
/plugin marketplace add /path/to/zAI-Skills

# Install the plugin
/plugin install consulting-toolkit@zAI-Skills
```

## Usage

### Quick Tasks (Slash Commands)
```
/issue-tree Should we build or buy our data platform?
/exec-summary Q3 earnings performance and strategic outlook
/market-size European electric vehicle charging infrastructure
```

### Complex Engagements (/engagement)
For multi-workstream briefs, use the `/engagement` command:

```
/engagement Evaluate whether FedEx should acquire a cold chain logistics company in Europe. Build me a board-ready recommendation.
```

The command decomposes the brief into workstreams, tracks state in `engagement-state.json` (schema in `templates/engagement-state.schema.json`), delegates to the specialist subagents in dependency order, runs the Engagement Manager as the quality gate over each output, and synthesizes a cohesive deliverable package.

## Architecture

```
Consultant (You)
    │
    ├── Slash Commands ──→ Direct, quick-turn outputs
    │
    └── /engagement ──→ Main conversation orchestrates:
            ├── Research Analyst (sonnet)
            ├── Financial Modeler (opus)
            ├── Due Diligence (sonnet)
            ├── Deck Builder (sonnet, when a deck is requested)
            └── Engagement Manager (opus) ── quality gate + synthesis
```

## Financial Intelligence MCP Server

A custom MCP server that gives agents direct access to financial data from SEC EDGAR, FRED (Federal Reserve), and Yahoo Finance.

### Tools (8)

| Tool | Source | Description |
|------|--------|-------------|
| `fin_get_company_financials` | SEC EDGAR XBRL | Revenue, EBITDA, margins, growth rates for public companies |
| `fin_get_filing_text` | SEC EDGAR | Full text from 10-K, 10-Q, 8-K filings |
| `fin_get_filing_section` | SEC EDGAR | Extract a specific 10-K/10-Q section (risk_factors, mdna, business, legal_proceedings, financial_statements) with pagination |
| `fin_get_stock_data` | Yahoo Finance | Price, daily change, 52-week range, volume, OHLCV history |
| `fin_get_macro_indicators` | FRED | GDP, CPI, interest rates, unemployment, and thousands more |
| `fin_get_earnings_transcript` | SEC EDGAR 8-K | Earnings-related 8-K filings (Item 2.02 proxy) |
| `fin_compare_companies` | SEC EDGAR | Side-by-side comparison of 2-5 companies |
| `fin_get_industry_benchmarks` | SEC EDGAR | Median/mean/quartile metrics by SIC code |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FRED_API_KEY` | For FRED tools | Free key from https://fred.stlouisfed.org/docs/api/api_key.html |
| `EDGAR_USER_AGENT` | Recommended | SEC requires email in User-Agent (e.g., "YourName your@email.com") |

### Architecture

```
consulting-toolkit/
├── .mcp.json                          ← MCP server configuration
├── mcp-servers/
│   └── financial-intelligence/
│       ├── src/
│       │   ├── index.ts               ← Entry point, 8 tool registrations
│       │   ├── services/              ← API clients (EDGAR, FRED, Yahoo)
│       │   ├── tools/                 ← Tool handler implementations
│       │   └── schemas/               ← Zod input validation
│       └── dist/                      ← Built output
```

## License

MIT
