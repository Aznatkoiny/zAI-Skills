#!/usr/bin/env bash
# Launcher for the real-estate-data MCP server.
#
# On first run this creates a virtualenv next to the server and installs
# requirements.txt into it; later runs reuse the venv (re-installing only if
# requirements.txt changes). All setup output goes to stderr because stdout
# is the MCP stdio transport and must stay clean.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
STAMP="$VENV_DIR/.requirements-installed"

log() {
    echo "[real-estate-data] $*" >&2
}

# Return the venv's python interpreter path (POSIX or Windows layout), or "".
venv_python() {
    if [ -x "$VENV_DIR/bin/python" ]; then
        echo "$VENV_DIR/bin/python"
    elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
        echo "$VENV_DIR/Scripts/python.exe"
    else
        echo ""
    fi
}

# --- Find a Python 3.10+ interpreter ----------------------------------------
# The mcp package needs Python 3.10 or newer, and some systems' default
# python3 is older, so try versioned names first.
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    log "ERROR: no Python 3.10 or newer was found on PATH."
    log "Install Python 3.10+ (https://www.python.org/downloads/), make sure it is on PATH, then restart Claude Code."
    exit 1
fi

# --- Create the venv on first run ------------------------------------------
VENV_PY="$(venv_python)"
if [ -z "$VENV_PY" ]; then
    log "First run: creating virtualenv at $VENV_DIR ..."
    if ! "$PYTHON" -m venv "$VENV_DIR" >&2; then
        log "ERROR: '$PYTHON -m venv' failed."
        log "On Debian/Ubuntu you may need: sudo apt install python3-venv"
        rm -rf "$VENV_DIR"
        exit 1
    fi
    VENV_PY="$(venv_python)"
    if [ -z "$VENV_PY" ]; then
        log "ERROR: virtualenv was created but contains no python executable."
        exit 1
    fi
fi

# --- Install dependencies (first run, or when requirements.txt changes) -----
if [ ! -f "$STAMP" ] || [ "$REQUIREMENTS" -nt "$STAMP" ]; then
    log "Installing dependencies from requirements.txt (one-time setup) ..."
    if ! "$VENV_PY" -m pip install --disable-pip-version-check -r "$REQUIREMENTS" >&2; then
        log "ERROR: pip install failed. See the output above, fix the issue, then restart Claude Code."
        exit 1
    fi
    touch "$STAMP"
    log "Dependencies installed."
fi

# --- Run the server ---------------------------------------------------------
exec "$VENV_PY" "$SCRIPT_DIR/server.py"
