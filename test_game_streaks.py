"""
Tests for game streak tracking.
Tests consecutive completion streaks and consistency metrics.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameStreaks(unittest.TestCase):
    """Tests for game streak tracking."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, completed=True, elapsed=100, difficulty=30):
        self.client.post('/api/games', data=json.dumps({
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
        }), content_type='application/json')

    def test_streak_with_no_games(self):
        """No games means zero streak."""
        res = self.client.get('/api/streaks')
        data = res.get_json()
        self.assertEqual(data['current_streak'], 0)
        self.assertEqual(data['best_streak'], 0)

    def test_current_streak_all_completed(self):
        """All completed games should give a streak equal to count."""
        for _ in range(3):
            self._create_game(completed=True)
        res = self.client.get('/api/streaks')
        self.assertEqual(res.get_json()['current_streak'], 3)

    def test_streak_broken_by_incomplete(self):
        """An incomplete game should break the streak."""
        self._create_game(completed=True)
        self._create_game(completed=True)
        self._create_game(completed=False)  # Breaks streak
        self._create_game(completed=True)
        res = self.client.get('/api/streaks')
        data = res.get_json()
        self.assertEqual(data['current_streak'], 1)  # Only last game
        self.assertEqual(data['best_streak'], 2)  # Best was 2

    def test_best_streak(self):
        """Best streak should track the longest run."""
        for _ in range(5):
            self._create_game(completed=True)
        self._create_game(completed=False)
        for _ in range(3):
            self._create_game(completed=True)
        res = self.client.get('/api/streaks')
        data = res.get_json()
        self.assertEqual(data['best_streak'], 5)
        self.assertEqual(data['current_streak'], 3)

    def test_all_incomplete(self):
        """All incomplete games means zero streak."""
        for _ in range(3):
            self._create_game(completed=False)
        res = self.client.get('/api/streaks')
        data = res.get_json()
        self.assertEqual(data['current_streak'], 0)
        self.assertEqual(data['best_streak'], 0)

    def test_single_completed(self):
        """Single completed game gives streak of 1."""
        self._create_game(completed=True)
        res = self.client.get('/api/streaks')
        self.assertEqual(res.get_json()['current_streak'], 1)

    def test_streak_reset_after_incomplete(self):
        """Streak should reset to 0 after an incomplete game."""
        self._create_game(completed=True)
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/streaks')
        self.assertEqual(res.get_json()['current_streak'], 0)

    def test_streak_has_total_completions(self):
        """Streaks endpoint should include total completions."""
        for _ in range(3):
            self._create_game(completed=True)
        res = self.client.get('/api/streaks')
        self.assertEqual(res.get_json()['total_completions'], 3)

    def test_streak_has_completion_rate(self):
        """Streaks endpoint should include completion rate."""
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/streaks')
        self.assertEqual(res.get_json()['completion_rate'], 50.0)

    def test_streaks_endpoint_fields(self):
        """Streaks endpoint should have all required fields."""
        self._create_game(completed=True)
        res = self.client.get('/api/streaks')
        data = res.get_json()
        self.assertIn('current_streak', data)
        self.assertIn('best_streak', data)
        self.assertIn('total_completions', data)
        self.assertIn('total_games', data)
        self.assertIn('completion_rate', data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
