# consulting-toolkit

For consultants, strategy and corp-dev teams, and anyone who needs consulting-grade deliverables: issue trees, market sizings, company profiles, business cases, DD memos, storylines and executive summaries, with every number sourced. Sixteen slash commands for single deliverables, an `/engagement` command that runs a multi-workstream project with specialist agents, and a data server for SEC filings, FRED and stock prices.

## Install

```
/plugin marketplace add Aznatkoiny/zAI-Skills
/plugin install consulting-toolkit@zAI-Skills
```

Restart Claude Code after installing.

## Try it

Start with one that needs no setup:

```
/issue-tree Should we build or buy our data platform?
```

You get a MECE issue tree with the analysis each branch needs and the branches to tackle first. Then:

```
/market-size European EV charging infrastructure        # top-down and bottom-up sizing, every figure cited
/company-profile Datadog                                # one page from SEC filings and the web
/exec-summary market-sizing-european-ev-charging.md     # turn an analysis file into an SCR summary
/partner-review market-sizing-european-ev-charging.md   # pass/revise verdict with concrete fixes
```

Deliverable commands work best from existing analysis (a file or pasted findings). Given only a topic, they offer to research it first or to draft with marked `[TBD]` placeholders, rather than inventing numbers.

## What it needs

| | |
|---|---|
| **Required** | Nothing for the thinking and writing commands (`/issue-tree`, `/hypothesis`, `/raci`, `/workplan`, `/storyline`, ...). |
| **For financial data** | Node.js 18+ (runs the bundled server; it's prebuilt, no install step). |
| Optional: `EDGAR_USER_AGENT` | Your name and email, e.g. `Jane Doe jane@example.com`. The SEC asks every client to identify itself; without it a generic placeholder is sent. |
| Optional: `FRED_API_KEY` | Free from https://fred.stlouisfed.org/docs/api/api_key.html. Needed only for `fin_get_macro_indicators` (GDP, CPI, rates). |
| Optional: Python with openpyxl / python-pptx | Lets the financial-modeler and deck-builder agents produce `.xlsx` and `.pptx` files; without them they produce Markdown and CSV. Use a virtual environment rather than the system Python. |
| Python 3 | Used by the citation-check hook; without it the hook does nothing. |

Set variables in your shell profile (`export FRED_API_KEY=...`) or under `env` in `~/.claude/settings.json`, then restart Claude Code.

## Commands

| | Command | Does |
|---|---|---|
| Orchestration | `/engagement <brief>` | Plans workstreams and shows you the plan first, then runs the specialist agents, quality-gates each output, and synthesizes a recommendation. Tracks state in `engagement-state.json`. |
| Research | `/market-size`, `/competitive-landscape`, `/company-profile`, `/benchmark` | Sourced research deliverables. |
| Structured thinking | `/issue-tree`, `/hypothesis`, `/so-what`, `/size-the-prize` | Problem structuring, testable hypotheses, implications from analysis, value sizing. |
| Deliverables | `/storyline`, `/exec-summary`, `/steerco-update`, `/business-case` | Pyramid-principle storylines, SCR summaries, status updates, business cases with a model outline. |
| Engagement management | `/workplan`, `/raci`, `/risk-log` | Plans, accountability and risk registers. |
| Quality | `/partner-review <file>` | Grades a deliverable against the plugin's quality bar, with exact fixes. |

## Agents

Claude delegates to these on its own when a request fits, and `/engagement` runs them as workstreams. They use whatever model your session runs.

| Agent | Does |
|---|---|
| `research-analyst` | Sourced research memos: markets, companies, competitors, regulation. |
| `financial-modeler` | Multi-scenario models (NPV/IRR, business cases) with a narrative; validates existing workbooks. |
| `due-diligence` | Tests an investment thesis, rates every risk, and writes a DD memo with a risk register. |
| `deck-builder` | Storyline plus slide deck from finished analysis. |
| `engagement-manager` | Quality gate and synthesis inside `/engagement`, or pulls several analyses into one recommendation. |

## Skill

**consulting-frameworks**: how to apply MECE, issue trees, hypotheses, the pyramid principle and SCR, Five Forces, TAM/SAM/SOM, NPV/IRR, build/buy/partner, RACI, synergy sizing, valuation triangulation and pricing frameworks. Its `quality-bar.md` is the sourcing and review standard every deliverable is held to: figures cited `[Source, Date]` or labeled `[Assumption: ...]`, citations only from sources actually read, and rules of thumb labeled as such.

## Financial data server

| Tool | Returns |
|---|---|
| `fin_get_company_financials` | Annual (fiscal-year) or quarterly (3-month) metrics from SEC XBRL, with year-over-year growth, margins and period-end dates. US-listed filers only. |
| `fin_get_filing_section` | One section of a 10-K/10-Q (risk factors, MD&A, business, legal proceedings, financial statements), paginated. |
| `fin_get_filing_text` | The first ~30,000 characters of a filing. |
| `fin_get_earnings_transcript` | Earnings press releases (8-K Exhibit 99.1). Not call transcripts. |
| `fin_compare_companies` | 2-5 companies side by side, with each one's fiscal period end. |
| `fin_get_industry_benchmarks` | Median and quartiles across up to 15 companies sharing a SIC code (a rough sample, not a curated peer set). |
| `fin_get_stock_data` | Price summary and the last 10 daily bars from Yahoo Finance's unofficial endpoint, plus market cap and P/E derived from SEC data. |
| `fin_get_macro_indicators` | FRED series (needs `FRED_API_KEY`). |

Responses are cached under `~/.cache/financial-intelligence`. To rebuild the server after changing its source: `cd mcp-servers/financial-intelligence && npm ci && npm run build`.

## Templates and hook

`templates/` holds the skeletons deliverables start from (DD memo, market sizing, storyline, SteerCo update, model narrative, competitive landscape) and the `/engagement` state schema.

The **citation check** hook runs when a deliverable this plugin names (market-sizing-\*, dd-memo-\*, benchmark-\*, storyline-\*, ...) is saved. It points out lines with figures that have no citation or assumption label, once per distinct problem, and writes nothing into your project.

## License

MIT
