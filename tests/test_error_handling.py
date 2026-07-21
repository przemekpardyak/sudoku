"""
Tests for API error handling and edge cases.
Tests malformed inputs, invalid data, and error responses.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestErrorHandling(unittest.TestCase):
    """Tests for API error handling."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_create_game_without_body(self):
        """Creating a game without a body should return 400."""
        res = self.client.post('/api/games', content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_create_game_with_invalid_json(self):
        """Creating a game with invalid JSON should not crash."""
        res = self.client.post('/api/games', data='not json',
                             content_type='application/json')
        # Flask's force=True will try to parse, might 400 or create empty
        self.assertIn(res.status_code, [201, 400])

    def test_get_nonexistent_game(self):
        """Getting a nonexistent game should return 404."""
        res = self.client.get('/api/games/nonexistent-id')
        self.assertEqual(res.status_code, 404)
        self.assertIn('error', res.get_json())

    def test_update_nonexistent_game(self):
        """Updating a nonexistent game should return 404."""
        res = self.client.put('/api/games/nonexistent-id',
                            data=json.dumps({'elapsed': 100}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_delete_nonexistent_game(self):
        """Deleting a nonexistent game should return 404."""
        res = self.client.delete('/api/games/nonexistent-id')
        self.assertEqual(res.status_code, 404)

    def test_new_game_invalid_difficulty(self):
        """New game with invalid difficulty should still work (defaults)."""
        res = self.client.get('/api/new-game?difficulty=abc')
        # Flask will handle the conversion error
        self.assertIn(res.status_code, [200, 400])

    def test_new_game_negative_difficulty(self):
        """New game with negative difficulty should handle gracefully."""
        res = self.client.get('/api/new-game?difficulty=-5')
        self.assertIn(res.status_code, [200, 400])

    def test_new_game_extreme_difficulty(self):
        """New game with extreme difficulty should still work."""
        res = self.client.get('/api/new-game?difficulty=100')
        self.assertIn(res.status_code, [200, 400])

    def test_solve_with_non_array(self):
        """Solve with non-array input should return 400."""
        res = self.client.post('/api/solve',
                             data=json.dumps({'board': 'not an array'}),
                             content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_solve_with_wrong_dimensions(self):
        """Solve with wrong dimensions should return 400."""
        res = self.client.post('/api/solve',
                             data=json.dumps({'board': [[1, 2], [3, 4]]}),
                             content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_hint_with_non_array(self):
        """Hint with non-array input should return 400."""
        res = self.client.post('/api/hint',
                             data=json.dumps({'board': 42}),
                             content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_validate_with_non_array(self):
        """Validate with non-array input should return 400."""
        res = self.client.post('/api/validate',
                             data=json.dumps({'board': 'invalid'}),
                             content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_import_invalid_code(self):
        """Importing an invalid share code should return 400."""
        res = self.client.post('/api/games/import',
                             data=json.dumps({'share_code': 'invalid-base64!!!'}),
                             content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_import_missing_code(self):
        """Importing without share_code should return 400."""
        res = self.client.post('/api/games/import',
                             data=json.dumps({}),
                             content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_archive_nonexistent_game(self):
        """Archiving a nonexistent game should return 404."""
        res = self.client.put('/api/games/nonexistent/archive',
                            data=json.dumps({'archived': True}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_clone_nonexistent_game(self):
        """Cloning a nonexistent game should return 404."""
        res = self.client.post('/api/games/nonexistent/clone')
        self.assertEqual(res.status_code, 404)

    def test_rate_nonexistent_game(self):
        """Rating a nonexistent game should return 404."""
        res = self.client.put('/api/games/nonexistent/rate',
                            data=json.dumps({'rating': 5}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_export_nonexistent_game(self):
        """Exporting a nonexistent game should return 404."""
        res = self.client.get('/api/games/nonexistent/export')
        self.assertEqual(res.status_code, 404)

    def test_games_list_with_negative_limit(self):
        """List with negative limit should handle gracefully."""
        res = self.client.get('/api/games?limit=-1')
        self.assertEqual(res.status_code, 200)

    def test_games_list_with_huge_limit(self):
        """List with huge limit should handle gracefully."""
        res = self.client.get('/api/games?limit=999999')
        self.assertEqual(res.status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
