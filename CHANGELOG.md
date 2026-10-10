# Changelog

Notable changes to the zAI-Skills marketplace and its plugins. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); each plugin is versioned
independently, so entries are grouped per plugin.

The Phase 1–3 overhaul landed as three consecutive commits on 2026-07-26; the interim
versions they introduced (ai-toolkit 2.3.0; career-coach 1.1.0–1.2.0; consulting-toolkit
1.2.0–1.3.0; real-estate-investment 1.1.0–1.2.0) were never published separately and are
folded into the current entries below.

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
