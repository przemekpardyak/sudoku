"""
Tests for storage boundary conditions.
Tests edge cases in the storage layer.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestStorageBoundaries(unittest.TestCase):
    """Tests for storage boundary conditions."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_empty_state(self):
        """Creating a game with empty state should work."""
        res = self.client.post('/api/games', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game.get('difficulty', 0), 0)
        self.assertEqual(game.get('elapsed', 0), 0)

    def test_large_state(self):
        """Creating a game with large state should work."""
        large_notes = 'A' * 10000
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
            'notes': large_notes,
            'tags': ['tag'] * 100,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 201)
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['notes'], large_notes)

    def test_update_nonexistent_returns_404(self):
        """Updating nonexistent game should return 404."""
        res = self.client.put('/api/games/nonexistent', data=json.dumps({
            'elapsed': 100,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_get_nonexistent_returns_404(self):
        """Getting nonexistent game should return 404."""
        res = self.client.get('/api/games/nonexistent')
        self.assertEqual(res.status_code, 404)

    def test_delete_nonexistent_returns_404(self):
        """Deleting nonexistent game should return 404."""
        res = self.client.delete('/api/games/nonexistent')
        self.assertEqual(res.status_code, 404)

    def test_partial_update_merges(self):
        """Partial update should merge with existing state."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
            'elapsed': 100,
            'mistakes': 5,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Update only elapsed
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'elapsed': 200,
        }), content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 200)
        self.assertEqual(game['difficulty'], 30)  # Preserved
        self.assertEqual(game['mistakes'], 5)  # Preserved

    def test_game_ids_are_unique(self):
        """Multiple games should have unique IDs."""
        ids = set()
        for _ in range(50):
            res = self.client.post('/api/games', data=json.dumps({
                'difficulty': 30,
            }), content_type='application/json')
            ids.add(res.get_json()['game_id'])
        self.assertEqual(len(ids), 50)

    def test_list_games_preserves_order(self):
        """Games list should be consistent across calls."""
        for _ in range(5):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30,
            }), content_type='application/json')

        res1 = self.client.get('/api/games')
        res2 = self.client.get('/api/games')
        ids1 = [g['game_id'] for g in res1.get_json()['games']]
        ids2 = [g['game_id'] for g in res2.get_json()['games']]
        self.assertEqual(ids1, ids2)

    def test_zero_difficulty_game(self):
        """Game with difficulty 0 should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 0,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['difficulty'], 0)

    def test_large_elapsed_time(self):
        """Large elapsed time should be stored correctly."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
            'elapsed': 999999,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['elapsed'], 999999)

    def test_negative_values_default(self):
        """Negative values should be stored as-is (validation is separate)."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
            'elapsed': -5,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}')
        # Storage doesn't validate, just stores
        self.assertEqual(res.get_json()['elapsed'], -5)

    def test_create_and_immediately_read(self):
        """Game should be immediately readable after creation."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
            'elapsed': 100,
            'completed': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['game_id'], game_id)
        self.assertEqual(game['elapsed'], 100)
        self.assertTrue(game['completed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
