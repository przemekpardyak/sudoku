"""
Tests for hint counter tracking.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestHintCounter(unittest.TestCase):
    """Tests for hint usage tracking in game state."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_hints_used_default_zero(self):
        """A game without hintsUsed should default to 0."""
        state = {'difficulty': 40, 'elapsed': 0}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game.get('hintsUsed', 0), 0)

    def test_hints_used_persisted(self):
        """hintsUsed should be persisted in game state."""
        state = {'difficulty': 40, 'elapsed': 50, 'hintsUsed': 3}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['hintsUsed'], 3)

    def test_hints_used_updated(self):
        """hintsUsed should be updatable via PUT."""
        state = {'difficulty': 40, 'elapsed': 0, 'hintsUsed': 1}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'hintsUsed': 5, 'difficulty': 40, 'elapsed': 100}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['hintsUsed'], 5)

    def test_stats_include_hints(self):
        """Stats should include total hints used."""
        state1 = {'difficulty': 40, 'elapsed': 0, 'hintsUsed': 3}
        state2 = {'difficulty': 40, 'elapsed': 0, 'hintsUsed': 2}
        self.client.post('/api/games', data=json.dumps(state1),
                         content_type='application/json')
        self.client.post('/api/games', data=json.dumps(state2),
                         content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats.get('total_hints', 0), 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
