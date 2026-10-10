#!/bin/bash
# tax-disclaimer.sh — PostToolUse hook for the real-estate-investment plugin.
# When content written or edited mentions real estate tax topics, emits one
# hookSpecificOutput.additionalContext JSON on stdout asking Claude to add a
# one-line CPA reminder if (and only if) that content gives the user tax
# guidance. Fires at most once per session; the dedupe marker lives in the
# temp directory, never in the user's project.

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

  # Once-per-session dedupe marker, kept in the temp directory so nothing is
  # written into the user's project.
  MARKER_DIR="${TMPDIR:-/tmp}/real-estate-investment-tax-reminder"
  MARKER="$MARKER_DIR/${SESSION_ID:-nosession}"

  if [[ -f "$MARKER" ]]; then
    exit 0
  fi

  # Non-fatal if the marker dir is unwritable — worst case the reminder repeats.
  mkdir -p "$MARKER_DIR" 2>/dev/null || true
  touch "$MARKER" 2>/dev/null || true

  cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[real-estate-investment] The content just written mentions real estate tax topics. If it gives the user tax guidance (depreciation, 1031, cost segregation, capital gains), add one line to your reply saying it is educational and a CPA or tax attorney should confirm it before they act. If it's code or unrelated material, ignore this. Shown once per session."}}
EOF
fi

exit 0
