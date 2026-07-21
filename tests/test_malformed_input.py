"""
Tests for API robustness against malformed input.
Tests handling of invalid JSON, wrong content types, and malformed data.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestMalformedInput(unittest.TestCase):
    """Tests for API robustness against malformed input."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_create_with_invalid_json(self):
        """Creating a game with invalid JSON should return 400."""
        res = self.client.post('/api/games', data='not json',
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_create_with_wrong_content_type(self):
        """Creating a game with wrong content type should return 400."""
        res = self.client.post('/api/games', data='difficulty=30',
                               content_type='application/x-www-form-urlencoded')
        self.assertEqual(res.status_code, 400)

    def test_create_with_null_body(self):
        """Creating a game with null body should return 400."""
        res = self.client.post('/api/games', data=None,
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_create_with_empty_string(self):
        """Creating a game with empty string should return 400."""
        res = self.client.post('/api/games', data='',
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_update_with_invalid_json(self):
        """Updating with invalid JSON should return 400."""
        # Create a game first
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.put(f'/api/games/{game_id}', data='not json',
                              content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_solve_with_no_body(self):
        """Solve with no body should return 400."""
        res = self.client.post('/api/solve', data=None,
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_solve_with_missing_board(self):
        """Solve with missing board field should return 400."""
        res = self.client.post('/api/solve', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_validate_with_missing_board(self):
        """Validate with missing board field should return 400."""
        res = self.client.post('/api/validate', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_hint_with_missing_board(self):
        """Hint with missing board field should return 400."""
        res = self.client.post('/api/hint', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_analyze_with_missing_puzzle(self):
        """Analyze with missing puzzle field should return 400."""
        res = self.client.post('/api/analyze', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_rate_with_missing_rating(self):
        """Rate with missing rating field should return 400."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.put(f'/api/games/{game_id}/rate', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_import_with_missing_share_code(self):
        """Import with missing share_code should return 400."""
        res = self.client.post('/api/games/import', data=json.dumps({}),
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_archive_with_missing_field(self):
        """Archive with missing archived field should handle gracefully."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.put(f'/api/games/{game_id}/archive', data=json.dumps({}),
                               content_type='application/json')
        # Should not crash — either 400 or 200 with default
        self.assertIn(res.status_code, [200, 400])

    def test_new_game_with_non_numeric_difficulty(self):
        """New game with non-numeric difficulty should handle gracefully."""
        res = self.client.get('/api/new-game?difficulty=abc')
        # Should fall back to default or return error
        self.assertIn(res.status_code, [200, 400])
        if res.status_code == 200:
            self.assertIn('puzzle', res.get_json())

    def test_new_game_with_negative_difficulty(self):
        """New game with negative difficulty should handle gracefully."""
        res = self.client.get('/api/new-game?difficulty=-5')
        self.assertIn(res.status_code, [200, 400])
        if res.status_code == 200:
            self.assertIn('puzzle', res.get_json())

    def test_clone_nonexistent_game(self):
        """Cloning a nonexistent game should return 404."""
        res = self.client.post('/api/games/nonexistent/clone')
        self.assertEqual(res.status_code, 404)

    def test_export_nonexistent_game(self):
        """Exporting a nonexistent game should return 404."""
        res = self.client.get('/api/games/nonexistent/export')
        self.assertEqual(res.status_code, 404)

    def test_compare_with_swapped_params(self):
        """Compare with params in reverse order should work."""
        res1 = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100,
        }), content_type='application/json')
        res2 = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 200,
        }), content_type='application/json')
        id1 = res1.get_json()['game_id']
        id2 = res2.get_json()['game_id']

        res = self.client.get(f'/api/games/compare?a={id2}&b={id1}')
        self.assertEqual(res.status_code, 200)
        # Differences should be negative (b - a = id1 - id2 = -100)
        self.assertEqual(res.get_json()['differences']['elapsed'], -100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
