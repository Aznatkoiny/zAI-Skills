#!/usr/bin/env bash
set -euo pipefail

# validate-profile.sh — PostToolUse hook for career-coach plugin
# When career-profile.json is written or edited, runs the advisory validator
# (scripts/validate-profile.py) and surfaces its WARN lines back to Claude as
# hookSpecificOutput.additionalContext. Never blocks the write.

INPUT="$(cat)"

# Extract file_path from tool payload; skip when the tool call itself failed.
FILE_PATH="$(printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
response = data.get('tool_response')
if isinstance(response, dict) and response.get('success') is False:
    sys.exit(0)
tool_input = data.get('tool_input', data.get('input', {})) or {}
print(tool_input.get('file_path', ''))
" 2>/dev/null || true)"

# Guard: must have a file path
if [[ -z "$FILE_PATH" ]]; then
  exit 0
fi

# Guard: neutralize paths beginning with '-' so they can't be read as options
if [[ "$FILE_PATH" == -* ]]; then
  FILE_PATH="./$FILE_PATH"
fi

# Guard: only react to career-profile.json
if [[ "$(basename -- "$FILE_PATH")" != "career-profile.json" ]]; then
  exit 0
fi

# Locate the validator relative to this hook (hooks/ -> scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$SCRIPT_DIR/../scripts/validate-profile.py"
if [[ ! -f "$VALIDATOR" ]]; then
  exit 0
fi

# Run the validator (advisory — always exits 0) and keep only WARN lines
OUTPUT="$(python3 "$VALIDATOR" "$FILE_PATH" 2>/dev/null || true)"
WARNS="$(printf '%s\n' "$OUTPUT" | grep '^WARN' || true)"

if [[ -z "$WARNS" ]]; then
  exit 0
fi

# Emit warnings as additionalContext JSON for the PostToolUse hook protocol
WARNS="$WARNS" python3 -c "
import json, os
warns = os.environ.get('WARNS', '').strip()
context = (
    'career-profile.json validation warnings (advisory, from '
    'scripts/validate-profile.py — fix in the profile, do not ignore silently):\n'
    + warns
)
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': context,
    }
}))
"
