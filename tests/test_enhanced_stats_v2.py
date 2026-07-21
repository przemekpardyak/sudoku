"""
Tests for enhanced stats with completion_pct and avg_rating.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestEnhancedStatsV2(unittest.TestCase):
    """Tests for completion_pct and avg_rating in stats."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, completed=False, rating=None):
        state = {'difficulty': 30, 'elapsed': 100, 'completed': completed}
        if rating is not None:
            state['rating'] = rating
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_completion_pct_zero(self):
        """No games should give 0% completion."""
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['completion_pct'], 0)

    def test_completion_pct_fifty(self):
        """Half completed games should give 50%."""
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['completion_pct'], 50.0)

    def test_completion_pct_hundred(self):
        """All completed should give 100%."""
        self._create_game(completed=True)
        self._create_game(completed=True)
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['completion_pct'], 100.0)

    def test_avg_rating_zero(self):
        """No rated games should give avg_rating 0."""
        self._create_game(completed=True)
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['avg_rating'], 0)

    def test_avg_rating_calculated(self):
        """Average rating should be calculated from rated games."""
        self._create_game(completed=True, rating=3)
        self._create_game(completed=True, rating=5)
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['avg_rating'], 4.0)

    def test_avg_rating_ignores_unrated(self):
        """Unrated completed games should not affect avg_rating."""
        self._create_game(completed=True, rating=4)
        self._create_game(completed=True)  # no rating
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['avg_rating'], 4.0)

    def test_completion_pct_is_number(self):
        """completion_pct should be a number."""
        self._create_game(completed=True)
        res = self.client.get('/api/stats')
        self.assertIsInstance(res.get_json()['completion_pct'], (int, float))


if __name__ == '__main__':
    unittest.main(verbosity=2)
