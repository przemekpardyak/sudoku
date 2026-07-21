#!/usr/bin/env bash
#
# run_tests.sh — Run all unit and integration tests for the Sudoku project.
#
# Usage:
#   ./scripts/run_tests.sh              Run all tests once
#   ./scripts/run_tests.sh --watch      Re-run tests on file changes
#   ./scripts/run_tests.sh --quiet      Less verbose output
#   ./scripts/run_tests.sh --fail-fast  Stop on first failure
#
# Exit codes:
#   0 = all tests passed
#   1 = one or more tests failed
#   2 = setup/infrastructure error
#
set -euo pipefail
cd "$(dirname "$0")/.."

# ─── Config ───────────────────────────────────────────────────────────────────
PYTHON="${PYTHON:-python3}"
VENV_DIR="venv"
TEST_MODULES=(test_sudoku test_storage test_app)
WATCH_MODE=false
QUIET=false
FAIL_FAST=""
QUIET_FLAG="-v"

# ─── Parse args ──────────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --watch)     WATCH_MODE=true ;;
    --quiet)     QUIET=true; QUIET_FLAG="" ;;
    --fail-fast) FAIL_FAST="-f" ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done

# ─── Ensure venv exists ───────────────────────────────────────────────────────
setup_venv() {
  if [ ! -d "${VENV_DIR}" ]; then
    echo "📦 Creating virtual environment..."
    ${PYTHON} -m venv --without-pip "${VENV_DIR}"
    if [ ! -f "/tmp/get-pip.py" ]; then
      curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    fi
    "${VENV_DIR}/bin/python3" /tmp/get-pip.py --quiet
  fi
  # Install/upgrade dependencies
  "${VENV_DIR}/bin/python3" -m pip install -q -r requirements.txt 2>/dev/null || true
}

setup_venv

# ─── Run tests ────────────────────────────────────────────────────────────────
run_tests() {
  local start_time=$SECONDS
  local test_args="${QUIET_FLAG} ${FAIL_FAST}"

  echo "🧪 Running all tests..."
  echo "   Modules: ${TEST_MODULES[*]}"
  echo "────────────────────────────────────────────────────────"
  echo ""

  "${VENV_DIR}/bin/python3" -m unittest "${TEST_MODULES[@]}" ${test_args} 2>&1
  local exit_code=$?

  local elapsed=$(( SECONDS - start_time ))

  echo ""
  echo "────────────────────────────────────────────────────────"

  if [ ${exit_code} -eq 0 ]; then
    echo "✅ All tests passed (${elapsed}s)"
  else
    echo "❌ Some tests failed (${elapsed}s)"
  fi

  return ${exit_code}
}

# ─── Watch mode ───────────────────────────────────────────────────────────────
if [ "${WATCH_MODE}" = true ]; then
  echo "👀 Watch mode: re-running tests on file changes (Ctrl+C to stop)"
  echo ""
  while true; do
    clear
    run_tests || true
    echo ""
    echo "⏳ Waiting for file changes... (Ctrl+C to stop)"
    # Watch all Python files in the project root
    inotifywait -q -e modify -e create -e delete \
      sudoku.py test_sudoku.py \
      app.py test_app.py \
      storage.py test_storage.py \
      requirements.txt 2>/dev/null || sleep 2
  done
else
  run_tests
  exit $?
fi
