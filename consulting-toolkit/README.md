# Consulting Toolkit

A multi-agent consulting system for Claude Code that replicates the structure and quality standards of a top-tier strategy consulting engagement.

## What It Does

The **/engagement** command is the entry point for complex briefs. It orchestrates from the main conversation (Claude Code subagents cannot spawn other subagents): it decomposes the brief into MECE workstreams, delegates each to a specialist subagent, runs the **Engagement Manager** agent (opus) as the quality gate over every output, and synthesizes an answer-first recommendation. For quick-turn tasks, 15 further slash commands (16 total) provide direct access to consulting methodologies.

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

### Slash Commands (16)

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

**Engagement Management**
- `/workplan` — Structured workplan with workstreams and timeline
- `/business-case` — Full business case scaffold
- `/raci` — RACI matrix generation
- `/risk-log` — Risk and issue log
- `/benchmark` — Benchmarking analysis

### Skills (1)

- **consulting-frameworks** — Core consulting thinking frameworks (MECE, Pyramid Principle, SCR, Porter's Five Forces, TAM/SAM/SOM, and more)

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

### Tools (7)

| Tool | Source | Description |
|------|--------|-------------|
| `fin_get_company_financials` | SEC EDGAR XBRL | Revenue, EBITDA, margins, growth rates for public companies |
| `fin_get_filing_text` | SEC EDGAR | Full text from 10-K, 10-Q, 8-K filings |
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
│       │   ├── index.ts               ← Entry point, 7 tool registrations
│       │   ├── services/              ← API clients (EDGAR, FRED, Yahoo)
│       │   ├── tools/                 ← Tool handler implementations
│       │   └── schemas/               ← Zod input validation
│       └── dist/                      ← Built output
```

## License

MIT
