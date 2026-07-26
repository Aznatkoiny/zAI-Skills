#!/usr/bin/env bash
set -euo pipefail

# compile-latex.sh — PostToolUse hook for career-coach plugin
# Reads tool payload JSON from stdin, compiles .tex or converts .md resumes to PDF.

# Read stdin into a variable
INPUT="$(cat)"

# Extract file_path from tool_input using python3. Skips the hook entirely when
# the tool call itself failed (tool_response.success == false). Works for Write,
# Edit and MultiEdit payloads alike — all carry tool_input.file_path.
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

# Guard: must be under a /resumes/ path
if [[ "$FILE_PATH" != */resumes/* ]]; then
  exit 0
fi

# Guard: must be .md or .tex
EXT="${FILE_PATH##*.}"
if [[ "$EXT" != "md" && "$EXT" != "tex" ]]; then
  exit 0
fi

# Derive output PDF path (same dir, same basename)
DIR="$(dirname -- "$FILE_PATH")"
BASENAME="$(basename -- "$FILE_PATH" ".$EXT")"
PDF_PATH="$DIR/$BASENAME.pdf"

cleanup_aux() {
  for EXT_CLEAN in aux log out fls fdb_latexmk xdv; do
    rm -f -- "$DIR/$BASENAME.$EXT_CLEAN"
  done
}

if [[ "$EXT" == "tex" ]]; then
  # --- Compile .tex: prefer latexmk -xelatex (multi-pass), else single pass ---
  if command -v latexmk &>/dev/null && command -v xelatex &>/dev/null; then
    echo "[career-coach hook] Compiling $FILE_PATH with latexmk -xelatex ..." >&2
    if ! latexmk -xelatex -interaction=nonstopmode -output-directory="$DIR" "$FILE_PATH" >&2; then
      echo "[career-coach hook] LaTeX compilation failed for $FILE_PATH — see $DIR/$BASENAME.log, fix the source and save again to retry." >&2
      exit 0
    fi
  else
    if command -v xelatex &>/dev/null; then
      LATEX_BIN="xelatex"
    elif command -v pdflatex &>/dev/null; then
      LATEX_BIN="pdflatex"
    else
      echo "[career-coach hook] xelatex/pdflatex not found. Install TeX Live or MiKTeX to auto-compile resumes." >&2
      exit 0
    fi

    echo "[career-coach hook] Compiling $FILE_PATH with $LATEX_BIN ..." >&2
    if ! "$LATEX_BIN" -interaction=nonstopmode -output-directory="$DIR" "$FILE_PATH" >&2; then
      echo "[career-coach hook] LaTeX compilation failed for $FILE_PATH — see $DIR/$BASENAME.log, fix the source and save again to retry." >&2
      exit 0
    fi
  fi

  # Clean up auxiliary files
  cleanup_aux

  echo "[career-coach hook] PDF written to $PDF_PATH" >&2

elif [[ "$EXT" == "md" ]]; then
  # --- Convert .md to PDF with pandoc ---
  if ! command -v pandoc &>/dev/null; then
    echo "[career-coach hook] pandoc not found. Install pandoc to auto-convert Markdown resumes to PDF." >&2
    exit 0
  fi

  if command -v xelatex &>/dev/null; then
    PDF_ENGINE="xelatex"
  elif command -v pdflatex &>/dev/null; then
    PDF_ENGINE="pdflatex"
  else
    echo "[career-coach hook] xelatex/pdflatex not found. Install TeX Live or MiKTeX to compile Markdown resumes." >&2
    exit 0
  fi

  echo "[career-coach hook] Converting $FILE_PATH to PDF with pandoc + $PDF_ENGINE ..." >&2
  if ! pandoc "$FILE_PATH" \
    --pdf-engine="$PDF_ENGINE" \
    -V geometry:margin=0.75in \
    -V fontsize=11pt \
    -o "$PDF_PATH" >&2; then
    echo "[career-coach hook] PDF conversion failed for $FILE_PATH — fix the source and save again to retry." >&2
    exit 0
  fi

  echo "[career-coach hook] PDF written to $PDF_PATH" >&2
fi
