"""
Tests for the difficulty recommendation endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestRecommendDifficulty(unittest.TestCase):
    """Tests for the difficulty recommendation endpoint."""

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

    def test_no_games_recommends_medium(self):
        """No games should recommend medium (30)."""
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertEqual(data['recommended_difficulty'], 30)
        self.assertIn('reasoning', data)

    def test_no_completed_games_recommends_medium(self):
        """Only incomplete games should still recommend medium."""
        self._create_game(completed=False)
        res = self.client.get('/api/recommend-difficulty')
        self.assertEqual(res.get_json()['recommended_difficulty'], 30)

    def test_fast_completion_recommends_harder(self):
        """Fast completion (<60s) should recommend harder difficulty."""
        self._create_game(elapsed=40, difficulty=30)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertGreater(data['recommended_difficulty'], 30)

    def test_slow_completion_recommends_easier(self):
        """Slow completion (>300s avg) should recommend easier."""
        for _ in range(5):
            self._create_game(elapsed=400, difficulty=40)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertLess(data['recommended_difficulty'], 40)

    def test_steady_performance_keeps_same(self):
        """Normal performance should keep same difficulty."""
        self._create_game(elapsed=120, difficulty=30)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertEqual(data['recommended_difficulty'], 30)

    def test_recommendation_has_reasoning(self):
        """Recommendation should include reasoning text."""
        self._create_game(elapsed=100, difficulty=30)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertIn('reasoning', data)
        self.assertIsInstance(data['reasoning'], str)
        self.assertGreater(len(data['reasoning']), 10)

    def test_recommendation_has_stats(self):
        """Recommendation should include current stats."""
        self._create_game(elapsed=50, difficulty=30)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertIn('current_difficulty', data)
        self.assertIn('best_time', data)
        self.assertIn('avg_time', data)
        self.assertIn('completed_at_level', data)

    def test_hard_difficulty_capped(self):
        """Difficulty recommendation should cap at 58 (expert)."""
        for _ in range(3):
            self._create_game(elapsed=20, difficulty=50)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertLessEqual(data['recommended_difficulty'], 58)

    def test_easy_difficulty_floored(self):
        """Difficulty recommendation should floor at 20 (easy)."""
        for _ in range(5):
            self._create_game(elapsed=600, difficulty=20)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertGreaterEqual(data['recommended_difficulty'], 20)

    def test_uses_most_played_difficulty(self):
        """Should base recommendation on most played difficulty."""
        for _ in range(5):
            self._create_game(elapsed=100, difficulty=30)
        for _ in range(2):
            self._create_game(elapsed=100, difficulty=50)
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertEqual(data['current_difficulty'], 30)


if __name__ == '__main__':
    unittest.main(verbosity=2)
