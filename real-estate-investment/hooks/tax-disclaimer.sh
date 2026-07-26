#!/bin/bash
# tax-disclaimer.sh — PostToolUse hook for the real-estate-investment plugin.
# When written/edited content touches tax-specific topics, emits additionalContext
# JSON on stdout so Claude reminds the user to consult a CPA or tax attorney.
# Fires at most once per session (marker file).

# Read tool payload from stdin
INPUT=$(cat)

# Parse the JSON with python3 and match word-boundary tax terms against the
# written content only (tool_input.content / new_string / edits). A raw grep
# over the whole payload would false-positive on words like "syntax" or
# "taxonomy", or on "tax" appearing in tool_input.file_path — so file_path is
# deliberately excluded from matching. On match, prints "match:<session_id>".
MATCHED=$(printf '%s' "$INPUT" | python3 -c "
import sys, json, re

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get('tool_input') or {}
file_path = tool_input.get('file_path', '')  # extracted but never matched on

parts = []
for key in ('content', 'new_string'):
    value = tool_input.get(key)
    if isinstance(value, str):
        parts.append(value)
for edit in tool_input.get('edits') or []:  # MultiEdit payloads
    if isinstance(edit, dict) and isinstance(edit.get('new_string'), str):
        parts.append(edit['new_string'])
text = '\n'.join(parts)

terms = [
    r'1031',
    r'cost\s+segregation',
    r'depreciation(?:\s+recapture)?',
    r'opportunity\s+zone',
    r'entity\s+structure',
    r'capital\s+gains',
]
pattern = r'\b(?:' + '|'.join(terms) + r')\b'
if re.search(pattern, text, re.IGNORECASE):
    print('match:' + str(data.get('session_id', '')), end='')
" 2>/dev/null || true)

if [[ -n "$MATCHED" ]]; then
  SESSION_ID="${MATCHED#match:}"

  # Once-per-session dedupe marker. Prefer the project's .claude dir; fall
  # back to TMPDIR. Keyed by session id when one is available.
  if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
    MARKER_DIR="${CLAUDE_PROJECT_DIR}/.claude"
  else
    MARKER_DIR="${TMPDIR:-/tmp}"
  fi
  MARKER="$MARKER_DIR/.tax-disclaimer-shown${SESSION_ID:+-$SESSION_ID}"

  if [[ -f "$MARKER" ]]; then
    exit 0
  fi

  # Non-fatal if the marker dir is unwritable — worst case the reminder repeats.
  mkdir -p "$MARKER_DIR" 2>/dev/null || true
  touch "$MARKER" 2>/dev/null || true

  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Reminder: Tax analysis is for educational purposes only. Recommend the user consult a CPA or tax attorney before acting on it."}}
EOF
fi

exit 0
