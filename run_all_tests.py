#!/usr/bin/env python3
"""
run_all_tests.py — Discover and run all test_*.py files in the project root.

Usage:
    python3 run_all_tests.py              # run all tests
    python3 run_all_tests.py --watch      # re-run on file changes
    python3 run_all_tests.py --fail-fast  # stop on first failure
    python3 run_all_tests.py --module test_storage  # run specific module

Exit codes:
    0 = all passed
    1 = some failed
    2 = setup error
"""
import os
import sys
import time
import unittest

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


def main():
    args = sys.argv[1:]
    fail_fast = False
    watch = False
    specific_module = None

    for arg in args:
        if arg == "--fail-fast":
            fail_fast = True
        elif arg == "--watch":
            watch = True
        elif arg == "--module":
            pass  # next arg is the module name
        elif args and args[args.index(arg) - 1] == "--module":
            specific_module = arg

    # Ensure venv is usable
    venv_python = os.path.join(PROJECT_ROOT, "venv", "bin", "python3")
    if not os.path.exists(venv_python):
        print("⚠️  venv not found. Run: ./scripts/run_tests.sh first to set up.")
        sys.exit(2)

    if watch:
        run_watch_loop(fail_fast)
    else:
        run_once(fail_fast, specific_module)


def run_once(fail_fast=False, module=None):
    """Discover and run all tests once."""
    start = time.time()

    if module:
        suite = unittest.TestLoader().loadTestsFromName(module)
        print(f"🧪 Running tests from: {module}")
    else:
        # Auto-discover all test_*.py files
        suite = unittest.TestLoader().discover(
            PROJECT_ROOT, pattern="test_*.py"
        )
        print("🧪 Running all tests (auto-discovered)")

    print("─" * 56)
    print()

    runner = unittest.TextTestRunner(
        verbosity=2,
        failfast=fail_fast,
    )
    result = runner.run(suite)

    elapsed = time.time() - start
    print()
    print("─" * 56)

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - errors - skipped

    if result.wasSuccessful():
        print(f"✅ All tests passed ({elapsed:.1f}s)")
        print(f"   {passed} passed, {skipped} skipped, {total} total")
        sys.exit(0)
    else:
        print(f"❌ Tests failed ({elapsed:.1f}s)")
        print(f"   {passed} passed, {failures} failed, {errors} errors, {skipped} skipped, {total} total")
        sys.exit(1)


def run_watch_loop(fail_fast):
    """Re-run tests on file changes."""
    print("👀 Watch mode: re-running tests on file changes (Ctrl+C to stop)")
    print()

    # Use inotifywait if available
    import subprocess
    import shutil

    inotifywait = shutil.which("inotifywait")
    watch_files = [
        "sudoku.py", "test_sudoku.py",
        "app.py", "test_app.py",
        "storage.py", "test_storage.py",
        "requirements.txt",
    ]
    # Only watch files that exist
    watch_files = [f for f in watch_files if os.path.exists(f)]

    while True:
        os.system("clear" if os.name != "nt" else "cls")
        try:
            run_once(fail_fast)
        except SystemExit:
            pass  # we don't want to exit the loop

        print()
        print("⏳ Waiting for file changes... (Ctrl+C to stop)")

        if inotifywait:
            cmd = [inotifywait, "-q", "-e", "modify", "-e", "create", "-e", "delete"] + watch_files
            try:
                subprocess.run(cmd, timeout=3600, capture_output=True)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                break
        else:
            # Fallback: poll every 2 seconds
            mtimes = {f: os.path.getmtime(f) for f in watch_files if os.path.exists(f)}
            try:
                while True:
                    time.sleep(2)
                    for f in watch_files:
                        if os.path.exists(f):
                            current_mtime = os.path.getmtime(f)
                            if current_mtime != mtimes.get(f):
                                mtimes[f] = current_mtime
                                break
                    else:
                        continue
                    break
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    main()
