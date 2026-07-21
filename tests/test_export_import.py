"""
Tests for game state export/import functionality.
Tests the /api/games/<id>/share and /api/games/import endpoints.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameExportImport(unittest.TestCase):
    """Tests for game export/import via shareable codes."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_export_game_returns_share_code(self):
        """Exporting a game should return a shareable code."""
        # Create a game
        state = {
            'puzzle': [[5, 0, 1], [0, 3, 0], [0, 0, 9]],
            'solution': [[5, 7, 1], [8, 3, 2], [4, 6, 9]],
            'board': [[5, 0, 1], [0, 3, 0], [0, 0, 9]],
            'given': [[True, False, True], [False, True, False], [False, False, True]],
            'notes': [[[False] * 9] * 3] * 3,
            'undoStack': [], 'redoStack': [],
            'mistakes': 0, 'elapsed': 0, 'difficulty': 40, 'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Export
        res = self.client.get(f'/api/games/{game_id}/export')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('share_code', data)
        self.assertTrue(len(data['share_code']) > 10)

    def test_import_game_from_share_code(self):
        """Importing a game from a share code should create a new game."""
        # Create and export
        state = {
            'puzzle': [[5, 0, 1], [0, 3, 0], [0, 0, 9]],
            'solution': [[5, 7, 1], [8, 3, 2], [4, 6, 9]],
            'board': [[5, 0, 1], [0, 3, 0], [0, 0, 9]],
            'difficulty': 40, 'mistakes': 2, 'elapsed': 100,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}/export')
        share_code = res.get_json()['share_code']

        # Import as a new game
        res = self.client.post('/api/games/import',
                              data=json.dumps({'share_code': share_code}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 201)
        new_game_id = res.get_json()['game_id']
        self.assertNotEqual(new_game_id, game_id)

        # Verify the imported game has the same state
        res = self.client.get(f'/api/games/{new_game_id}')
        game = res.get_json()
        self.assertEqual(game['puzzle'][0][0], 5)
        self.assertEqual(game['mistakes'], 2)
        self.assertEqual(game['elapsed'], 100)

    def test_export_nonexistent_game_returns_404(self):
        """Exporting a non-existent game should return 404."""
        res = self.client.get('/api/games/nonexistent/export')
        self.assertEqual(res.status_code, 404)

    def test_import_invalid_share_code_returns_400(self):
        """Importing an invalid share code should return 400."""
        res = self.client.post('/api/games/import',
                              data=json.dumps({'share_code': 'invalid-code'}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_export_import_roundtrip_preserves_state(self):
        """Export then import should preserve the full game state."""
        state = {
            'puzzle': [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                       [0, 3, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6,
            'solution': [[5, 7, 1, 2, 4, 3, 6, 8, 9],
                         [8, 3, 2, 5, 7, 9, 1, 4, 6],
                         [4, 6, 9, 1, 2, 8, 3, 5, 7]] + [[1] * 9] * 6,
            'board': [[5, 7, 1, 0, 0, 0, 0, 0, 0],
                      [0, 3, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6,
            'given': [[True, False, True] + [False] * 6,
                      [False, True, False] + [False] * 6,
                      [False, False, True] + [False] * 6] + [[False] * 9] * 6,
            'notes': [[[False] * 9 for _ in range(9)] for _ in range(9)],
            'undoStack': [], 'redoStack': [],
            'mistakes': 3, 'elapsed': 250, 'difficulty': 40, 'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Export
        res = self.client.get(f'/api/games/{game_id}/export')
        share_code = res.get_json()['share_code']

        # Import
        res = self.client.post('/api/games/import',
                              data=json.dumps({'share_code': share_code}),
                              content_type='application/json')
        new_id = res.get_json()['game_id']

        # Verify
        res = self.client.get(f'/api/games/{new_id}')
        game = res.get_json()
        self.assertEqual(game['puzzle'][0][0], 5)
        self.assertEqual(game['solution'][0][1], 7)
        self.assertEqual(game['board'][0][1], 7)  # filled cell
        self.assertEqual(game['mistakes'], 3)
        self.assertEqual(game['elapsed'], 250)
        self.assertEqual(game['difficulty'], 40)
        self.assertFalse(game['completed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
