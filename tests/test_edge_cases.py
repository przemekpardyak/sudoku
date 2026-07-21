"""
Tests for game state edge cases and error handling.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameStateEdgeCases(unittest.TestCase):
    """Tests for edge cases in game state handling."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_empty_state(self):
        """An empty state dict should be accepted and stored."""
        res = self.client.post('/api/games', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 200)

    def test_extra_fields_preserved(self):
        """Extra fields in state should be preserved."""
        state = {'difficulty': 40, 'custom_field': 'hello', 'extra_num': 42}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game.get('custom_field'), 'hello')
        self.assertEqual(game.get('extra_num'), 42)

    def test_null_values_handled(self):
        """Null values in state should be handled gracefully."""
        state = {'difficulty': None, 'elapsed': None, 'completed': None}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_large_elapsed_time(self):
        """Large elapsed times should be stored correctly."""
        state = {'difficulty': 40, 'elapsed': 999999, 'completed': True}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 999999)

    def test_negative_mistakes(self):
        """Negative mistakes should be stored (no validation on API level)."""
        state = {'difficulty': 40, 'mistakes': -1}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['mistakes'], -1)

    def test_partial_update_preserves_other_fields(self):
        """A partial PUT should preserve fields not included in the update."""
        state = {'difficulty': 40, 'elapsed': 100, 'mistakes': 5, 'completed': False}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Partial update — only change elapsed
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 200}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 200)
        self.assertEqual(game['mistakes'], 5)
        self.assertFalse(game['completed'])

    def test_multiple_games_same_difficulty(self):
        """Multiple games with the same difficulty should all be listed."""
        for i in range(5):
            state = {'difficulty': 40, 'elapsed': i * 10}
            self.client.post('/api/games', data=json.dumps(state),
                             content_type='application/json')

        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertEqual(len(games), 5)

    def test_game_id_is_unique(self):
        """Each game should have a unique ID."""
        ids = set()
        for _ in range(10):
            res = self.client.post('/api/games', data=json.dumps({'difficulty': 40}),
                                   content_type='application/json')
            ids.add(res.get_json()['game_id'])
        self.assertEqual(len(ids), 10)

    def test_delete_already_deleted_game(self):
        """Deleting a non-existent game should return 404."""
        res = self.client.delete('/api/games/nonexistent-id')
        self.assertEqual(res.status_code, 404)

    def test_get_nonexistent_game(self):
        """Getting a non-existent game should return 404."""
        res = self.client.get('/api/games/nonexistent-id')
        self.assertEqual(res.status_code, 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
