#!/usr/bin/env python3
"""Watch for changes to sudoku.py, test_sudoku.py, app.py, and requirements.txt,
then automatically re-run the unit tests."""
import hashlib
import os
import subprocess
import sys
import time

WATCH_FILES = [
    "sudoku.py",
    "test_sudoku.py",
    "app.py",
    "requirements.txt",
]

VENV_PYTHON = os.path.join(os.path.dirname(__file__), "..", "venv", "bin", "python3")
VENV_PYTHON = os.path.abspath(VENV_PYTHON)
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable


def file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return None


def run_tests():
    print("\n🧪 Running unit tests...")
    print("=" * 60)
    result = subprocess.run(
        [VENV_PYTHON, "-m", "unittest", "test_sudoku", "-v"],
        capture_output=False,
    )
    print("=" * 60)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed (exit code {result.returncode})")
    return result.returncode


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")
    print(f"👀 Watching {len(WATCH_FILES)} files for changes...")
    print(f"   Files: {', '.join(WATCH_FILES)}")
    print(f"   Using: {VENV_PYTHON}")
    print("   Press Ctrl+C to stop.\n")

    # Run tests once at startup
    run_tests()

    hashes = {f: file_hash(f) for f in WATCH_FILES}

    while True:
        time.sleep(2)
        changed = []
        for f in WATCH_FILES:
            h = file_hash(f)
            if h != hashes[f]:
                changed.append(f)
                hashes[f] = h

        if changed:
            print(f"\n🔄 Change detected in: {', '.join(changed)}")
            # If requirements.txt changed, reinstall deps
            if "requirements.txt" in changed:
                print("📦 requirements.txt changed — reinstalling dependencies...")
                subprocess.run(
                    [VENV_PYTHON, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                    capture_output=True,
                )
            run_tests()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Stopped watching.")
