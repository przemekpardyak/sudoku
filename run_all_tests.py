#!/usr/bin/env python3
"""
run_all_tests.py — Categorized test runner with progress output.

Runs all tests in meaningful categories, showing pass/fail counts per category.

Categories:
  1. Unit           — Pure function tests (solver, validation, generation)
  2. Storage        — Data layer tests (InMemoryStorage, Firestore serialization)
  3. Integration    — API endpoint tests via Flask test client
  4. E2E            — Browser tests via Playwright (requires running app)
  5. Deployed       — Smoke tests against live Cloud Run (skipped by default)

Usage:
  python3 run_all_tests.py                    Run all categories except E2E
  python3 run_all_tests.py --all              Run everything including E2E
  python3 run_all_tests.py --category unit     Run only unit tests
  python3 run_all_tests.py --category storage  Run only storage tests
  python3 run_all_tests.py --category integration
  python3 run_all_tests.py --category e2e
  python3 run_all_tests.py --fail-fast        Stop on first failure
  python3 run_all_tests.py --watch            Re-run on file changes
"""
import sys
import os
import time
import unittest
import argparse
import subprocess

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─── Test Categories ──────────────────────────────────────────────────────────

# Unit tests: test pure Python functions in sudoku.py — no HTTP, no Flask, no storage
UNIT_TESTS = [
    "tests.test_sudoku",
    "tests.test_is_valid",
    "tests.test_solver_edge_cases",
    "tests.test_solver_robustness",
    "tests.test_solver_techniques",
    "tests.test_generation_stress",
    "tests.test_puzzle_quality",
    "tests.test_difficulty_validation",
    "tests.test_validation",
    "tests.test_performance",
]

# Storage tests: test InMemoryStorage and FirestoreStorage classes directly
STORAGE_TESTS = [
    "tests.test_storage",
    "tests.test_storage_behavior",
    "tests.test_storage_boundaries",
    "tests.test_storage_merge",
    "tests.test_firestore_serialization",
]

# Integration tests: test Flask API endpoints via app.test_client()
INTEGRATION_TESTS = [
    "tests.test_app",
    "tests.test_game_api",
    "tests.test_best_times",
    "tests.test_stats",
    "tests.test_stats_summary",
    "tests.test_enhanced_stats",
    "tests.test_enhanced_stats_v2",
    "tests.test_difficulty_stats",
    "tests.test_stats_export",
    "tests.test_undo_redo",
    "tests.test_undo_redo_behavior",
    "tests.test_concurrency",
    "tests.test_auto_notes",
    "tests.test_export_import",
    "tests.test_export_integrity",
    "tests.test_timer_pause",
    "tests.test_seeded_puzzles",
    "tests.test_daily_puzzle",
    "tests.test_weekly_puzzle",
    "tests.test_progress",
    "tests.test_win_detection",
    "tests.test_hint_counter",
    "tests.test_edge_cases",
    "tests.test_api_format",
    "tests.test_games_sort",
    "tests.test_board_reset",
    "tests.test_games_filter",
    "tests.test_validate_endpoint",
    "tests.test_game_lifecycle",
    "tests.test_archive",
    "tests.test_solve_endpoint",
    "tests.test_hint_endpoint",
    "tests.test_api_integration",
    "tests.test_game_tags",
    "tests.test_clone_game",
    "tests.test_board_diff",
    "tests.test_game_rating",
    "tests.test_game_notes",
    "tests.test_api_consistency",
    "tests.test_game_search",
    "tests.test_game_session",
    "tests.test_achievements",
    "tests.test_full_lifecycle",
    "tests.test_game_favorite",
    "tests.test_api_resilience",
    "tests.test_puzzle_schedule",
    "tests.test_game_timeline",
    "tests.test_error_handling",
    "tests.test_leaderboard",
    "tests.test_game_replay",
    "tests.test_data_integrity",
    "tests.test_recommend_difficulty",
    "tests.test_puzzle_analysis",
    "tests.test_game_history",
    "tests.test_api_discovery",
    "tests.test_game_streaks",
    "tests.test_completion_certificate",
    "tests.test_game_progress",
    "tests.test_batch_operations",
    "tests.test_game_comparison",
    "tests.test_player_profile",
    "tests.test_cross_endpoint",
    "tests.test_response_format",
    "tests.test_comprehensive",
    "tests.test_new_endpoint_edges",
    "tests.test_state_transitions",
    "tests.test_data_flow",
    "tests.test_concurrent_safety",
    "tests.test_session_metrics",
    "tests.test_malformed_input",
    "tests.test_numeric_boundaries",
    "tests.test_query_params",
    "tests.test_regression",
    "tests.test_health_check",
    "tests.test_api_docs",
    "tests.test_browser_flow",
]

# Deployed tests: HTTP smoke tests against running Flask app (auto-starts)
DEPLOYED_TESTS = [
    "tests.test_deployed_service",
]

# E2E tests: real browser via Playwright (run separately, needs running app)
E2E_TESTS = [
    "tests.test_e2e_sudoku",
]

CATEGORIES = {
    "unit": ("🔧 Unit Tests", UNIT_TESTS),
    "storage": ("💾 Storage Tests", STORAGE_TESTS),
    "integration": ("🔗 Integration Tests", INTEGRATION_TESTS),
    "deployed": ("🌐 Deployed/HTTP Tests", DEPLOYED_TESTS),
    "e2e": ("🎭 E2E UI Tests", E2E_TESTS),
}


# ─── Color helpers ────────────────────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def color(text, c):
    return f"{c}{text}{RESET}"


# ─── Runner ────────────────────────────────────────────────────────────────────

def run_category(name, label, modules, fail_fast=False):
    """Run a single category and return (total, passed, failed, errors, skipped, duration)."""
    print(f"\n{'─' * 60}")
    print(f"  {color(label, CYAN)}")
    print(f"  {len(modules)} module(s): {', '.join(m.replace('tests.', '') for m in modules[:8])}"
          + (" ..." if len(modules) > 8 else ""))
    print(f"{'─' * 60}")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for mod in modules:
        try:
            tests = loader.loadTestsFromName(mod)
            suite.addTests(tests)
        except Exception as e:
            print(f"  {color('⚠', YELLOW)} Failed to load {mod}: {e}")

    total = suite.countTestCases()
    if total == 0:
        print(f"  {color('⚠', YELLOW)} No tests found")
        return 0, 0, 0, 0, 0, 0

    # Custom result class for progress
    class ProgressResult(unittest.TextTestRunner):
        pass

    # Use a result that shows progress
    class ProgressTextResult(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.passed_count = 0
            self.failed_count = 0
            self.error_count = 0
            self.skipped_count = 0
            self._last_milestone = 0

        def addSuccess(self, test):
            super().addSuccess(test)
            self.passed_count += 1
            self._print_progress()

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.failed_count += 1
            self._print_progress()

        def addError(self, test, err):
            super().addError(test, err)
            self.error_count += 1
            self._print_progress()

        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            self.skipped_count += 1
            self._print_progress()

        def _print_progress(self):
            done = self.passed_count + self.failed_count + self.error_count + self.skipped_count
            pct = done * 100 // total if total else 0
            # Print on every 5% milestone or on failures/errors or at 100%
            milestone = pct // 5
            should_print = (milestone > self._last_milestone) or (self.failed_count > 0) or (self.error_count > 0) or (done == total)
            if not should_print:
                return
            self._last_milestone = milestone

            bar_filled = done * 30 // total if total else 0
            bar = "█" * bar_filled + "░" * (30 - bar_filled)
            status_parts = [f"{color(str(self.passed_count), GREEN)} passed"]
            if self.failed_count:
                status_parts.append(f"{color(str(self.failed_count), RED)} failed")
            if self.error_count:
                status_parts.append(f"{color(str(self.error_count), RED)} errors")
            if self.skipped_count:
                status_parts.append(f"{color(str(self.skipped_count), YELLOW)} skipped")
            status = " · ".join(status_parts)
            print(f"  [{bar}] {done}/{total} ({pct}%) — {status}", flush=True)

    runner = unittest.TextTestRunner(
        stream=sys.stdout,
        verbosity=0,
        resultclass=ProgressTextResult,
        failfast=fail_fast,
    )

    start = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start

    # Clear progress line and print summary
    sys.stdout.write(f"\r{' ' * 80}\r")
    sys.stdout.flush()

    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)

    icon = color("✅", GREEN) if failed == 0 and errors == 0 else color("❌", RED)
    print(f"  {icon} {passed + failed + errors + skipped} tests in {elapsed:.1f}s"
          f" — {color(str(passed), GREEN)} passed"
          + (f", {color(str(failed), RED)} failed" if failed else "")
          + (f", {color(str(errors), RED)} errors" if errors else "")
          + (f", {color(str(skipped), YELLOW)} skipped" if skipped else ""))

    # Print failure details
    if result.failures or result.errors:
        for test, traceback in result.failures + result.errors:
            print(f"\n  {color('FAIL', RED)}: {test}")
            # Print last few lines of traceback
            lines = traceback.strip().split('\n')
            for line in lines[-5:]:
                print(f"    {line}")

    return total, passed, failed, errors, skipped, elapsed


def main():
    parser = argparse.ArgumentParser(description="Run categorized tests with progress")
    parser.add_argument("--category", choices=list(CATEGORIES.keys()),
                        help="Run only a specific category")
    parser.add_argument("--all", action="store_true",
                        help="Run all categories including E2E")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Stop on first failure")
    parser.add_argument("--watch", action="store_true",
                        help="Re-run tests on file changes")
    args = parser.parse_args()

    # Ensure venv exists
    venv_dir = os.path.join(os.path.dirname(__file__), "venv")
    if not os.path.isdir(venv_dir):
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", venv_dir])
        subprocess.run(["curl", "-sS", "https://bootstrap.pypa.io/get-pip.py", "-o", "/tmp/get-pip.py"])
        subprocess.run([os.path.join(venv_dir, "bin", "python3"), "/tmp/get-pip.py", "--quiet"])
    subprocess.run([os.path.join(venv_dir, "bin", "python3"), "-m", "pip", "install", "-q",
                    "-r", "requirements.txt", "--index-url", "https://pypi.org/simple/"],
                   capture_output=True)

    if args.category:
        categories = {args.category: CATEGORIES[args.category]}
    else:
        # Default: everything except E2E and deployed (they start servers)
        categories = {k: v for k, v in CATEGORIES.items() if k not in ("e2e", "deployed")}
        if args.all:
            categories = dict(CATEGORIES)

    print(f"\n{color('🧪 Sudoku Test Suite', BOLD)}")
    print(f"   Categories: {', '.join(categories.keys())}")
    print(f"   Fail fast: {args.fail_fast}")

    grand_total = 0
    grand_passed = 0
    grand_failed = 0
    grand_errors = 0
    grand_skipped = 0
    grand_time = 0

    for name, (label, modules) in categories.items():
        total, passed, failed, errors, skipped, elapsed = run_category(
            name, label, modules, fail_fast=args.fail_fast
        )
        grand_total += total
        grand_passed += passed
        grand_failed += failed
        grand_errors += errors
        grand_skipped += skipped
        grand_time += elapsed

        if args.fail_fast and (failed > 0 or errors > 0):
            print(f"\n{color('⏹', YELLOW)} Stopping due to --fail-fast")
            break

    # Grand summary
    print(f"\n{'═' * 60}")
    print(f"  {color('📊 Grand Summary', BOLD)}")
    print(f"{'═' * 60}")
    print(f"  Total:   {grand_total}")
    print(f"  {color('Passed:  ' + str(grand_passed), GREEN)}")
    if grand_failed:
        print(f"  {color('Failed:  ' + str(grand_failed), RED)}")
    if grand_errors:
        print(f"  {color('Errors:  ' + str(grand_errors), RED)}")
    if grand_skipped:
        print(f"  {color('Skipped: ' + str(grand_skipped), YELLOW)}")
    print(f"  Time:    {grand_time:.1f}s")

    icon = color("✅ ALL PASSED", GREEN) if grand_failed == 0 and grand_errors == 0 else color("❌ SOME FAILED", RED)
    print(f"\n  {icon}\n")

    return 1 if (grand_failed > 0 or grand_errors > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
