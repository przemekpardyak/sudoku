#!/usr/bin/env bash
# Run all unit tests for the Sudoku project.
# Usage: ./run_tests.sh [--watch]   (use --watch to re-run on file changes)
set -euo pipefail
cd "$(dirname "$0")/.."

# Ensure venv exists and dependencies are installed
if [ ! -d "venv" ]; then
    echo "⚠️  Creating virtual environment..."
    python3 -m venv --without-pip venv
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    venv/bin/python3 /tmp/get-pip.py --quiet
fi
venv/bin/python3 -m pip install -q -r requirements.txt 2>/dev/null

if [ "${1:-}" = "--watch" ]; then
    echo "👀 Watch mode: re-running tests on file changes (Ctrl+C to stop)..."
    # Use a simple polling loop since pytest-watch isn't available
    while true; do
        clear
        venv/bin/python3 -m unittest test_sudoku -v 2>&1
        echo ""
        echo "⏳ Waiting for file changes... (Ctrl+C to stop)"
        inotifywait -q -e modify -e create -e delete \
            sudoku.py test_sudoku.py app.py requirements.txt 2>/dev/null || sleep 2
    done
else
    echo "🧪 Running unit tests..."
    venv/bin/python3 -m unittest test_sudoku -v "$@"
fi
