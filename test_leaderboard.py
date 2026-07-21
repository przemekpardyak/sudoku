"""
Tests for the leaderboard endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestLeaderboard(unittest.TestCase):
    """Tests for the leaderboard endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_completed_game(self, elapsed, difficulty=30, mistakes=0, rating=0):
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': True,
            'mistakes': mistakes,
            'rating': rating,
        }), content_type='application/json')
        return res.get_json()['game_id']

    def test_empty_leaderboard(self):
        """Leaderboard with no games should return empty list."""
        res = self.client.get('/api/leaderboard')
        data = res.get_json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['leaderboard']), 0)

    def test_leaderboard_sorted_by_time(self):
        """Leaderboard should be sorted by elapsed time (fastest first)."""
        self._create_completed_game(300)
        self._create_completed_game(100)
        self._create_completed_game(200)
        res = self.client.get('/api/leaderboard')
        times = [e['elapsed'] for e in res.get_json()['leaderboard']]
        self.assertEqual(times, [100, 200, 300])

    def test_leaderboard_default_limit(self):
        """Default limit should be 10."""
        for i in range(15):
            self._create_completed_game(50 + i * 10)
        res = self.client.get('/api/leaderboard')
        self.assertEqual(res.get_json()['count'], 10)

    def test_leaderboard_custom_limit(self):
        """Custom limit should work."""
        for i in range(20):
            self._create_completed_game(50 + i * 10)
        res = self.client.get('/api/leaderboard?limit=5')
        self.assertEqual(res.get_json()['count'], 5)

    def test_leaderboard_max_limit(self):
        """Limit should be capped at 50."""
        for i in range(60):
            self._create_completed_game(50 + i * 10)
        res = self.client.get('/api/leaderboard?limit=100')
        self.assertEqual(res.get_json()['count'], 50)

    def test_leaderboard_only_completed(self):
        """Leaderboard should only include completed games."""
        self._create_completed_game(100)
        # Create an incomplete game
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 50, 'completed': False,
        }), content_type='application/json')
        res = self.client.get('/api/leaderboard')
        self.assertEqual(res.get_json()['count'], 1)

    def test_leaderboard_filter_by_difficulty(self):
        """Leaderboard should filter by difficulty."""
        self._create_completed_game(100, difficulty=30)
        self._create_completed_game(200, difficulty=50)
        res = self.client.get('/api/leaderboard?difficulty=30')
        data = res.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['leaderboard'][0]['difficulty'], 30)

    def test_leaderboard_entries_have_fields(self):
        """Each leaderboard entry should have required fields."""
        self._create_completed_game(100, difficulty=30, mistakes=2, rating=4)
        res = self.client.get('/api/leaderboard')
        entry = res.get_json()['leaderboard'][0]
        self.assertIn('game_id', entry)
        self.assertIn('difficulty', entry)
        self.assertIn('elapsed', entry)
        self.assertIn('mistakes', entry)
        self.assertIn('hintsUsed', entry)
        self.assertIn('rating', entry)
        self.assertIn('created_at', entry)
        self.assertTrue(entry['completed'])

    def test_leaderboard_invalid_difficulty_ignored(self):
        """Invalid difficulty filter should be ignored (show all)."""
        self._create_completed_game(100, difficulty=30)
        self._create_completed_game(200, difficulty=50)
        res = self.client.get('/api/leaderboard?difficulty=abc')
        self.assertEqual(res.get_json()['count'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
