# zAI-Skills

A Claude Code plugin marketplace with four plugins.

## Installation

### Via [skills.sh](https://skills.sh)

```bash
npx skills add Aznatkoiny/zAI-Skills
```

### Via Claude Code

```bash
# Add the marketplace
/plugin marketplace add Aznatkoiny/zAI-Skills

# Install any or all plugins
/plugin install ai-toolkit@zAI-Skills
/plugin install consulting-toolkit@zAI-Skills
/plugin install real-estate-investment@zAI-Skills
/plugin install career-coach@zAI-Skills
/plugin install plugin-forge@zAI-Skills
```

Then restart Claude Code.

---

## Plugins

### [AI-Toolkit](AI-Toolkit/)

Skills, commands, and agents for building AI/ML systems and optimizing prompts.

| Component | Details |
|-----------|---------|
| **Commands** | `/optimize-prompt` `/rl-new-project` `/x402-scaffold` `/openclaw-audit` |
| **Agents** | RL Debugger (training diagnostics), Prompt Rewriter (isolated-context prompt optimization) |

| Skill | Description |
|-------|-------------|
| **deep-learning** | Keras 3 (JAX/TF/PyTorch) — CNNs, RNNs, Transformers, GANs, custom training loops |
| **reinforcement-learning** | Python RL with Stable-Baselines3, RLlib, Gymnasium (PPO, SAC, DQN, TD3, A2C) |
| **cpp-reinforcement-learning** | C++ RL with libtorch and modern C++17/20 for performance-critical applications |
| **prompt-optimizer** | Optimize prompts for the Claude 5 family using Anthropic's official best practices |
| **x402-payments** | Build x402 protocol apps — HTTP-native USDC payments on Base (EVM) and Solana (SVM) |
| **openclaw-setup** | Set up and configure OpenClaw with Anthropic auth, messaging channels, and VPS deployment |

### [consulting-toolkit](consulting-toolkit/)

Multi-agent consulting system replicating top-tier strategy engagement structure.

| Component | Details |
|-----------|---------|
| **Agents** | Engagement Manager, Research Analyst, Financial Modeler, Deck Builder, Due Diligence |
| **Commands** | 17 slash commands across Research, Structured Thinking, Deliverables, Quality Gates, and Engagement Management |
| **Skill** | Consulting frameworks — MECE, Pyramid Principle, Porter's Five Forces, TAM/SAM/SOM, M&A/DD, pricing, and more |
| **MCP Server** | Financial Intelligence — 8 tools for SEC EDGAR (incl. 10-K/10-Q section extraction), FRED, and Yahoo Finance data |
| **Templates** | 6 deliverable skeletons (DD memo, market sizing, storyline, SteerCo, model narrative, competitive landscape) |
| **Hooks** | Citation lint — flags uncited quantitative claims in written deliverables |

### [real-estate-investment](real-estate-investment/)

End-to-end real estate investment analysis — from deal screening through financial modeling to investor-ready reports. Covers all property types with live data integrations.

| Component | Details |
|-----------|---------|
| **Skill** | Core analysis hub with 5 reference files — financial metrics (12 metrics with Python/Excel), advanced analysis (Monte Carlo, sensitivity, waterfalls), property types (BRRRR, commercial, STR, land), market data (6 API integrations), tax strategy (depreciation, 1031, cost seg, 2025-2026 law) |
| **Agents** | Deal Analyzer (autonomous pro forma + sensitivity), Market Researcher (API-driven market scoring), Tax Optimizer (depreciation, cost seg, 1031, entity structure), Portfolio Reviewer (multi-property assessment) |
| **Commands** | `/analyze-deal` `/compare-markets` `/pro-forma` `/brrrr` `/waterfall` `/str-revenue` `/exit-analysis` `/screen` `/portfolio` |
| **MCP Server** | 13 tools across 7 APIs — Census Bureau, Redfin (live market snapshots, no key), FRED, Rentcast (free tier), Mashvisor, AirDNA, ATTOM |
| **Output Styles** | Investor Report (formal memo), Quick Screen (rapid deal screening) |
| **Hooks** | Tax disclaimer on write operations |

### [career-coach](career-coach/)

AI-powered career coaching and job search plugin with resume building, interview preparation, and multi-platform job discovery.

| Component | Details |
|-----------|---------|
| **Agents** | Career Director (Opus orchestrator + coach), Job Search (multi-platform discovery), Interview Prep (mock interviews + coaching) |
| **Skill** | Resume Updater — interactive interview that captures experience into `career-profile.json` with achievement quality gates |
| **Commands** | `/resume-generator` `/cover-letter` `/job-hunt` `/ats-check` `/mock-interview` `/compare-offers` `/validate-profile` `/follow-ups` |
| **MCP Server** | Job Intelligence — 5 tools, API-first (Remotive, RemoteOK, Greenhouse/Lever boards, Adzuna, USAJobs) with scrapers as labeled fallback |
| **Industry Styles** | Software Engineering, AI/ML, Sales, Consulting formatting references (extensible — drop `.md` files to add more) |
| **Templates** | 6 LaTeX resume templates (modern-professional, technical-clean, jakes-resume, deedy, altacv, awesome-cv) |
| **Hooks** | Auto-compile LaTeX/Markdown resumes to PDF; career-profile validation with achievement quality gate |

### [plugin-forge](https://github.com/Aznatkoiny/plugin-forge)

Eval-first plugin builder — the eval suite is the contract; green is the definition of done. Hosted in its own repo; installed through this marketplace via a GitHub source.

| Component | Details |
|-----------|---------|
| **Pipeline** | `/forge` state machine: interview → contract → evals → armed → building → smoke → verify → ship |
| **Skills** | `forge` `write-contract` `build-evals` `arm-evals` `build-loop` `verify` `ship` + primitive-catalog (12 decision cards) and generation-standards knowledge decks |
| **Agents** | spec-critic (read-only three-lens design gate), triage (agent-error / grader-error / task-ambiguity classifier) |
| **Hooks** | Eval-freeze guards (Edit/Write + Bash) and a Stop-hook sha256 sweep — the frozen suite is un-editable during builds |
| **Harness** | `forge-eval` / `forge-build` CLIs; stdlib-only runner vendored into generated plugins; pass^k, RED baselines, judge calibration, holdout tranches, `--max-cost-usd` |
| **Dogfood** | Self-verifying regression suite (8/8, zero-token, CI-ready) |

---

## Platform support

macOS and Linux; Windows via WSL — the hooks are bash scripts and the
real-estate-investment MCP server bootstraps a Python venv via bash.

## Development

```bash
# Add local marketplace
/plugin marketplace add /path/to/this/repo

# Install from local
/plugin install ai-toolkit@zAI-Skills
/plugin install consulting-toolkit@zAI-Skills
/plugin install real-estate-investment@zAI-Skills
/plugin install career-coach@zAI-Skills
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for repo conventions, versioning policy, and the
release checklist. Run `python3 scripts/validate_marketplace.py` before committing; the
same checks run in CI via `.github/workflows/validate.yml`.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
