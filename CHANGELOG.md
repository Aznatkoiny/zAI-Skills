# Changelog

Notable changes to the zAI-Skills marketplace and its plugins. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); each plugin is versioned
independently, so entries are grouped per plugin.

Versions skipped in the sequence below (ai-toolkit 2.3.0; career-coach 1.1.0–1.2.0;
consulting-toolkit 1.2.0–1.3.0; real-estate-investment 1.1.0–1.2.0) were never released
on their own; their changes are in the next listed version.

## Repository

### 2026-10-09
- The validator now catches the mistakes that had shipped: bare `mcp__<server>__<tool>`
  names in agent tool lists (they grant nothing for plugin servers), `${VAR}` without a
  default in `.mcp.json`, missing `$ARGUMENTS`, missing READMEs, count drift for agents
  and skills, missing injection cautions, and retired model names in prompts. It no
  longer crashes on external marketplace sources, which had failed CI since plugin-forge
  was added.
- plugin-forge pinned to its v0.2.0 tag; CI actions updated.
- AGENTS.md now holds the repo conventions, and CLAUDE.md imports it, so Claude Code and
  Codex follow the same rules. The root README opens with a "which plugin do I want?"
  table; CONTRIBUTING covers plugin-scoped MCP names, `model: inherit`, external plugins
  and the release checks.

## ai-toolkit

### [2.5.0] - 2026-10-09

Prompts updated for current Claude models (Opus 5.5, Sonnet 5.5, Haiku 5.5, Fable 5.1),
and fast-moving technical content re-checked against upstream sources.

#### Changed
- **prompt-optimizer replaced by prompt-engineer**, an exact copy of the author's
  prompt-engineer skill (Anthropic's prompting docs as of 2026-10-09, per-model guides,
  the "what used to help but now hurts" table). The old skill was a model generation
  behind and gave advice that now hurts (always use xhigh effort, delete verification
  steps, write reasoning in `<thinking>` tags). `ab_eval.py` and `evals.md` were removed
  with it. `/optimize-prompt` and `prompt-rewriter` now follow the skill's workflow, ask
  where the prompt runs before recommending API settings, and can draft a prompt from a
  description.
- **x402-payments** rewritten against x402 2.28.0 (repo now `x402-foundation/x402`): V2
  field names (`amount`, `transaction`), renamed client hooks, `verifyPayment` /
  `settlePayment`, CDP auth via `createCdpFacilitatorClient()`, Next.js `proxy.ts`,
  Node 22+, `@x402/mcp`. Adds money-and-keys guidance (testnet first, keys never printed,
  spend limits on every paying client). `/x402-scaffold` defaults to seller + EVM and checks
  the starter builds.
- **openclaw-setup** rewritten against OpenClaw 2026.9.9 as a thinner guide: config
  snippets that strict validation rejected are fixed (`agents.defaults.model.primary`,
  `agents.defaults.heartbeat`), iMessage moved from the removed BlueBubbles to
  `@openclaw/imessage`, Node 24.16+, confirm-before-acting and secrets-handling rules,
  and a VPS guide that secures SSH in a safe order and keeps all three Docker ports on
  loopback. The Hostinger guide became a general `vps-setup.md` with Hostinger notes.
  API keys are now the only recommended Anthropic auth route. `/openclaw-audit` works on
  Docker installs and never quotes secrets.
- Skill and agent descriptions say what each is for and not for; agents inherit the
  session's model instead of pinning opus/sonnet.

#### Fixed
- RL scripts: `module:Class` specs now import from the current directory;
  `eval_report.py` gains `--vecnormalize` (without it a trained agent scored worse than
  random in testing) and `--max-steps`; `pretrain_check.py` no longer tells you to
  normalize image observations.
- RL guidance: entropy-loss sign, `max_grad_norm` direction, Atari install
  (`gymnasium[atari]`), wrapper order, TD3 `batch_size` 256, SB3 >= 2.4, Optuna pruning
  and separate eval env, ONNX export with a deterministic wrapper (tested: 200/200
  matching actions), TorchScript and `torch.quantization` replaced by `torch.export` /
  AOTInductor and ONNX Runtime / torchao.
- C++ RL: C++20 (required by current LibTorch), CUDA memory statistics via the caching
  allocator, epsilon decay, SAC entropy tuning on GPU, a missing `RolloutBuffer` and SAC
  helpers, aggregate `Experience`; DQN/PPO/SAC snippets now compile against LibTorch 2.14.
- Deep learning: `cache()` before `shuffle/batch/prefetch`, backend-neutral imports and
  mixed precision, Transformer decoder masks, `LeakyReLU(negative_slope=)`, backend
  column in the reference table.

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

### [1.4.0] - 2026-10-09

#### Fixed
- **Agents can use the job-data tools again.** Their `tools:` lists used the bare
  `mcp__job-intelligence__…` names, which match nothing for a plugin-bundled server, so
  job-search and interview-prep silently had no MCP tools. Now plugin-scoped
  (`mcp__plugin_career-coach_job-intelligence__…`); verified live.
- First run no longer dead-ends: `/job-hunt`, `/resume-generator`, `/cover-letter`,
  `/ats-check` and `/mock-interview` explain what's missing and offer to build the profile
  from a pasted resume, or run without one where that's possible.
- Fabrication pressure removed: commands, style files and the profile hook no longer push
  for a metric on every bullet; missing numbers are listed for the user instead, and cover
  letters use a placeholder rather than an invented motivation.
- PDF hook reports its result to Claude (built, failed with log path, or LaTeX missing with
  install hints) instead of writing only to stderr, and only runs in career-coach folders.
- Live mock interviews run in the main conversation (`/mock-interview`); the interview-prep
  agent now builds prep packs.
- Option values use the 409A (common) price, not the preferred price.

#### Changed
- **resume-updater** imports an existing resume or LinkedIn text and asks only about gaps;
  the achievement quality gate has an honest way out; `publications` added to the schema;
  `interview-questions.md` renamed `profile-intake-questions.md`.
- **Job-data server 1.1.0:** LinkedIn scraper removed (robots.txt and terms prohibit it);
  Glassdoor, Indeed and TrueUp scrapers are off unless `JOB_INTEL_ENABLE_SCRAPERS=1`; all
  requests use an honest User-Agent; Levels.fyi data now comes from its sanctioned
  markdown routes (per-level total compensation, with attribution); Remotive is fetched once
  per 6h within its documented limits; for city searches, remote-only results no longer
  crowd out location-aware sources; tool descriptions state exactly what each returns.
- career-director is a coaching analyst (no delegation briefs, no state file); all agents
  inherit the session model.
- Shared rules (file locations, tracker and prep-notes schemas, industry-style lookup with
  a project-local `./industry-styles/` override, honesty rule) live in one reference,
  `working-files.md`.
- README rewritten: who it's for, first steps, required vs optional setup and keys. Removed
  the Claude-in-Chrome auto-apply claim (no agent had those tools).

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

### [1.5.0] - 2026-10-09

#### Fixed
- **Agents can use the financial tools again.** research-analyst, due-diligence and
  financial-modeler listed tools under bare `mcp__financial-intelligence__…` names, which
  match nothing for a plugin-bundled server; now plugin-scoped (verified live: 8/8 tools).
- **`fin_get_company_financials` returned wrong numbers.** Periods were labeled with the
  filing's fiscal year (three years of Alphabet revenue all showed as "FY2025"), quarterly
  mode returned 6- and 9-month year-to-date totals, and "growth" compared adjacent rows.
  Periods now come from each fact's own dates, only 12-month or 3-month spans are kept,
  alternative XBRL tags are merged, and growth is year over year. Tables show period ends.
- `fin_get_filing_text` returned inline-XBRL header noise instead of 10-K text; the hidden
  header is now stripped. `fin_get_earnings_transcript` returns the Exhibit 99.1 press
  release rather than the 8-K cover form, and says it isn't a call transcript.
- `.mcp.json` passed unset keys as the literal `${FRED_API_KEY}`; now `${VAR:-}`, and the
  server treats an unexpanded value as unset.
- Price-volume-mix formula (mix was always zero) and the elasticity example's margin
  threshold corrected.

#### Changed
- `/engagement` shows the workstream plan and expected agent runs before starting, checks
  small outputs itself, caps revisions at two, and passes the prior output when revising.
- The engagement manager makes a recommendation (and separates the client's decisions);
  specialists no longer "ask the EM" mid-run and state assumptions instead; the deck
  builder checks its own storyline and builds the deck in one run.
- One shared standard, `references/quality-bar.md`, for sourcing and review: cite only
  sources actually read, label rules of thumb as assumptions, use role titles instead of
  invented names. Deliverable commands handle file, topic-only and empty input without
  inventing figures.
- Citation hook covers all of the plugin's deliverable names, reports each new problem
  instead of once per session, and keeps its markers out of the user's project.
- Tool descriptions state exactly what each tool returns (US filers only, computed EBITDA,
  last 10 price bars, alphabetical SIC sample, FRED key required).
- Agents inherit the session model; descriptions say what each is not for. README
  rewritten around a no-setup first command and optional keys.

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

### [1.4.0] - 2026-10-09

Prompts updated for current Claude models, every entry point now gives the same numbers
for the same deal, and the data server, scripts and tax content were brought up to date.

#### Changed
- **One calculation engine and one set of benchmarks.** `/analyze-deal`, the
  deal-analyzer agent and the skill now run `pro_forma.py` instead of building models by
  hand. A new `references/benchmarks.md` holds the only default assumptions, expense
  ratios, bear/base/bull scenarios and thresholds; there is one market-scoring rubric
  (market-analysis.md) and one typical waterfall (the script's). One recommendation
  vocabulary everywhere: **Go / Conditional / Pass** (Quick Screen's old PASS meant the
  opposite of Pass).
- Commands ask only for what can't be defaulted (price, rent, financing), run with stated
  defaults and show results first; `/brrrr quick` is defined as a 5-input path. A missing
  FRED key falls back to a web lookup of the Freddie Mac rate instead of a question.
- Agents use `model: inherit`, receive their MCP tools under the plugin-scoped names
  (`mcp__plugin_real-estate-investment_real-estate-data__*`; the old bare names granted
  nothing), state assumptions instead of asking (subagents can't), and carry the
  standard injection caution. market-researcher and portfolio-reviewer gained the
  Redfin snapshot and FRED tools. tax-optimizer checks current figures on the web and no
  longer suggests S-Corps for buy-and-hold rentals.
- Scripts run with the data server's venv (`numpy` and `numpy-financial` added to its
  requirements) instead of a bare `python` plus `pip install`.
- Skill description says what it's for and not for (corporate models belong to
  consulting-frameworks); output styles apply only to delivered analyses and allow a
  one-line assumptions and caveat line; the market-analysis API section is now a
  provider → tool table.
- `portfolio.json` gains optional `annual_debt_service`, `amortization_years` and
  `cost_seg_depreciation`; portfolio-reviewer no longer promises IRR or equity multiple
  without cash-flow history.

#### Fixed
- **Redfin**: the old market-tracker files stopped updating in June 2026; the snapshot
  tool now reads Redfin's current housing-market CSVs, adds state and national levels,
  takes several regions in one call (one download for a whole comparison), and labels
  rolling 3-month periods. `get_redfin_market_data`'s column guide matches the real files.
- **Census**: year-built bins are labeled by vintage (2020+ / 2010-2019 from 2021 on;
  they were mislabeled 2014+ / 2010-2013), and all "no estimate" sentinel codes become
  null.
- **Rentcast**: live calls stop at the 50 free calls a month unless
  `RENTCAST_ALLOW_OVERAGE=1`, since Rentcast bills each extra request; descriptions no
  longer promise a confidence score or vacancy rate.
- **ATTOM** valuation uses `/attomavm/detail` (the old endpoint isn't in ATTOM's docs);
  **AirDNA** market stats use the Enterprise v2 search-then-metrics flow; **Mashvisor**
  neighborhoods look up the ID first. These three follow the providers' docs but are
  unverified against live keys, and say so in every response.
- `run.sh` finds a Python 3.10+ (it used the first `python3`, which is 3.9 on some Macs);
  missing-key errors say where to set keys.
- `pro_forma.py`: closing costs and upfront capex are part of cash invested (returns were
  overstated), monthly amortization, all-cash deals.
- Math: `/brrrr` counted the down payment twice; `/str-revenue` break-even occupancy mixed
  per-night and annual units and ignored platform fees; `/exit-analysis` now sets
  amortization, opex ratio, exit cap and one selling-cost figure for every path; LTR
  operating costs were 15% in one reference (now 35-45%); a DCF example grew Year-1 NOI;
  a stated IRR was 15.24% instead of 14.97%.
- **Tax content** (checked against IRS Notice 2026-11, Rev. Proc. 2025-32 and current
  publications): 100% bonus depreciation is permanent for property acquired after
  Jan 19, 2025 (not "through 2030"); recapture split into §1245 (ordinary) and
  unrecaptured §1250 (up to 25%); 2026 §179 and §461(l) figures; old-regime opportunity
  zone step-ups are no longer reachable and new designations start Jan 1, 2027; QPP
  excludes lessors; QIP is straight-line and doesn't come with a purchase; corrected
  MACRS, boot, 1031 and catch-up worked examples; QI related-party test is >10%; a dated
  key-figures table (SALT, estate exemption, QBI, STR 7-day rule) replaces scattered
  thresholds.
- STR figures: 15.5% Airbnb host fee as the default; stale AirDNA statistics replaced with
  the 2026 midyear outlook.
- The tax hook keeps its once-per-session marker in the temp directory instead of the
  user's project, and only asks for a reminder when the written content is tax guidance.

### [1.3.1] - 2026-07-26

#### Fixed
- The MCP server moved from an inline `mcpServers` block in `plugin.json` to `.mcp.json`;
  the inline form passed validation but registered no servers.

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

## plugin-forge

Maintained in [its own repo](https://github.com/Aznatkoiny/plugin-forge), which has its
own changelog. Listed in this marketplace since 2026-08-02; pinned to v0.2.0.

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
