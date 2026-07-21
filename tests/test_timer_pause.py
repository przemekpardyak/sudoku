"""
Tests for the game timer pause/resume functionality.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestTimerPause(unittest.TestCase):
    """Tests for timer pause/resume via the API."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_save_with_paused_state(self):
        """Saving a game with a 'paused' field should persist it."""
        state = {
            'difficulty': 40,
            'elapsed': 100,
            'paused': True,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertTrue(game.get('paused', False))

    def test_unpause_on_resume(self):
        """When resuming, paused should be set to False."""
        # Create paused game
        state = {'difficulty': 40, 'elapsed': 100, 'paused': True}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Unpause
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'paused': False}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertFalse(game.get('paused', False))

    def test_elapsed_time_preserved_on_pause(self):
        """Elapsed time should be preserved when pausing."""
        state = {'difficulty': 40, 'elapsed': 250, 'paused': True}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 250)

    def test_game_without_paused_field(self):
        """Games without a 'paused' field should work normally."""
        state = {'difficulty': 40, 'elapsed': 50}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        # paused should default to False or not be present
        self.assertFalse(game.get('paused', False))


if __name__ == '__main__':
    unittest.main(verbosity=2)
