"""
Tests for game session metrics and timing.
Tests session tracking, elapsed time, and timing-related fields.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestSessionMetrics(unittest.TestCase):
    """Tests for game session metrics and timing."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_session_start_stored(self):
        """Session start should be stored."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'session_start': '2026-07-21T10:00:00Z',
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game.get('session_start'), '2026-07-21T10:00:00Z')

    def test_session_end_stored(self):
        """Session end should be stored."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'session_end': '2026-07-21T10:05:00Z',
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game.get('session_end'), '2026-07-21T10:05:00Z')

    def test_elapsed_stored_correctly(self):
        """Elapsed time should be stored exactly."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 347,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['elapsed'], 347)

    def test_elapsed_updated(self):
        """Elapsed time should be updatable."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'elapsed': 250,
        }), content_type='application/json')
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['elapsed'], 250)

    def test_elapsed_zero_default(self):
        """Elapsed time should default to 0."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game.get('elapsed', 0), 0)

    def test_mistakes_increment(self):
        """Mistakes should be updatable."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'mistakes': 0,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        for i in range(1, 5):
            self.client.put(f'/api/games/{game_id}', data=json.dumps({
                'mistakes': i,
            }), content_type='application/json')
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['mistakes'], 4)

    def test_hints_used_increment(self):
        """Hints used should be updatable."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'hintsUsed': 0,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'hintsUsed': 3,
        }), content_type='application/json')
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['hintsUsed'], 3)

    def test_completion_time_in_stats(self):
        """Completed game time should appear in stats."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 120,
        }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['total_time'], 120)
        self.assertEqual(stats['avg_completion_time'], 120.0)

    def test_best_time_tracked(self):
        """Best time should be tracked per difficulty."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 50,
        }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['best_time'], 50)

    def test_stats_avg_time_multiple_games(self):
        """Average completion time should be correct for multiple games."""
        for t in [100, 200, 300]:
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': t,
            }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['avg_completion_time'], 200.0)

    def test_paused_state_persisted(self):
        """Paused state should be persisted."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'paused': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertTrue(game.get('paused', False))

    def test_game_mode_stored(self):
        """Game mode should be stored."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'mode': 'notes',
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game.get('mode'), 'notes')


if __name__ == '__main__':
    unittest.main(verbosity=2)
