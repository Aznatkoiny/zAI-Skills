# zAI-Skills

A Claude Code plugin marketplace with five plugins: four maintained here and one ([plugin-forge](https://github.com/Aznatkoiny/plugin-forge)) hosted in its own repo.

## Which plugin do I want?

| If you want to… | Install | Try first | Needs |
|---|---|---|---|
| Write or fix prompts for Claude, train RL agents or neural nets, build x402 pay-per-request APIs, set up OpenClaw | `ai-toolkit` | `/optimize-prompt ./prompts/support_bot.md` | Nothing for prompts; Python, LibTorch, Node or a VPS for the other areas |
| Produce consulting deliverables (issue trees, market sizings, company profiles, business cases) with every number sourced | `consulting-toolkit` | `/issue-tree Should we build or buy our data platform?` | Nothing for the thinking commands; Node 18+ for financial data; optional free `FRED_API_KEY` |
| Analyze a rental or commercial deal, screen listings, compare markets, plan a sale or 1031 | `real-estate-investment` | `/analyze-deal 4-plex in Columbus OH, $520k, $1,450/unit, 25% down` | Python 3.10+; optional free Census and FRED keys, Rentcast free tier, paid ATTOM/AirDNA/Mashvisor |
| Run a job search: profile from your resume, ranked openings, tailored resumes and cover letters, mock interviews | `career-coach` | Paste your resume and say "set up my career profile from this", then `/job-hunt staff platform engineer, remote` | Node 18+ and Python 3; optional LaTeX for PDFs; optional free Adzuna and USAJOBS keys |
| Build a Claude Code plugin test-first, with an eval suite as the contract | `plugin-forge` | `/forge` | See its [README](https://github.com/Aznatkoiny/plugin-forge) |

## Install

In Claude Code:

```
/plugin marketplace add Aznatkoiny/zAI-Skills
/plugin install real-estate-investment@zAI-Skills   # or any plugin name from the table
```

Restart Claude Code after installing. Each plugin's README has a short "Try it" section and lists exactly what it needs.

**Skills only:** `npx skills add Aznatkoiny/zAI-Skills` (via [skills.sh](https://skills.sh)) copies the skills but not the commands, agents, hooks or data servers, so most plugin features won't be there. Use `/plugin install` for the full plugins.

### API keys

Keys are optional; every plugin works without them and says what a missing key costs you. Set any you have in your shell profile (`export FRED_API_KEY=...`) or under `env` in `~/.claude/settings.json`, then restart Claude Code. Which keys each plugin reads, and where to get them, is in its README: [consulting-toolkit](consulting-toolkit/README.md#what-it-needs), [real-estate-investment](real-estate-investment/README.md#what-it-needs), [career-coach](career-coach/README.md#what-it-needs).

## The plugins

### [ai-toolkit](AI-Toolkit/)

| Component | Details |
|---|---|
| **Skills** | `prompt-engineer` (prompts for Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5, from Anthropic's prompting docs), `reinforcement-learning` (Gymnasium, Stable-Baselines3), `cpp-reinforcement-learning` (LibTorch), `deep-learning` (Keras 3), `x402-payments`, `openclaw-setup` |
| **Commands** | `/optimize-prompt` `/rl-new-project` `/x402-scaffold` `/openclaw-audit` |
| **Agents** | `prompt-rewriter` (prompt work in a separate context), `rl-debugger` (training diagnostics) |

### [consulting-toolkit](consulting-toolkit/)

| Component | Details |
|---|---|
| **Commands** | 17 slash commands for research, structured thinking, deliverables, engagement management and partner review, including the `/engagement` orchestrator |
| **Agents** | Engagement Manager, Research Analyst, Financial Modeler, Deck Builder, Due Diligence |
| **Skill** | Consulting frameworks (MECE, pyramid principle, Five Forces, TAM/SAM/SOM, NPV/IRR, M&A, pricing) and the quality bar every deliverable is held to |
| **MCP server** | Financial intelligence, 8 tools: SEC EDGAR financials and filing sections, earnings releases, peer benchmarks, Yahoo Finance prices, FRED |
| **Templates and hook** | Deliverable skeletons; a citation check that flags unsourced figures |

### [real-estate-investment](real-estate-investment/)

| Component | Details |
|---|---|
| **Commands** | `/analyze-deal` `/pro-forma` `/screen` `/brrrr` `/str-revenue` `/compare-markets` `/waterfall` `/portfolio` `/exit-analysis` |
| **Agents** | Deal Analyzer, Market Researcher, Portfolio Reviewer, Tax Optimizer |
| **Skill** | Analysis hub with tested Python scripts (pro forma, sensitivity, Monte Carlo, waterfall) and references for benchmarks, metrics, property types, markets and tax |
| **MCP server** | Real estate data, 13 tools across 7 sources: Redfin (no key), Census, FRED, Rentcast, ATTOM, Mashvisor, AirDNA |
| **Output styles and hook** | Investor Report, Quick Screen; a once-per-session tax reminder |

### [career-coach](career-coach/)

| Component | Details |
|---|---|
| **Commands** | `/job-hunt` `/resume-generator` `/cover-letter` `/ats-check` `/mock-interview` `/compare-offers` `/validate-profile` `/follow-ups` |
| **Agents** | Career Director, Job Search, Interview Prep |
| **Skill** | Resume Updater: builds `career-profile.json` from your resume, then fills the gaps |
| **MCP server** | Job intelligence, 5 tools: Remotive, RemoteOK, Greenhouse and Lever company boards, Adzuna, USAJOBS, Levels.fyi compensation; Glassdoor, Indeed and TrueUp are opt-in |
| **Templates and hooks** | Six LaTeX resume templates; PDF compile and profile validation hooks |

### [plugin-forge](https://github.com/Aznatkoiny/plugin-forge)

Eval-first plugin builder: the eval suite is the contract, and green is the definition of done. It's maintained in its own repo and installed through this marketplace from a pinned GitHub source; see its README for components and usage.

## Platform support

macOS and Linux; Windows through WSL. The hooks are bash scripts, and the real-estate data server sets up its Python environment with bash.

## Development

```
/plugin marketplace add /path/to/zAI-Skills
/plugin install <plugin>@zAI-Skills
```

Repo conventions are in [AGENTS.md](AGENTS.md) (read by Claude Code through CLAUDE.md, and by Codex directly); the how-to and release checklist are in [CONTRIBUTING.md](CONTRIBUTING.md). Run `python3 scripts/validate_marketplace.py` before committing; CI runs the same checks.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
