"""
Smoke tests for the deployed Cloud Run service.
Tests the live service at https://sudoku-d5mqgioeaa-uc.a.run.app
"""
import json
import unittest
import urllib.request
import urllib.error

BASE_URL = "https://sudoku-d5mqgioeaa-uc.a.run.app"


def _get(path):
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.read else {}
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, json.loads(body) if body else {}
    except Exception as e:
        return 0, {"error": str(e)}


@unittest.skipUnless(False, "Set to True to run against live service")
class TestDeployedService(unittest.TestCase):
    """Smoke tests for the deployed Cloud Run service."""

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
