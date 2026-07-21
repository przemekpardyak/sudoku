"""
Tests for concurrent and rapid-fire operations on the storage layer.
Tests that the system handles rapid saves, multiple creates, and
edge cases gracefully.
"""
import json
import unittest
import threading
import time
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestConcurrentOperations(unittest.TestCase):
    """Test concurrent and rapid-fire operations."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_rapid_updates_to_same_game(self):
        """Rapidly updating the same game should not corrupt data."""
        res = self.client.post('/api/games',
                               data=json.dumps({'difficulty': 40, 'elapsed': 0}),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Rapidly update 20 times
        for i in range(20):
            self.client.put(f'/api/games/{game_id}',
                           data=json.dumps({'elapsed': i * 5, 'mistakes': i}),
                           content_type='application/json')

        # Final state should have the last values
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 95)
        self.assertEqual(game['mistakes'], 19)

    def test_create_multiple_games_rapidly(self):
        """Creating multiple games in quick succession should work."""
        ids = []
        for i in range(10):
            res = self.client.post('/api/games',
                                  data=json.dumps({'difficulty': 30 + i, 'elapsed': i}),
                                  content_type='application/json')
            ids.append(res.get_json()['game_id'])

        # All IDs should be unique
        self.assertEqual(len(ids), len(set(ids)))

        # All should be retrievable
        for i, game_id in enumerate(ids):
            res = self.client.get(f'/api/games/{game_id}')
            self.assertEqual(res.status_code, 200)

    def test_update_then_delete_then_get(self):
        """Update, then delete, then get should return 404."""
        res = self.client.post('/api/games',
                              data=json.dumps({'difficulty': 40}),
                              content_type='application/json')
        game_id = res.get_json()['game_id']

        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 100}),
                       content_type='application/json')
        self.client.delete(f'/api/games/{game_id}')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 404)

    def test_list_after_all_deleted(self):
        """List should be empty after all games are deleted."""
        for _ in range(5):
            self.client.post('/api/games',
                            data=json.dumps({'difficulty': 40}),
                            content_type='application/json')
        self.client.delete('/api/games')
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 0)

    def test_large_game_state(self):
        """Test with a full game state with large undo/redo stacks."""
        # Build a large undo stack (50 entries)
        undo = []
        for i in range(50):
            board = [[0] * 9 for _ in range(9)]
            board[0][0] = i % 9 + 1
            given = [[False] * 9 for _ in range(9)]
            given[0][0] = True
            undo.append({
                'board': board,
                'notes': [[[False] * 9 for _ in range(9)] for _ in range(9)],
                'given': given,
                'mistakes': i,
            })

        state = {
            'puzzle': [[0] * 9] * 9,
            'solution': [[1] * 9] * 9,
            'board': [[5] * 9] * 9,
            'given': [[True] * 9] * 9,
            'notes': [[[False] * 9] * 9] * 9,
            'undoStack': undo,
            'redoStack': undo[:10],
            'mistakes': 50,
            'elapsed': 9999,
            'difficulty': 58,
            'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(len(game['undoStack']), 50)
        self.assertEqual(len(game['redoStack']), 10)
        self.assertEqual(game['mistakes'], 50)
        self.assertEqual(game['elapsed'], 9999)

    def test_overwrite_existing_game(self):
        """Saving to an existing game should overwrite its state."""
        res = self.client.post('/api/games',
                              data=json.dumps({'difficulty': 40, 'mistakes': 5, 'elapsed': 100}),
                              content_type='application/json')
        game_id = res.get_json()['game_id']

        # Overwrite with completely different state
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'mistakes': 0, 'elapsed': 50}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['mistakes'], 0)
        self.assertEqual(game['elapsed'], 50)

    def test_game_ids_are_valid_uuids(self):
        """Generated game IDs should be valid UUIDs."""
        import uuid as uuid_module
        for _ in range(5):
            res = self.client.post('/api/games',
                                  data=json.dumps({'difficulty': 40}),
                                  content_type='application/json')
            game_id = res.get_json()['game_id']
            # Should parse as a valid UUID
            parsed = uuid_module.UUID(game_id)
            self.assertEqual(str(parsed), game_id)


class TestStorageResilience(unittest.TestCase):
    """Test storage resilience and error recovery."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_save_with_null_values(self):
        """Saving with null/None values should not crash."""
        state = {
            'difficulty': 40,
            'puzzle': None,
            'board': None,
            'solution': None,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_save_with_extra_fields(self):
        """Extra unknown fields should be preserved (schemaless storage)."""
        state = {
            'difficulty': 40,
            'custom_field': 'hello',
            'extra_data': {'nested': 'value'},
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['custom_field'], 'hello')
        self.assertEqual(game['extra_data']['nested'], 'value')

    def test_save_with_large_numbers(self):
        """Large numbers should be handled correctly."""
        state = {
            'difficulty': 40,
            'elapsed': 999999,
            'mistakes': 999,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['elapsed'], 999999)
        self.assertEqual(game['mistakes'], 999)


if __name__ == '__main__':
    unittest.main(verbosity=2)
