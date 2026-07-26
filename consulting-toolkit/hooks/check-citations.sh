#!/bin/bash
# check-citations.sh — PostToolUse hook for the consulting-toolkit plugin.
# When a consulting deliverable is written or edited with quantitative claim
# lines that lack a bracketed [Source, ...] citation, emits ONE
# hookSpecificOutput.additionalContext JSON on stdout summarizing up to 5
# offending lines, so Claude flags the gap and suggests /partner-review.
#
# Deliverable detection: markdown files whose basename carries a memo/sizing/
# profile segment (covers this plugin's naming conventions — dd-memo-*.md,
# market-sizing-*.md, company-profile-*.md — as well as plain *-memo.md,
# *-sizing.md, *-profile.md), plus anything under a deliverables/ directory.
#
# Matching is deliberately conservative: code fences are skipped, headers
# (including dated headers) are skipped, table separator rows and TOC link
# lines are skipped, list numbering is stripped, and only digits attached to a
# unit signal (currency, %, B/M/K/bn/mm, bps/pp, or an "x" multiple) count as
# quantitative claims. Lines mentioning "assumption" are treated as explicitly
# labeled and skipped, matching the agents' sourcing standard.
#
# Fires at most once per session (marker file), following the pattern of
# real-estate-investment/hooks/tax-disclaimer.sh.

# Read tool payload from stdin
INPUT=$(cat)

# Python does all parsing and matching. The code is loaded through a quoted
# heredoc so bash performs no interpolation on it. On a hit, it prints the
# session id on line 1 and the complete hook JSON payload on line 2.
PYCODE=$(cat <<'PYEOF'
import sys, json, re

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get('tool_input') or {}
file_path = tool_input.get('file_path', '')
if not isinstance(file_path, str) or not file_path.endswith('.md'):
    sys.exit(0)

basename = file_path.rsplit('/', 1)[-1]
is_deliverable = (
    re.search(r'(?:^|[-_])(?:memo|sizing|profile)(?:[-_.])', basename) is not None
    or '/deliverables/' in file_path
    or file_path.startswith('deliverables/')
)
if not is_deliverable:
    sys.exit(0)

# Collect only the written content (Write content / Edit new_string /
# MultiEdit edits[].new_string) — never the whole payload, which would
# false-positive on file paths and old_string context.
parts = []
for key in ('content', 'new_string'):
    value = tool_input.get(key)
    if isinstance(value, str):
        parts.append(value)
for edit in tool_input.get('edits') or []:  # MultiEdit payloads
    if isinstance(edit, dict) and isinstance(edit.get('new_string'), str):
        parts.append(edit['new_string'])
text = '\n'.join(parts)
if not text:
    sys.exit(0)

FENCE = ('\x60\x60\x60', '~~~')  # ``` or ~~~ code fences

# A citation is a bracket whose contents include a comma or colon:
# [Statista, 2025], [SEC EDGAR, 2025-05-01], [Analyst calculation: ...].
# Markdown links [text](url) also count as sourced — conservative.
CITED = re.compile(r'\[[^\][]*[,:][^\][]*\]|\]\(')

# A quantitative claim: a digit attached to a unit signal. Bare integers
# (list numbering, section references, years in prose, dates) never match.
QUANT = re.compile(
    r'[$\u20ac\u00a3\u00a5]\s?\d'                       # currency symbols
    r'|\d[\d,.]*\s?%'                                   # percentages
    r'|\b\d[\d,.]*\s?(?:bn|mm|[BMK])\b'                 # magnitude suffixes
    r'|\b\d[\d,.]*\s?(?:billion|million|thousand|bps|pp)\b'
    r'|\b\d+(?:\.\d+)?x\b',                             # multiples (3.2x)
    re.IGNORECASE)

offending = []
in_fence = False
for raw in text.splitlines():
    line = raw.strip()
    if line.startswith(FENCE):
        in_fence = not in_fence
        continue
    if in_fence or not line:
        continue
    if line.startswith('#'):                    # headers, incl. dated headers
        continue
    if re.fullmatch(r'[|\s:\-]+', line):        # table separator rows
        continue
    if re.match(r'^(?:[-*+]|\d+[.)])\s*\[[^\]]*\]\(#', line):  # TOC links
        continue
    if re.search(r'\bassumptions?\b', line, re.IGNORECASE):
        continue                                # explicitly labeled assumption
    # Strip list numbering ("1." / "2)") so it never reads as a claim.
    stripped = re.sub(r'^\d+[.)]\s+', '', line)
    if QUANT.search(stripped) and not CITED.search(stripped):
        offending.append(stripped[:120])
        if len(offending) >= 5:
            break

if not offending:
    sys.exit(0)

n = len(offending)
suffix = ' (first 5 shown)' if n >= 5 else ''
quoted = ' | '.join('"' + l + '"' for l in offending)
message = (
    str(n) + ' quantitative line(s) lack [Source, Date] citations in '
    + basename + ' — run /partner-review before sending' + suffix
    + '. Offending lines: ' + quoted
)
payload = {
    'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': message,
    }
}
print(str(data.get('session_id', '')))
print(json.dumps(payload))
PYEOF
)

RESULT=$(printf '%s' "$INPUT" | python3 -c "$PYCODE" 2>/dev/null || true)

if [[ -n "$RESULT" ]]; then
  SESSION_ID="${RESULT%%$'\n'*}"
  PAYLOAD="${RESULT#*$'\n'}"

  # Once-per-session dedupe marker. Prefer the project's .claude dir; fall
  # back to TMPDIR. Keyed by session id when one is available.
  if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
    MARKER_DIR="${CLAUDE_PROJECT_DIR}/.claude"
  else
    MARKER_DIR="${TMPDIR:-/tmp}"
  fi
  MARKER="$MARKER_DIR/.citation-lint-shown${SESSION_ID:+-$SESSION_ID}"

  if [[ -f "$MARKER" ]]; then
    exit 0
  fi

  # Non-fatal if the marker dir is unwritable — worst case the reminder repeats.
  mkdir -p "$MARKER_DIR" 2>/dev/null || true
  touch "$MARKER" 2>/dev/null || true

  printf '%s\n' "$PAYLOAD"
fi

exit 0
