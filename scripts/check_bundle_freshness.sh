#!/usr/bin/env bash
# Supply-chain gate for the committed MCP server bundles.
#
# For each Node MCP server, rebuilds dist/index.cjs from source in a TEMP COPY
# (npm ci + npm run build against the committed package-lock.json) and compares
# the fresh build byte-for-byte against the committed bundle. The repo working
# tree is never modified. Exits nonzero if any bundle is stale.
#
# Requirements: node >= 18, npm, network access for npm ci.
#
# Usage: bash scripts/check_bundle_freshness.sh

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILURES=0

SERVERS=(
  "career-coach/mcp-servers/job-intelligence"
  "consulting-toolkit/mcp-servers/financial-intelligence"
)

TMP_BASE="$(mktemp -d)"
trap 'rm -rf "$TMP_BASE"' EXIT

for server in "${SERVERS[@]}"; do
  src_dir="$ROOT/$server"
  name="$(basename "$server")"
  echo "== $name =="

  if [ ! -f "$src_dir/dist/index.cjs" ]; then
    echo "  FAIL  $server/dist/index.cjs is not committed"
    FAILURES=$((FAILURES + 1))
    continue
  fi

  work="$TMP_BASE/$name"
  mkdir -p "$work"
  cp "$src_dir/package.json" "$src_dir/package-lock.json" "$work/"
  [ -f "$src_dir/tsconfig.json" ] && cp "$src_dir/tsconfig.json" "$work/"
  cp -R "$src_dir/src" "$work/src"

  if ! (cd "$work" && npm ci --no-audit --no-fund --loglevel=error) > "$work/npm-ci.log" 2>&1; then
    echo "  FAIL  $name: npm ci failed"
    tail -n 20 "$work/npm-ci.log" | sed 's/^/        /'
    FAILURES=$((FAILURES + 1))
    continue
  fi

  if ! (cd "$work" && npm run build) > "$work/npm-build.log" 2>&1; then
    echo "  FAIL  $name: npm run build failed"
    tail -n 20 "$work/npm-build.log" | sed 's/^/        /'
    FAILURES=$((FAILURES + 1))
    continue
  fi

  if [ ! -f "$work/dist/index.cjs" ]; then
    echo "  FAIL  $name: build produced no dist/index.cjs"
    FAILURES=$((FAILURES + 1))
    continue
  fi

  if cmp -s "$work/dist/index.cjs" "$src_dir/dist/index.cjs"; then
    echo "  ok    $name: committed dist/index.cjs matches a fresh build from src ($(wc -c < "$src_dir/dist/index.cjs") bytes)"
  else
    echo "  FAIL  $name: committed dist/index.cjs is STALE — rebuild and commit:"
    echo "        (cd $server && npm ci && npm run build) then commit dist/index.cjs"
    FAILURES=$((FAILURES + 1))
  fi
done

echo
if [ "$FAILURES" -gt 0 ]; then
  echo "RESULT: FAIL ($FAILURES stale or unbuildable bundles)"
  exit 1
fi
echo "RESULT: PASS"
