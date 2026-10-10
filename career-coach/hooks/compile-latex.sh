#!/usr/bin/env bash
set -euo pipefail

# compile-latex.sh — PostToolUse hook for the career-coach plugin.
# When a .tex or .md file under a resumes/ folder is written or edited in a
# career-coach project, build a PDF next to it (latexmk/xelatex for .tex,
# pandoc for .md) and tell Claude what happened through
# hookSpecificOutput.additionalContext: the PDF path, the log to read on
# failure, or which tool is missing. Output on stderr never reaches Claude for
# PostToolUse hooks, which is why results are reported this way.

INPUT="$(cat)"

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

[[ -z "$FILE_PATH" ]] && exit 0
# Neutralize paths beginning with '-' so they can't be read as options
[[ "$FILE_PATH" == -* ]] && FILE_PATH="./$FILE_PATH"

# Only resumes/*.md or resumes/*.tex
[[ "$FILE_PATH" != */resumes/* ]] && exit 0
EXT="${FILE_PATH##*.}"
[[ "$EXT" != "md" && "$EXT" != "tex" ]] && exit 0

DIR="$(dirname -- "$FILE_PATH")"
BASENAME="$(basename -- "$FILE_PATH" ".$EXT")"
PDF_PATH="$DIR/$BASENAME.pdf"
LOG_PATH="$DIR/$BASENAME.build.log"

# Only in career-coach projects: a career-profile.json in the project root or
# next to the resumes folder. Keeps the hook out of unrelated repos that happen
# to have a resumes/ directory.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
if [[ ! -f "$PROJECT_DIR/career-profile.json" && ! -f "$DIR/../career-profile.json" ]]; then
  exit 0
fi

report() {
  MSG="$1" python3 -c "
import json, os
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': '[career-coach PDF build] ' + os.environ['MSG']}}))
"
  exit 0
}

cleanup_aux() {
  for EXT_CLEAN in aux log out fls fdb_latexmk xdv; do
    rm -f -- "$DIR/$BASENAME.$EXT_CLEAN"
  done
}

if command -v xelatex &>/dev/null; then
  ENGINE="xelatex"
elif command -v pdflatex &>/dev/null; then
  ENGINE="pdflatex"
else
  report "No PDF was built for $FILE_PATH: no LaTeX engine (xelatex or pdflatex) is installed. The source file is saved and usable. Tell the user, and offer options: install TeX Live (macOS: 'brew install --cask mactex-no-gui'; Ubuntu/Debian: 'sudo apt install texlive-xetex texlive-fonts-extra'), upload the .tex to Overleaf, or use the Markdown version."
fi

if [[ "$EXT" == "tex" ]]; then
  if command -v latexmk &>/dev/null && [[ "$ENGINE" == "xelatex" ]]; then
    BUILD=(latexmk -xelatex -interaction=nonstopmode -output-directory="$DIR" "$FILE_PATH")
  else
    BUILD=("$ENGINE" -interaction=nonstopmode -output-directory="$DIR" "$FILE_PATH")
  fi
  if ! "${BUILD[@]}" >"$LOG_PATH" 2>&1; then
    report "LaTeX build failed for $FILE_PATH. The build log is at $LOG_PATH; read its last lines for the error, fix the source, and save again to rebuild. Templates need TeX Gyre fonts, and awesome-cv also needs fontawesome5."
  fi
  cleanup_aux
else
  if ! command -v pandoc &>/dev/null; then
    report "No PDF was built for $FILE_PATH: pandoc isn't installed (it converts Markdown to PDF). The Markdown file is saved. Tell the user they can install pandoc (macOS: 'brew install pandoc'; Ubuntu/Debian: 'sudo apt install pandoc'), or use a LaTeX template instead (/resume-generator --template jakes-resume)."
  fi
  if ! pandoc "$FILE_PATH" --pdf-engine="$ENGINE" -V geometry:margin=0.75in -V fontsize=11pt -o "$PDF_PATH" >"$LOG_PATH" 2>&1; then
    report "PDF conversion failed for $FILE_PATH. The log is at $LOG_PATH; fix the source and save again to rebuild."
  fi
fi

rm -f -- "$LOG_PATH"
report "PDF built: $PDF_PATH"
