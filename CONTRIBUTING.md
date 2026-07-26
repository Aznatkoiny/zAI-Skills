# Contributing to zAI-Skills

This repo is a Claude Code plugin marketplace. Each top-level plugin directory is
self-contained; `.claude-plugin/marketplace.json` at the repo root indexes them.
[CLAUDE.md](CLAUDE.md) lists the hard conventions in short form — this document is the
how-to.

## Repository layout

```
.claude-plugin/marketplace.json   # marketplace index (name, description, version per plugin)
AI-Toolkit/                       # plugin "ai-toolkit"       (dir name is historical)
career-coach/                     # plugin "career-coach"
consulting-toolkit/               # plugin "consulting-toolkit"
real-estate-investment/           # plugin "real-estate-investment"
scripts/                          # validation, smoke tests, bundle-freshness checks
.github/workflows/validate.yml    # CI: runs the scripts/ checks on every push/PR
```

Each plugin directory contains `.claude-plugin/plugin.json` plus any of: `commands/`,
`agents/`, `skills/`, `hooks/`, `mcp-servers/`, `templates/`, `output-styles/`, and a
`README.md`.

## Adding a new plugin

1. Create `<plugin-dir>/.claude-plugin/plugin.json` with a lowercase kebab-case `name`,
   a `version` (start at `1.0.0`), `description`, and `author`.
2. Add a `README.md` in the plugin directory documenting every component it ships.
3. Add component directories as needed (`commands/`, `agents/`, `skills/`, `hooks/`,
   `mcp-servers/`). Follow the conventions in [CLAUDE.md](CLAUDE.md) — especially the
   `hooks.json` object schema and `${CLAUDE_PLUGIN_ROOT}` file references.
4. Add an entry to `.claude-plugin/marketplace.json` with the same `name` and `version`
   and a `source` pointing at the plugin directory.
5. Update the root `README.md` plugin tables.
6. Run the checks (see release checklist) and make sure CI
   (`.github/workflows/validate.yml`) passes.

## Adding to an existing plugin

In every case: bump the plugin version (see policy below) in BOTH
`<plugin>/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, and update
the plugin README and any numeric counts in the root README / marketplace description.
CI verifies claimed counts against actual files.

- **Command** — add `commands/<name>.md` with `description` and `argument-hint`
  frontmatter; interpolate user input with `$ARGUMENTS` in the body. If it sources data,
  name the exact `mcp__<server>__<tool>` IDs and give the fallback chain
  (MCP → WebSearch → ask the user).
- **Agent** — add `agents/<name>.md` with frontmatter (`description` with trigger
  examples, `tools` whitelist including any MCP tools it uses, deliberate `model`
  choice). Reference plugin files via `${CLAUDE_PLUGIN_ROOT}/...`. If the agent consumes
  web or MCP content, include a prompt-injection caution.
- **Skill** — add `skills/<name>/SKILL.md` (description under the 1024-character limit)
  plus `references/` and `scripts/` as needed. Scripts should be runnable as-is.
- **MCP tool** (Node servers: `job-intelligence`, `financial-intelligence`) — implement
  in `src/`, keep the tool description limited to what the implementation returns, use
  structured error fields (not sentinel values), then rebuild the committed bundle:

  ```bash
  cd <plugin>/mcp-servers/<server>
  npm install
  npm run build        # regenerates dist/index.cjs — commit it with the src/ change
  ```

  The real-estate server (`real-estate-investment/mcp-servers/real-estate-data`) is
  Python: edit `server.py`, keep `test_server.py` green, no bundle step (`run.sh`
  bootstraps a venv at launch).

## Versioning policy

Semantic-ish, per plugin:

- **Patch** (`x.y.Z`) — docs, prompt wording, bug fixes with no new surface.
- **Minor** (`x.Y.0`) — new components: commands, agents, skills, MCP tools, hooks,
  templates.
- **Major** (`X.0.0`) — breaking config changes: renamed plugin or commands, removed
  tools, changed required env vars or profile/config schemas.

Always bump `plugin.json` and the `marketplace.json` entry together — installed caches
refresh only when the marketplace version changes.

## Local development

```bash
# In Claude Code, from any project:
/plugin marketplace add /path/to/zAI-Skills
/plugin install <plugin-name>@zAI-Skills
# restart Claude Code, then exercise the commands/agents you changed
```

After editing a plugin, bump its version and reinstall (or update) so the local cache
picks up the change.

## Release checklist

Before committing / opening a PR:

1. `python3 scripts/validate_marketplace.py` — manifest schema, kebab-case names,
   plugin.json/marketplace.json version agreement, count claims.
2. `bash scripts/smoke_servers.sh` — MCP servers start and answer over stdio.
3. `bash scripts/check_bundle_freshness.sh` — committed `dist/index.cjs` bundles match
   their `src/` (required whenever `src/` changed).
4. Versions bumped in both `plugin.json` and `marketplace.json` for every touched plugin.
5. [CHANGELOG.md](CHANGELOG.md) entry added under the new version.
6. CI (`.github/workflows/validate.yml`) green.
