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
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
VENV_DIR="venv"
TEST_MODULES=(tests.test_sudoku tests.test_storage tests.test_app tests.test_browser_flow tests.test_game_api tests.test_best_times tests.test_stats tests.test_solver_edge_cases tests.test_undo_redo tests.test_validation tests.test_concurrency tests.test_auto_notes tests.test_is_valid tests.test_export_import tests.test_timer_pause tests.test_seeded_puzzles tests.test_daily_puzzle tests.test_progress tests.test_win_detection tests.test_hint_counter tests.test_edge_cases tests.test_api_format tests.test_firestore_serialization tests.test_storage_behavior tests.test_games_sort tests.test_enhanced_stats tests.test_board_reset tests.test_difficulty_validation tests.test_games_filter tests.test_validate_endpoint tests.test_game_lifecycle tests.test_difficulty_stats tests.test_archive tests.test_solve_endpoint tests.test_hint_endpoint tests.test_undo_redo_behavior tests.test_api_integration tests.test_performance tests.test_game_tags tests.test_stats_summary tests.test_weekly_puzzle tests.test_clone_game tests.test_board_diff tests.test_storage_merge tests.test_game_rating tests.test_puzzle_quality tests.test_enhanced_stats_v2 tests.test_game_notes tests.test_api_consistency tests.test_game_search tests.test_game_session tests.test_solver_robustness tests.test_achievements tests.test_full_lifecycle tests.test_game_favorite tests.test_api_resilience tests.test_puzzle_schedule tests.test_game_timeline tests.test_error_handling tests.test_leaderboard tests.test_game_replay tests.test_data_integrity tests.test_recommend_difficulty tests.test_stats_export tests.test_puzzle_analysis tests.test_game_history tests.test_api_discovery tests.test_game_streaks tests.test_deployed_service tests.test_completion_certificate tests.test_solver_techniques tests.test_game_progress tests.test_batch_operations tests.test_game_comparison tests.test_player_profile tests.test_cross_endpoint tests.test_response_format tests.test_comprehensive tests.test_storage_boundaries tests.test_generation_stress tests.test_api_docs tests.test_new_endpoint_edges tests.test_state_transitions tests.test_data_flow tests.test_concurrent_safety tests.test_session_metrics tests.test_malformed_input tests.test_numeric_boundaries tests.test_export_integrity tests.test_query_params tests.test_regression tests.test_health_check)
WATCH_MODE=false
QUIET_FLAG="-v"
FAIL_FAST=""

for arg in "$@"; do
  case "$arg" in
    --watch)     WATCH_MODE=true ;;
    --quiet)     QUIET_FLAG="" ;;
    --fail-fast) FAIL_FAST="-f" ;;
    *) echo "Unknown option: $arg"; exit 2 ;;
  esac
done

setup_venv() {
  if [ ! -d "${VENV_DIR}" ]; then
    echo "📦 Creating virtual environment..."
    ${PYTHON} -m venv --without-pip "${VENV_DIR}"
    if [ ! -f "/tmp/get-pip.py" ]; then
      curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    fi
    "${VENV_DIR}/bin/python3" /tmp/get-pip.py --quiet
  fi
  "${VENV_DIR}/bin/python3" -m pip install -q -r requirements.txt 2>/dev/null || true
}

setup_venv

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

if [ "${WATCH_MODE}" = true ]; then
  echo "👀 Watch mode: re-running tests on file changes (Ctrl+C to stop)"
  echo ""
  while true; do
    clear
    run_tests || true
    echo ""
    echo "⏳ Waiting for file changes... (Ctrl+C to stop)"
    inotifywait -q -e modify -e create -e delete \
      sudoku.py tests/test_sudoku.py \
      app.py tests/test_app.py \
      storage.py tests/test_storage.py \
      tests/test_browser_flow.py tests/test_game_api.py \
      tests/test_best_times.py tests/test_stats.py \
      tests/test_solver_edge_cases.py \
      requirements.txt 2>/dev/null || sleep 2
  done
else
  run_tests
  exit $?
fi
