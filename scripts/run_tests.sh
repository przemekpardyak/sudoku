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
TEST_MODULES=(test_sudoku test_storage test_app test_browser_flow test_game_api test_best_times test_stats test_solver_edge_cases test_undo_redo test_validation test_concurrency test_auto_notes test_is_valid test_export_import test_timer_pause test_seeded_puzzles test_daily_puzzle test_progress test_win_detection test_hint_counter test_edge_cases test_api_format test_firestore_serialization test_storage_behavior test_games_sort test_enhanced_stats test_board_reset test_difficulty_validation test_games_filter test_validate_endpoint test_game_lifecycle test_difficulty_stats test_archive test_solve_endpoint test_hint_endpoint test_undo_redo_behavior test_api_integration test_performance test_game_tags test_stats_summary test_weekly_puzzle test_clone_game test_board_diff test_storage_merge test_game_rating test_puzzle_quality test_enhanced_stats_v2 test_game_notes test_api_consistency test_game_search test_game_session test_solver_robustness test_achievements test_full_lifecycle test_game_favorite test_api_resilience test_puzzle_schedule test_game_timeline test_error_handling test_leaderboard test_game_replay test_data_integrity test_recommend_difficulty test_stats_export test_puzzle_analysis test_game_history test_api_discovery test_game_streaks test_deployed_service test_completion_certificate test_solver_techniques test_game_progress test_batch_operations test_game_comparison test_player_profile test_cross_endpoint test_response_format test_comprehensive test_storage_boundaries test_generation_stress test_api_docs test_new_endpoint_edges test_state_transitions test_data_flow test_concurrent_safety test_session_metrics test_malformed_input test_numeric_boundaries test_export_integrity test_query_params test_regression test_health_check)
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
      sudoku.py test_sudoku.py \
      app.py test_app.py \
      storage.py test_storage.py \
      test_browser_flow.py test_game_api.py \
      test_best_times.py test_stats.py \
      test_solver_edge_cases.py \
      requirements.txt 2>/dev/null || sleep 2
  done
else
  run_tests
  exit $?
fi
