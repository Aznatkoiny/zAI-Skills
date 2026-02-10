# Consulting Toolkit

A multi-agent consulting system for Claude Code that replicates the structure and quality standards of a top-tier strategy consulting engagement.

## What It Does

An **Engagement Manager** agent (opus) orchestrates four specialist sub-agents (all opus) to decompose complex strategic briefs into workstreams, delegate to specialists, enforce quality gates, and synthesize deliverables. For quick-turn tasks, 15 slash commands provide direct access to consulting methodologies.

## Components

### Agents (5)

| Agent | Model | Role |
|-------|-------|------|
| `engagement-manager` | opus | Orchestrator, quality gate, client proxy |
| `research-analyst` | opus | Market research, competitive intelligence, company profiling |
| `financial-modeler` | opus | Financial models, business cases, NPV/ROI, sensitivity analysis |
| `deck-builder` | opus | Presentation storylines, pyramid principle, slide decks |
| `due-diligence` | opus | Target screening, risk assessment, DD checklists |

### Slash Commands (15)

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

### Complex Engagements (Engagement Manager)
For multi-workstream briefs, the Engagement Manager automatically activates:

> Evaluate whether FedEx should acquire a cold chain logistics company in Europe. Build me a board-ready recommendation.

The EM will decompose this into workstreams, delegate to specialists, enforce quality reviews, and synthesize a cohesive deliverable package.

## Architecture

```
Consultant (You)
    │
    ├── Slash Commands ──→ Direct, quick-turn outputs
    │
    └── Complex Briefs ──→ Engagement Manager (opus)
                               ├── Research Analyst (sonnet)
                               ├── Financial Modeler (sonnet)
                               ├── Deck Builder (sonnet)
                               └── Due Diligence (sonnet)
```

## Future: Financial Intelligence MCP Server

A custom MCP server wrapping public financial data APIs (SEC EDGAR, FRED, stock data) is planned for a future phase to give agents direct access to company financials, economic indicators, and industry benchmarks.

## License

MIT
