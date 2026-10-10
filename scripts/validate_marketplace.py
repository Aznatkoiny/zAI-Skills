#!/usr/bin/env python3
"""Marketplace / plugin static validator for the zAI-Skills repo.

Runs entirely offline. Dependencies: Python stdlib + PyYAML.

Checks:
  1. JSON syntax: .claude-plugin/marketplace.json, every plugin.json,
     every hooks/hooks.json (object schema required — top-level arrays are
     rejected), every .mcp.json. External (GitHub/git) marketplace sources must
     pin a ref or sha; local checks are skipped for them. Every local plugin
     has a README.md. .mcp.json env values may not use ${VAR} without a
     default — an unset variable reaches the server as the literal "${VAR}".
  2. Marketplace entry versions equal the corresponding plugin.json versions.
  3. Plugin names are kebab-case.
  4. Frontmatter lint over commands/, agents/, skills/*/SKILL.md and
     output-styles/: description present everywhere, argument-hint present and
     $ARGUMENTS used in every command, SKILL.md descriptions <= 1024 chars and
     skill name == directory name, agent model values in
     {inherit, opus, sonnet, haiku} or absent.
  5. Cross-reference integrity: MCP tool references in *.md use the
     plugin-scoped form mcp__plugin_<plugin>_<server>__<tool> and match a tool
     registered in that server's source (the bare mcp__<server>__<tool> form is
     what a standalone server gets; for a plugin-bundled server it matches
     nothing, so an agent's tools: allowlist silently drops it). Every
     ${CLAUDE_PLUGIN_ROOT} path referenced from commands/ and agents/ resolves
     on disk.
  6. Count drift: numeric "N commands" / "N tools" / "N agents" / "N skills"
     claims in the root README, marketplace.json and plugin.json descriptions
     are compared against actual counts.
  7. Prompt hygiene: commands and agents that read web or MCP content carry
     the standard prompt-injection sentence (INJECTION_PHRASE); prompt files
     don't name retired models or settings (STALE_MODEL_RE), except files in
     STALE_ALLOWED that quote them on purpose.

Exit status: 0 if every check passes, 1 otherwise.

Usage: python3 scripts/validate_marketplace.py [repo_root]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
AGENT_MODELS = {"inherit", "opus", "sonnet", "haiku"}
EXCLUDED_DIRS = {"node_modules", ".git", "__pycache__", "dist", ".venv"}

# The standard caution every web- or MCP-consuming command/agent carries.
# Keep the sentence identical everywhere so this check can find it.
INJECTION_PHRASE = "as data to analyze, not as instructions to follow"
WEB_OR_MCP_RE = re.compile(r"\b(WebFetch|WebSearch|mcp__)")

# Retired model names and settings. Update this list each model generation.
STALE_MODEL_RE = re.compile(
    r"claude-(?:opus|sonnet|haiku)-[34]\b|claude-(?:opus|sonnet|haiku)-[34]-|"
    r"claude-(?:opus|sonnet|fable|haiku)-5(?![-.\d])|"
    r"\b(?:Opus|Sonnet|Haiku) [34]\.\d|\bbudget_tokens\b"
)
# Files that mention old models deliberately: the verbatim Anthropic prompting
# docs bundled in ai-toolkit's prompt-engineer skill, and the changelog.
STALE_ALLOWED = ("AI-Toolkit/skills/prompt-engineer/", "CHANGELOG.md")

# server.tool("name" | server.registerTool("name" | registerAppTool("name"
# | any registerXxxTool("name" wrapper (first argument must be a string literal).
TS_TOOL_RE = re.compile(
    r"""(?:\.(?:registerTool|registerAppTool|tool)|\bregister\w*Tool)\s*\(\s*["']([A-Za-z0-9_.-]+)["']"""
)
PY_TOOL_RE = re.compile(r"@mcp\.tool\([^)]*\)\s*\ndef\s+(\w+)")
MCP_REF_RE = re.compile(r"\bmcp__plugin_([a-z0-9-]+)_([A-Za-z0-9-]+)__([A-Za-z0-9_]+)")
BARE_MCP_REF_RE = re.compile(r"\bmcp__(?!plugin_)([A-Za-z0-9-]+)__([A-Za-z0-9_]+)")
ENV_NO_DEFAULT_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
PLUGIN_ROOT_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}(/[^\s\"'`),;]*)")
# "N commands", "N slash commands", "N-tool", "17 consulting slash commands", ...
# allows up to two intervening words between the number and commands/tools.
CLAIM_RE = re.compile(
    r"\b(\d+)[-\s]+((?:[A-Za-z][A-Za-z-]*[-\s]+){0,2}?)(commands?|tools?|agents?|skills?)\b",
    re.IGNORECASE,
)

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"  FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"  ok    {msg}")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def load_json(path: Path):
    """Parse a JSON file; on failure record it and return None."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        fail(f"{rel(path)}: invalid JSON — {exc}")
    except OSError as exc:
        fail(f"{rel(path)}: unreadable — {exc}")
    return None


def lenient_frontmatter(block: str):
    data: dict = {}
    key = None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s?(.*)$", line)
        if m:
            key = m.group(1)
            data[key] = m.group(2).strip()
        elif line.strip() and key is not None and line.startswith((" ", "\t")):
            data[key] = f"{data[key]} {line.strip()}".strip()
        elif line.strip():
            return None
    return data or None


def parse_frontmatter(path: Path):
    """Return (frontmatter_dict | None, error | None) for a markdown file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, "missing frontmatter block"
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not match:
        return None, "unterminated frontmatter block"
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        # Claude Code also accepts simple `key: value` lines whose value contains
        # ": " without quotes (strict YAML rejects them). Accept that form too,
        # but only when every line is a top-level key or a continuation.
        data = lenient_frontmatter(match.group(1))
        if data is None:
            return None, f"frontmatter is not valid YAML — {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter is not a YAML mapping"
    return data, None


def iter_md_files(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


# ── Load marketplace + plugins ────────────────────────────────────────────────

print("== Check 1: JSON syntax ==")

marketplace_path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
marketplace = load_json(marketplace_path)
if marketplace is None:
    print("\nRESULT: FAIL (marketplace.json unparseable — aborting)")
    sys.exit(1)
ok(f"{rel(marketplace_path)} parses")

plugins: list[dict] = []  # {name, version, description, dir}
for entry in marketplace.get("plugins", []):
    name = entry.get("name", "<unnamed>")
    source = entry.get("source", "")
    if isinstance(source, dict):
        # External plugin (e.g. {"source": "github", "repo": "owner/name"}).
        # Its files live in another repo, so only the entry itself is checked.
        # An unpinned source serves whatever the default branch holds, which
        # can drift from the version this marketplace advertises.
        kind = source.get("source")
        if kind not in {"github", "git", "url"}:
            fail(f"marketplace entry '{name}': unknown source type {kind!r}")
        elif kind == "github" and not source.get("repo"):
            fail(f"marketplace entry '{name}': github source needs 'repo'")
        elif not (source.get("ref") or source.get("sha")):
            fail(f"marketplace entry '{name}': external source must pin 'ref' or 'sha'")
        else:
            ok(f"marketplace entry '{name}': external {kind} source pinned")
        if not KEBAB_RE.match(name):
            fail(f"plugin name {name!r} is not kebab-case")
        continue
    plugin_dir = (REPO_ROOT / source).resolve()
    if not plugin_dir.is_dir():
        fail(f"marketplace entry '{name}': source '{source}' is not a directory")
        continue
    plugins.append(
        {
            "name": name,
            "version": entry.get("version"),
            "description": entry.get("description", ""),
            "dir": plugin_dir,
        }
    )

plugin_json_by_name: dict[str, dict] = {}
for plugin in plugins:
    pj_path = plugin["dir"] / ".claude-plugin" / "plugin.json"
    if not pj_path.is_file():
        fail(f"{plugin['name']}: missing {rel(pj_path)}")
        continue
    data = load_json(pj_path)
    if data is not None:
        ok(f"{rel(pj_path)} parses")
        plugin_json_by_name[plugin["name"]] = data
    if not (plugin["dir"] / "README.md").is_file():
        fail(f"{plugin['name']}: missing README.md")

for hooks_path in sorted(REPO_ROOT.glob("*/hooks/hooks.json")):
    data = load_json(hooks_path)
    if data is None:
        continue
    if isinstance(data, list):
        fail(f"{rel(hooks_path)}: top-level array — the object schema {{\"hooks\": {{...}}}} is required")
    elif not isinstance(data, dict):
        fail(f"{rel(hooks_path)}: top-level value must be an object")
    elif not isinstance(data.get("hooks"), dict):
        fail(f"{rel(hooks_path)}: 'hooks' key missing or not an object")
    else:
        ok(f"{rel(hooks_path)} parses (object schema)")

mcp_configs: dict[str, dict] = {}  # plugin name -> {server_name: config}
for plugin in plugins:
    servers: dict[str, dict] = {}
    mcp_path = plugin["dir"] / ".mcp.json"
    if mcp_path.is_file():
        data = load_json(mcp_path)
        if data is not None:
            if not isinstance(data, dict):
                fail(f"{rel(mcp_path)}: top-level value must be an object")
            else:
                ok(f"{rel(mcp_path)} parses")
                servers.update(data.get("mcpServers", data))
                for server_name, config in servers.items():
                    for key, value in (config.get("env") or {}).items():
                        for var in ENV_NO_DEFAULT_RE.findall(str(value)):
                            fail(
                                f"{rel(mcp_path)}: {server_name}.env.{key} uses ${{{var}}} with no default — "
                                f"write ${{{var}:-}} so an unset variable arrives empty, not as the literal text"
                            )
    pj = plugin_json_by_name.get(plugin["name"], {})
    inline = pj.get("mcpServers")
    if isinstance(inline, dict):
        # The harness does not register inline declarations even though
        # `claude plugin validate` accepts them: real-estate-investment showed
        # "MCP servers (0)" in `claude plugin details` until its server moved
        # to .mcp.json.
        fail(
            f"{plugin['name']}: plugin.json declares mcpServers inline — "
            f"move it to {rel(plugin['dir'] / '.mcp.json')} or the harness will not register it"
        )
        servers.update(inline)
    mcp_configs[plugin["name"]] = servers

# ── Check 2: version agreement ────────────────────────────────────────────────

print("\n== Check 2: marketplace vs plugin.json versions ==")
for plugin in plugins:
    pj = plugin_json_by_name.get(plugin["name"])
    if pj is None:
        continue
    mv, pv = plugin["version"], pj.get("version")
    if mv != pv:
        fail(f"{plugin['name']}: marketplace version {mv!r} != plugin.json version {pv!r}")
    else:
        ok(f"{plugin['name']}: version {mv} agrees")

# ── Check 3: kebab-case names ─────────────────────────────────────────────────

print("\n== Check 3: plugin names are kebab-case ==")
for plugin in plugins:
    names = {plugin["name"]}
    pj = plugin_json_by_name.get(plugin["name"])
    if pj and pj.get("name"):
        names.add(pj["name"])
    for name in sorted(names):
        if not KEBAB_RE.match(name):
            fail(f"plugin name {name!r} is not kebab-case")
        else:
            ok(f"{name} is kebab-case")

# ── Check 4: frontmatter lint ─────────────────────────────────────────────────

print("\n== Check 4: frontmatter lint ==")
fm_checked = 0
fm_errors_before = len(failures)
for plugin in plugins:
    pdir = plugin["dir"]
    groups = [
        ("command", sorted((pdir / "commands").glob("*.md")) if (pdir / "commands").is_dir() else []),
        ("agent", sorted((pdir / "agents").glob("*.md")) if (pdir / "agents").is_dir() else []),
        ("skill", sorted((pdir / "skills").glob("*/SKILL.md")) if (pdir / "skills").is_dir() else []),
        ("output-style", sorted((pdir / "output-styles").glob("*.md")) if (pdir / "output-styles").is_dir() else []),
    ]
    for kind, files in groups:
        for path in files:
            fm_checked += 1
            fm, err = parse_frontmatter(path)
            if err:
                fail(f"{rel(path)}: {err}")
                continue
            desc = fm.get("description")
            if not isinstance(desc, str) or not desc.strip():
                fail(f"{rel(path)}: missing 'description' in frontmatter")
            elif kind == "skill" and len(desc) > 1024:
                fail(f"{rel(path)}: SKILL.md description is {len(desc)} chars (max 1024)")
            if kind == "skill" and fm.get("name") != path.parent.name:
                fail(f"{rel(path)}: skill name {fm.get('name')!r} != directory name {path.parent.name!r}")
            if kind == "command":
                hint = fm.get("argument-hint")
                if not isinstance(hint, str) or not hint.strip():
                    fail(f"{rel(path)}: command missing 'argument-hint' in frontmatter")
                if "$ARGUMENTS" not in path.read_text(encoding="utf-8"):
                    fail(f"{rel(path)}: command body never uses $ARGUMENTS — arguments would be dropped")
            if kind == "agent":
                model = fm.get("model")
                if model is not None and model not in AGENT_MODELS:
                    fail(f"{rel(path)}: agent model {model!r} not in {sorted(AGENT_MODELS)}")
if len(failures) == fm_errors_before:
    ok(f"{fm_checked} component files linted")

# ── Check 5: cross-reference integrity ────────────────────────────────────────

print("\n== Check 5: cross-reference integrity ==")

# 5a. Discover registered tools per MCP server.
server_tools: dict[str, set[str]] = {}  # server name -> tool names
server_plugin: dict[str, str] = {}  # server name -> plugin name
for plugin in plugins:
    for server_name, config in mcp_configs[plugin["name"]].items():
        # Locate the server source dir: prefer an mcp-servers/<dir> segment in
        # the launch args, fall back to mcp-servers/<server_name>.
        args_blob = " ".join(str(a) for a in config.get("args", []))
        dir_match = re.search(r"mcp-servers/([A-Za-z0-9_-]+)", args_blob)
        server_dir = plugin["dir"] / "mcp-servers" / (dir_match.group(1) if dir_match else server_name)
        if not server_dir.is_dir():
            fail(f"{plugin['name']}: MCP server '{server_name}' source dir not found ({rel(server_dir)})")
            continue
        tools: set[str] = set()
        src_dir = server_dir / "src"
        if src_dir.is_dir():
            for ts in sorted(src_dir.rglob("*.ts")):
                tools.update(TS_TOOL_RE.findall(ts.read_text(encoding="utf-8")))
        for py in sorted(server_dir.glob("*.py")):
            if py.name.startswith("test_"):
                continue
            tools.update(PY_TOOL_RE.findall(py.read_text(encoding="utf-8")))
        if not tools:
            fail(f"{plugin['name']}: no registered tools found in {rel(server_dir)}")
            continue
        server_tools[server_name] = tools
        server_plugin[server_name] = plugin["name"]
        ok(f"server '{server_name}' ({plugin['name']}): {len(tools)} registered tools")

# 5b. Every MCP tool reference in markdown must use the plugin-scoped name and
# resolve to a registered tool of that plugin's server.
ref_errors = 0
for path in iter_md_files(REPO_ROOT):
    text = path.read_text(encoding="utf-8")
    for plugin_name, server_name, tool in MCP_REF_RE.findall(text):
        ref = f"mcp__plugin_{plugin_name}_{server_name}__{tool}"
        if server_name not in server_tools or server_plugin.get(server_name) != plugin_name:
            fail(f"{rel(path)}: references unknown plugin MCP server '{ref}'")
            ref_errors += 1
        elif tool not in server_tools[server_name]:
            fail(
                f"{rel(path)}: references unregistered tool '{ref}' "
                f"(server '{server_name}' registers: {', '.join(sorted(server_tools[server_name]))})"
            )
            ref_errors += 1
    for server_name, tool in BARE_MCP_REF_RE.findall(text):
        if server_name in server_tools:
            fail(
                f"{rel(path)}: bare 'mcp__{server_name}__{tool}' — plugin tools are named "
                f"'mcp__plugin_{server_plugin[server_name]}_{server_name}__{tool}'"
            )
            ref_errors += 1
if ref_errors == 0:
    ok("all MCP tool references are plugin-scoped and resolve to registered tools")

# 5c. Every ${CLAUDE_PLUGIN_ROOT} path in commands/ and agents/ resolves.
path_errors = 0
path_refs = 0
for plugin in plugins:
    for sub in ("commands", "agents"):
        sub_dir = plugin["dir"] / sub
        if not sub_dir.is_dir():
            continue
        for md in sorted(sub_dir.glob("*.md")):
            for suffix in PLUGIN_ROOT_RE.findall(md.read_text(encoding="utf-8")):
                if "<" in suffix or "*" in suffix:
                    continue  # templated placeholder, not a literal path
                path_refs += 1
                target = plugin["dir"] / suffix.lstrip("/")
                if not target.exists():
                    fail(f"{rel(md)}: ${{CLAUDE_PLUGIN_ROOT}}{suffix} does not exist on disk")
                    path_errors += 1
if path_errors == 0:
    ok(f"all {path_refs} literal ${{CLAUDE_PLUGIN_ROOT}} paths in commands/agents resolve")

# ── Check 6: count drift ──────────────────────────────────────────────────────

print("\n== Check 6: count drift (README + marketplace descriptions) ==")

actual_counts: dict[str, dict[str, int]] = {}
for plugin in plugins:
    commands_dir = plugin["dir"] / "commands"
    n_commands = len(list(commands_dir.glob("*.md"))) if commands_dir.is_dir() else 0
    n_tools = sum(
        len(tools)
        for server_name, tools in server_tools.items()
        if server_plugin.get(server_name) == plugin["name"]
    )
    agents_dir = plugin["dir"] / "agents"
    skills_dir = plugin["dir"] / "skills"
    actual_counts[plugin["name"]] = {
        "command": n_commands,
        "tool": n_tools,
        "agent": len(list(agents_dir.glob("*.md"))) if agents_dir.is_dir() else 0,
        "skill": len(list(skills_dir.glob("*/SKILL.md"))) if skills_dir.is_dir() else 0,
    }

totals = {kind: sum(c[kind] for c in actual_counts.values()) for kind in ("command", "tool", "agent", "skill")}

drift_errors = 0


def check_claim(where: str, plugin_name: str | None, claimed: int, kind: str) -> None:
    global drift_errors
    if plugin_name is not None:
        actual = actual_counts.get(plugin_name, {}).get(kind)
        scope = plugin_name
    else:
        actual = totals[kind]
        scope = "repo total"
    if actual is None:
        return
    if claimed != actual:
        fail(f"{where}: claims {claimed} {kind}s for {scope}, actual count is {actual}")
        drift_errors += 1
    else:
        ok(f"{where}: {claimed} {kind}s ({scope}) matches actual count")


def scan_claims(text: str, where: str, plugin_name: str | None) -> None:
    for match in CLAIM_RE.finditer(text):
        kind = match.group(3).lower().rstrip("s")
        check_claim(where, plugin_name, int(match.group(1)), kind)


# marketplace.json and plugin.json descriptions — scoped to their plugin.
for plugin in plugins:
    scan_claims(plugin["description"], f"marketplace.json [{plugin['name']}]", plugin["name"])
    pj_desc = plugin_json_by_name.get(plugin["name"], {}).get("description", "")
    scan_claims(pj_desc, f"{plugin['dir'].name}/.claude-plugin/plugin.json", plugin["name"])

# Root README — claims are scoped by the enclosing '### [plugin](dir/)' section.
readme_path = REPO_ROOT / "README.md"
if readme_path.is_file():
    dir_to_name = {plugin["dir"].name.lower(): plugin["name"] for plugin in plugins}
    name_set = {plugin["name"].lower(): plugin["name"] for plugin in plugins}
    current: str | None = None
    for lineno, line in enumerate(readme_path.read_text(encoding="utf-8").splitlines(), 1):
        header = re.match(r"^#{2,3}\s+\[([^\]]+)\]\(([^)]*)\)", line)
        if header:
            key_name = header.group(1).strip().lower()
            key_dir = header.group(2).strip().strip("./").rstrip("/").lower()
            current = name_set.get(key_name) or dir_to_name.get(key_dir)
        elif re.match(r"^#{1,2}\s", line):
            current = None  # left the plugin sections
        scan_claims(line, f"README.md:{lineno}", current)
else:
    fail("README.md not found at repo root")

# ── Check 7: prompt hygiene ───────────────────────────────────────────────────

print("\n== Check 7: prompt hygiene ==")
hygiene_errors = 0
for plugin in plugins:
    for sub in ("commands", "agents"):
        sub_dir = plugin["dir"] / sub
        if not sub_dir.is_dir():
            continue
        for md in sorted(sub_dir.glob("*.md")):
            text = md.read_text(encoding="utf-8")
            if WEB_OR_MCP_RE.search(text) and INJECTION_PHRASE not in text:
                fail(f"{rel(md)}: reads web/MCP content but lacks the standard injection caution ('{INJECTION_PHRASE}')")
                hygiene_errors += 1
for path in iter_md_files(REPO_ROOT):
    r = rel(path)
    if r.startswith(STALE_ALLOWED):
        continue
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = STALE_MODEL_RE.search(line)
        if m:
            fail(f"{r}:{lineno}: names a retired model or setting ({m.group(0)!r})")
            hygiene_errors += 1
if hygiene_errors == 0:
    ok("injection cautions present; no retired model names outside STALE_ALLOWED")

# ── Result ────────────────────────────────────────────────────────────────────

print()
if failures:
    print(f"RESULT: FAIL ({len(failures)} problem{'s' if len(failures) != 1 else ''})")
    sys.exit(1)
print("RESULT: PASS")
