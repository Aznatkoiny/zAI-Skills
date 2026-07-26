#!/usr/bin/env bash
# Smoke-test the committed MCP servers from a plain checkout — NO npm install.
#
#   - Boots each Node server directly from its committed dist/index.cjs and
#     drives a JSON-RPC initialize + tools/list handshake over stdio, asserting
#     the expected tool count.
#   - For the Python server: py_compile + offline unittest discovery.
#   - bash -n syntax-checks every hooks/*.sh.
#
# Requirements: node (>=18), python3. Exits nonzero on any failure.
#
# Usage: bash scripts/smoke_servers.sh

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILURES=0

fail() {
  echo "  FAIL  $*"
  FAILURES=$((FAILURES + 1))
}

ok() {
  echo "  ok    $*"
}

# ── Node servers: initialize + tools/list over stdio ─────────────────────────

smoke_node_server() {
  local label="$1" dist="$2" expected="$3"
  if [ ! -f "$ROOT/$dist" ]; then
    fail "$label: committed bundle $dist not found"
    return
  fi
  local out
  out=$(printf '%s\n%s\n%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0.0.0"}}}' \
    '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
    | timeout 30 node "$ROOT/$dist" 2>/dev/null)
  local status=$?
  if [ $status -ne 0 ] && [ -z "$out" ]; then
    fail "$label: server did not respond over stdio (exit $status)"
    return
  fi
  local count
  count=$(printf '%s\n' "$out" | python3 -c '
import json, sys
count = None
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    if msg.get("id") == 2 and "result" in msg:
        count = len(msg["result"].get("tools", []))
print(count if count is not None else "none")
')
  if [ "$count" = "none" ]; then
    fail "$label: no tools/list response received"
  elif [ "$count" != "$expected" ]; then
    fail "$label: tools/list returned $count tools, expected $expected"
  else
    ok "$label: booted from committed bundle, tools/list returned $count tools"
  fi
}

echo "== Node MCP servers (committed dist, no npm install) =="
smoke_node_server "job-intelligence" \
  "career-coach/mcp-servers/job-intelligence/dist/index.cjs" 5
smoke_node_server "financial-intelligence" \
  "consulting-toolkit/mcp-servers/financial-intelligence/dist/index.cjs" 8

# ── Python server: compile + offline unit tests ──────────────────────────────

echo "== Python MCP server (real-estate-data) =="
PY_DIR="$ROOT/real-estate-investment/mcp-servers/real-estate-data"
if [ ! -f "$PY_DIR/server.py" ]; then
  fail "real-estate-data: server.py not found"
else
  if python3 -m py_compile "$PY_DIR/server.py"; then
    ok "real-estate-data: server.py compiles"
  else
    fail "real-estate-data: server.py failed py_compile"
  fi
  UT_LOG="$(mktemp)"
  if (cd "$PY_DIR" && python3 -m unittest discover -s . -p 'test_*.py' -v) > "$UT_LOG" 2>&1; then
    ok "real-estate-data: unittest discovery passed ($(grep -c '\.\.\. ok' "$UT_LOG" || true) tests)"
  else
    fail "real-estate-data: unit tests failed"
    tail -n 40 "$UT_LOG" | sed 's/^/        /'
  fi
  rm -f "$UT_LOG"
fi

# ── Hook scripts: bash syntax check ──────────────────────────────────────────

echo "== Hook scripts (bash -n) =="
HOOK_COUNT=0
while IFS= read -r hook; do
  HOOK_COUNT=$((HOOK_COUNT + 1))
  if bash -n "$hook"; then
    ok "${hook#"$ROOT"/}: syntax OK"
  else
    fail "${hook#"$ROOT"/}: bash -n failed"
  fi
done < <(find "$ROOT" -path '*/node_modules' -prune -o -type f -path '*/hooks/*.sh' -print | sort)
if [ "$HOOK_COUNT" -eq 0 ]; then
  fail "no hooks/*.sh scripts found (expected at least one)"
fi

# ── Result ───────────────────────────────────────────────────────────────────

echo
if [ "$FAILURES" -gt 0 ]; then
  echo "RESULT: FAIL ($FAILURES problems)"
  exit 1
fi
echo "RESULT: PASS"
