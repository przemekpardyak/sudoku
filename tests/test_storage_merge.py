"""
Tests for storage layer merge behavior.
Verifies that partial updates correctly merge with existing game state.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestStorageMerge(unittest.TestCase):
    """Tests for storage merge behavior on partial updates."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_full_game(self):
        """Create a game with all fields populated."""
        state = {
            'puzzle': [[5, 3, 0, 0, 7, 0, 0, 0, 0]] + [[0]*9]*8,
            'solution': [[i+1 for i in range(9)]] + [[1]*9]*8,
            'board': [[5, 3, 0, 0, 7, 0, 0, 0, 0]] + [[0]*9]*8,
            'given': [[True, True, False, False, True, False, False, False, False]] + [[False]*9]*8,
            'notes': [[[False]*9 for _ in range(9)] for _ in range(9)],
            'undoStack': [],
            'redoStack': [],
            'difficulty': 40,
            'elapsed': 100,
            'mistakes': 2,
            'completed': False,
            'hintsUsed': 1,
            'tags': ['test'],
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_partial_update_preserves_other_fields(self):
        """Updating one field should not clear other fields."""
        game_id = self._create_full_game()
        # Update only elapsed
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 200}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 200)
        self.assertEqual(game['mistakes'], 2)  # unchanged
        self.assertEqual(game['difficulty'], 40)  # unchanged
        self.assertEqual(game['hintsUsed'], 1)  # unchanged

    def test_update_nested_field_preserves_top_level(self):
        """Updating a nested field (board) should preserve top-level fields."""
        game_id = self._create_full_game()
        new_board = [[5, 3, 4, 0, 7, 0, 0, 0, 0]] + [[0]*9]*8
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'board': new_board}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['board'], new_board)
        self.assertEqual(game['elapsed'], 100)  # unchanged
        self.assertEqual(game['puzzle'][0][:5], [5, 3, 0, 0, 7])  # unchanged

    def test_multiple_sequential_updates(self):
        """Multiple sequential updates should all apply correctly."""
        game_id = self._create_full_game()
        # Update 1: elapsed
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 150}),
                       content_type='application/json')
        # Update 2: mistakes
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'mistakes': 5}),
                       content_type='application/json')
        # Update 3: completed
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'completed': True}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 150)
        self.assertEqual(game['mistakes'], 5)
        self.assertTrue(game['completed'])

    def test_update_tags_preserves_state(self):
        """Updating tags should not affect game state."""
        game_id = self._create_full_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'tags': ['new', 'tags']}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(set(game['tags']), {'new', 'tags'})
        self.assertEqual(game['elapsed'], 100)
        self.assertEqual(game['difficulty'], 40)

    def test_empty_update_preserves_all(self):
        """An empty update should not change anything."""
        game_id = self._create_full_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 100)
        self.assertEqual(game['mistakes'], 2)
        self.assertEqual(game['difficulty'], 40)

    def test_update_timestamp_changes(self):
        """Updating a game should change its updated_at timestamp."""
        game_id = self._create_full_game()
        import time
        time.sleep(0.01)
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 999}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertNotEqual(game['created_at'], game['updated_at'])

    def test_update_does_not_corrupt_arrays(self):
        """Updating should not corrupt array fields."""
        game_id = self._create_full_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 50}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        # Arrays should still be valid
        self.assertEqual(len(game['puzzle']), 9)
        self.assertEqual(len(game['solution']), 9)
        self.assertEqual(len(game['notes']), 9)

    def test_concurrent_updates_last_wins(self):
        """Concurrent updates — last one wins for the same field."""
        game_id = self._create_full_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 300}),
                       content_type='application/json')
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 400}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
