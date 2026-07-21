"""
Smoke tests for the Sudoku service over HTTP.

By default, these tests auto-start the Flask app on localhost:5000.
To test against the deployed Cloud Run service instead:

    1. Start the proxy:
       gcloud run services proxy sudoku --region=us-central1 --project=ppardyak-cad --port=8080

    2. Run with env var:
       SUDOKU_TEST_URL=http://localhost:8080 venv/bin/python3 -m unittest tests.test_deployed_service -v

Or with a bearer token directly:
       SUDOKU_TEST_URL=https://sudoku-d5mqgioeaa-uc.a.run.app \
         SUDOKU_TOKEN=$(gcloud auth print-identity-token) \
         venv/bin/python3 -m unittest tests.test_deployed_service -v
"""
import json
import os
import unittest
import urllib.request
import urllib.error
import subprocess
import time
import signal

BASE_URL = os.environ.get("SUDOKU_TEST_URL", "http://localhost:5000")
TOKEN = os.environ.get("SUDOKU_TOKEN", "")


def _wait_for_app(timeout=30):
    """Wait for the service to be reachable."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{BASE_URL}/")
            if TOKEN:
                req.add_header("Authorization", f"Bearer {TOKEN}")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def _get(path):
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}")
        if TOKEN:
            req.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            try:
                return resp.status, json.loads(body)
            except (json.JSONDecodeError, ValueError):
                return resp.status, {"raw": body.decode("utf-8", errors="replace")}
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body) if body else {}
        except (json.JSONDecodeError, ValueError):
            return e.code, {"raw": body.decode("utf-8", errors="replace")}
    except Exception as e:
        return 0, {"error": str(e)}


def _post(path, data):
    try:
        req = urllib.request.Request(
            f"{BASE_URL}{path}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        if TOKEN:
            req.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, json.loads(body) if body else {}
    except Exception as e:
        return 0, {"error": str(e)}


class TestDeployedService(unittest.TestCase):
    """Smoke tests for the Sudoku service over HTTP."""

    @classmethod
    def setUpClass(cls):
        """Auto-start Flask app if pointing at localhost and not running."""
        cls._app_process = None
        if "localhost" in BASE_URL and not _wait_for_app(timeout=2):
            cls._app_process = subprocess.Popen(
                ["venv/bin/python3", "app.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            if not _wait_for_app(timeout=15):
                raise RuntimeError("Flask app did not start in time")

    @classmethod
    def tearDownClass(cls):
        if cls._app_process:
            os.killpg(os.getpgid(cls._app_process.pid), signal.SIGTERM)

    def test_root_page(self):
        """Root page should return HTML."""
        status, _ = _get("/")
        self.assertEqual(status, 200)

    def test_new_game(self):
        """New game endpoint should work."""
        status, data = _get("/api/new-game?difficulty=30")
        self.assertEqual(status, 200)
        self.assertIn("puzzle", data)

    def test_daily_puzzle(self):
        """Daily puzzle endpoint should work."""
        status, data = _get("/api/daily-puzzle")
        self.assertEqual(status, 200)
        self.assertIn("puzzle", data)

    def test_weekly_puzzle(self):
        """Weekly puzzle endpoint should work."""
        status, data = _get("/api/weekly-puzzle")
        self.assertEqual(status, 200)
        self.assertIn("puzzle", data)

    def test_stats(self):
        """Stats endpoint should work."""
        status, data = _get("/api/stats")
        self.assertEqual(status, 200)
        self.assertIn("total_games", data)

    def test_leaderboard(self):
        """Leaderboard endpoint should work."""
        status, data = _get("/api/leaderboard")
        self.assertEqual(status, 200)
        self.assertIn("leaderboard", data)

    def test_streaks(self):
        """Streaks endpoint should work."""
        status, data = _get("/api/streaks")
        self.assertEqual(status, 200)
        self.assertIn("current_streak", data)

    def test_history(self):
        """History endpoint should work."""
        status, data = _get("/api/history")
        self.assertEqual(status, 200)
        self.assertIn("history", data)

    def test_recommend_difficulty(self):
        """Recommend difficulty endpoint should work."""
        status, data = _get("/api/recommend-difficulty")
        self.assertEqual(status, 200)
        self.assertIn("recommended_difficulty", data)

    def test_stats_export(self):
        """Stats export endpoint should work."""
        status, data = _get("/api/stats/export")
        self.assertEqual(status, 200)
        self.assertIn("summary", data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
