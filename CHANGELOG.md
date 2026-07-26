# Changelog

Notable changes to the zAI-Skills marketplace and its plugins. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); each plugin is versioned
independently, so entries are grouped per plugin.

The Phase 1–3 overhaul landed as three consecutive commits on 2026-07-26; the interim
versions they introduced (ai-toolkit 2.3.0; career-coach 1.1.0–1.2.0; consulting-toolkit
1.2.0–1.3.0; real-estate-investment 1.1.0–1.2.0) were never published separately and are
folded into the current entries below.

## ai-toolkit

### [2.4.0] - 2026-07-26

#### Added
- First-ever commands and agents for this plugin: `/optimize-prompt`, `/rl-new-project`,
  `/x402-scaffold`, `/openclaw-audit`; `rl-debugger` and `prompt-rewriter` agents.
- Reinforcement-learning skill: runnable `validate_env.py`, `pretrain_check.py`, and
  `eval_report.py` (verified against CartPole in a fresh venv).
- prompt-optimizer: `ab_eval.py` A/B harness and `evals.md`.

#### Fixed
- Deleted the invalid empty-array `hooks/hooks.json` (it never registered anything).
- Renamed plugin `AI-Toolkit` → `ai-toolkit` (kebab-case required for marketplace sync)
  and corrected install commands.
- Reference-code corrections across skills: C++ RL `q_target` scope bug and libtorch API
  fixes, Gymnasium >= 1.0 wrapper renames, Keras 3 `train_step` pattern and imports,
  current model IDs in prompt-optimizer examples, zod schemas in the x402 MCP example.

## career-coach

### [1.3.0] - 2026-07-26

#### Added
- 6 new commands: `/job-hunt`, `/ats-check`, `/mock-interview`, `/compare-offers`,
  `/validate-profile`, `/follow-ups` (8 commands total).
- `render-resume.py` merging `career-profile.json` into all 6 LaTeX templates, with a
  `--template` option on `/resume-generator`.
- `validate-profile.py` plus a PostToolUse hook enforcing the achievement quality gate;
  negotiation-guide reference.
- Industry-style references (section order, metric-bearing example bullets, ATS keyword
  banks, interview weighting) selected via `preferences.industry_style`.

#### Changed
- job-intelligence MCP server rebuilt API-first: Remotive, RemoteOK, and Greenhouse/Lever
  boards keyless, optional Adzuna/USAJobs keys, scrapers demoted to labeled fallback;
  file TTL cache and a truthful per-source status footer.
- Commands and agents wired to exact `mcp__job-intelligence__*` tool IDs with key-gating
  notes and the MCP → WebSearch → ask-user fallback chain; career-director reframed to
  delegation briefs; prompt-injection cautions added to scraped-content consumers.

#### Fixed
- `hooks/hooks.json` rewritten to the valid object schema — at the previous release the
  compile-latex hook never registered; matchers broadened to `Write|Edit|MultiEdit`.
- Committed a self-contained esbuild CJS bundle (`dist/index.cjs`) so the MCP server
  works immediately after install; FIFO promise-queue rate limiting.

## consulting-toolkit

### [1.4.0] - 2026-07-26

#### Added
- `fin_get_filing_section` tool: paginated 10-K/10-Q section extraction (risk factors,
  MD&A, business, legal proceedings, financial statements), live-verified on AAPL and
  MSFT filings (8 MCP tools total).
- `/engagement` orchestration command driving specialists from the main thread
  (subagents cannot spawn subagents) and `/partner-review` quality gate (17 commands
  total); citation-lint PostToolUse hook; 6 deliverable templates; M&A/DD and pricing
  framework references.

#### Changed
- SIC peer discovery rebuilt on the supported EDGAR browse endpoint, with EDGAR-derived
  market cap/PE and a disk TTL cache; migrated to the `registerTool` API.
- Research commands and agents wired to exact `mcp__financial-intelligence__*` tool IDs
  with fallback chains; engagement-manager slimmed to a quality-gate persona; deliberate
  model tiering (opus for orchestration/finance, sonnet for specialists).

#### Fixed
- Deleted the invalid empty-array `hooks/hooks.json`.
- Committed a self-contained CJS bundle (`dist/index.cjs`); FIFO rate limiting
  (idle-start was 4–9 s), EDGAR retry/backoff, honest tool descriptions, structured
  error fields.

## real-estate-investment

### [1.3.0] - 2026-07-26

#### Added
- `get_redfin_market_snapshot` (keyless, streams Redfin's public gzipped TSV) and
  `get_fred_series` MCP tools (13 tools total); TTL cache, Rentcast free-tier quota
  counter, and 24 offline unit tests.
- Tested finance scripts (`pro_forma`, `waterfall`, `monte_carlo`, `sensitivity`)
  replacing copy-paste prose; commands now run the scripts.
- New commands: `/exit-analysis`, `/screen`, `/portfolio` with a persistent
  `portfolio.json` template (9 commands total); a plugin README (previously the only
  plugin without one).

#### Changed
- Agents reference plugin files via `${CLAUDE_PLUGIN_ROOT}` paths, with tools whitelists,
  model tiering, and trigger examples; commands name exact `mcp__real-estate-data__*`
  tool IDs with key-gating and fallback chains.

#### Fixed
- `plugin.json` empty-string env defaults clobbered user API keys; now `${VAR:-}`
  passthrough.
- Server fixes: `run.sh` venv bootstrap, ATTOM `address1`/`address2`, AirDNA POST
  rentalizer, parameterized Census vintage, input validation.
- tax-disclaimer hook now emits `hookSpecificOutput.additionalContext` JSON (stderr +
  exit 0 was invisible to Claude), with word-boundary matching and session dedupe.
- Skill reference math: `numpy_financial` for IRR, corrected incremental waterfall tiers
  and dated IRRs, `expense_growth` implemented, Excel sign fix.

## Earlier history

- **2026-06-05** — ai-toolkit: prompt-optimizer skill updated for the Claude Opus 4.8
  era.
- **2026-02-19/20** — career-coach 1.0.0 added: agents, resume-updater skill, commands,
  LaTeX templates, hooks, and the 5-tool job-intelligence MCP server.
- **2026-02-17** — real-estate-investment 1.0.0 added with the full analysis toolkit.
- **2026-02-13** — repository restructured into a clean marketplace of self-contained
  plugins; openclaw-setup skill added.
- **2026-02-10** — consulting-toolkit 1.0.0 added (5 agents, 15 commands, frameworks
  skill, 7-tool financial-intelligence MCP server); monolithic README split per plugin.
- **2026-01-31 – 2026-02-08** — original skills collection built up (deep-learning,
  then reinforcement-learning, cpp-reinforcement-learning, prompt-optimizer, and
  x402-payments) and converted into a Claude Code plugin.
