"""
Tests for best-time tracking per difficulty level.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestBestTimes(unittest.TestCase):
    """Tests for best-time tracking."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_no_best_times_initially(self):
        """GET /api/best-times should return empty when no games completed."""
        res = self.client.get('/api/best-times')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data, {})

    def test_best_time_after_completing_game(self):
        """Completing a game should record the best time for that difficulty."""
        # Create and complete a game
        state = {
            'puzzle': [[5, 0], [0, 3]],
            'solution': [[5, 7], [8, 3]],
            'board': [[5, 7], [8, 3]],
            'difficulty': 30,
            'mistakes': 0,
            'elapsed': 120,
            'completed': True,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Check best times
        res = self.client.get('/api/best-times')
        data = res.get_json()
        self.assertIn('30', data)
        self.assertEqual(data['30'], 120)

    def test_best_time_updates_with_better_time(self):
        """A faster completion should update the best time."""
        # First game: 120s
        state1 = {'difficulty': 30, 'mistakes': 0, 'elapsed': 120, 'completed': True}
        self.client.post('/api/games', data=json.dumps(state1),
                        content_type='application/json')

        # Second game: 90s (faster)
        state2 = {'difficulty': 30, 'mistakes': 0, 'elapsed': 90, 'completed': True}
        self.client.post('/api/games', data=json.dumps(state2),
                        content_type='application/json')

        res = self.client.get('/api/best-times')
        data = res.get_json()
        self.assertEqual(data.get('30'), 90)

    def test_best_time_does_not_update_with_slower_time(self):
        """A slower completion should not update the best time."""
        # First game: 90s
        state1 = {'difficulty': 40, 'mistakes': 0, 'elapsed': 90, 'completed': True}
        self.client.post('/api/games', data=json.dumps(state1),
                        content_type='application/json')

        # Second game: 120s (slower)
        state2 = {'difficulty': 40, 'mistakes': 0, 'elapsed': 120, 'completed': True}
        self.client.post('/api/games', data=json.dumps(state2),
                        content_type='application/json')

        res = self.client.get('/api/best-times')
        data = res.get_json()
        self.assertEqual(data.get('40'), 90)

    def test_best_times_separate_per_difficulty(self):
        """Each difficulty should track its own best time."""
        for diff, t in [(30, 100), (40, 200), (50, 300)]:
            state = {'difficulty': diff, 'mistakes': 0, 'elapsed': t, 'completed': True}
            self.client.post('/api/games', data=json.dumps(state),
                            content_type='application/json')

        res = self.client.get('/api/best-times')
        data = res.get_json()
        self.assertEqual(data.get('30'), 100)
        self.assertEqual(data.get('40'), 200)
        self.assertEqual(data.get('50'), 300)

    def test_incomplete_games_not_counted(self):
        """Incomplete games should not affect best times."""
        state = {'difficulty': 30, 'mistakes': 0, 'elapsed': 60, 'completed': False}
        self.client.post('/api/games', data=json.dumps(state),
                        content_type='application/json')

        res = self.client.get('/api/best-times')
        data = res.get_json()
        self.assertNotIn('30', data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
