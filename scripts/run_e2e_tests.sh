#!/usr/bin/env bash
#
# run_e2e_tests.sh — Run E2E Playwright UI tests for the Sudoku project.
#
# Usage:
#   ./scripts/run_e2e_tests.sh              Run all E2E tests
#   ./scripts/run_e2e_tests.sh --headful    Run with visible browser
#
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
VENV_DIR="venv"
HEADLESS_FLAG=""

for arg in "$@"; do
  case "$arg" in
    --headful) HEADLESS_FLAG="HEADFUL=1" ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done

# Ensure venv exists
if [ ! -d "${VENV_DIR}" ]; then
  echo "📦 Creating virtual environment..."
  ${PYTHON} -m venv --without-pip "${VENV_DIR}"
  if [ ! -f "/tmp/get-pip.py" ]; then
    curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
  fi
  "${VENV_DIR}/bin/python3" /tmp/get-pip.py --quiet
fi

# Install dependencies
"${VENV_DIR}/bin/python3" -m pip install -q -r requirements.txt --index-url https://pypi.org/simple/ 2>/dev/null || true

# Ensure Chromium browser is installed
"${VENV_DIR}/bin/python3" -m playwright install chromium 2>/dev/null || true

echo "🎭 Running E2E Playwright tests..."
echo "────────────────────────────────────────────────────────"
echo ""

# Run E2E tests separately from API tests (they start their own Flask server)
${HEADLESS_FLAG} "${VENV_DIR}/bin/python3" -m unittest tests.test_e2e_sudoku -v 2>&1
exit_code=$?

echo ""
echo "────────────────────────────────────────────────────────"

if [ ${exit_code} -eq 0 ]; then
  echo "✅ All E2E tests passed"
else
  echo "❌ Some E2E tests failed"
fi

exit ${exit_code}
