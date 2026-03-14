#!/bin/bash
# Cookidoo CLI wrapper - activates venv and runs the Python CLI

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
CLI_SCRIPT="$SCRIPT_DIR/cli.py"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/venv" >&2
    echo "Please run: cd $SCRIPT_DIR && python3 -m venv venv && ./venv/bin/pip install cookidoo-api python-dotenv" >&2
    exit 1
fi

# Run the CLI with the venv Python
exec "$VENV_PYTHON" "$CLI_SCRIPT" "$@"
