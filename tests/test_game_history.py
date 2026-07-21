"""
Tests for game history summary endpoint.
Tests the /api/history endpoint that returns a chronological summary
of all games with key metrics.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameHistory(unittest.TestCase):
    """Tests for game history summary endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, elapsed=100, completed=True, difficulty=30,
                     mistakes=0, rating=0):
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
            'mistakes': mistakes,
            'rating': rating,
        }), content_type='application/json')
        return res.get_json()['game_id']

    def test_empty_history(self):
        """Empty history should return empty list."""
        res = self.client.get('/api/history')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['history'], [])

    def test_history_has_entries(self):
        """History should have one entry per game."""
        self._create_game()
        self._create_game()
        res = self.client.get('/api/history')
        self.assertEqual(res.get_json()['count'], 2)

    def test_history_entries_have_fields(self):
        """Each history entry should have key fields."""
        game_id = self._create_game(elapsed=150, difficulty=30, mistakes=2)
        res = self.client.get('/api/history')
        entry = res.get_json()['history'][0]
        self.assertIn('game_id', entry)
        self.assertIn('difficulty', entry)
        self.assertIn('elapsed', entry)
        self.assertIn('completed', entry)
        self.assertIn('mistakes', entry)
        self.assertIn('created_at', entry)

    def test_history_sorted_by_created_at_desc(self):
        """History should be sorted newest first."""
        g1 = self._create_game()
        g2 = self._create_game()
        res = self.client.get('/api/history')
        history = res.get_json()['history']
        self.assertEqual(history[0]['game_id'], g2)
        self.assertEqual(history[1]['game_id'], g1)

    def test_history_with_limit(self):
        """History should respect limit parameter."""
        for _ in range(10):
            self._create_game()
        res = self.client.get('/api/history?limit=5')
        self.assertEqual(res.get_json()['count'], 5)

    def test_history_default_limit(self):
        """Default limit should be 20."""
        for _ in range(25):
            self._create_game()
        res = self.client.get('/api/history')
        self.assertEqual(res.get_json()['count'], 20)

    def test_history_filter_completed(self):
        """History should support filtering by completed status."""
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/history?completed=true')
        data = res.get_json()
        self.assertEqual(data['count'], 1)
        self.assertTrue(data['history'][0]['completed'])

    def test_history_filter_incomplete(self):
        """History should support filtering by incomplete status."""
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/history?completed=false')
        data = res.get_json()
        self.assertEqual(data['count'], 1)
        self.assertFalse(data['history'][0]['completed'])

    def test_history_filter_difficulty(self):
        """History should support filtering by difficulty."""
        self._create_game(difficulty=30)
        self._create_game(difficulty=50)
        res = self.client.get('/api/history?difficulty=30')
        data = res.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['history'][0]['difficulty'], 30)

    def test_history_has_total_count(self):
        """History should include total count before filtering."""
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/history?completed=true')
        data = res.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['total'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
