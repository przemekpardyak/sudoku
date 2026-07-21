"""
Tests for API endpoint consistency and response format validation.
Ensures all endpoints return consistent JSON structure.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestAPIConsistency(unittest.TestCase):
    """Tests for API response format consistency."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_all_endpoints_return_json(self):
        """All API endpoints should return JSON content type."""
        endpoints = [
            ('/api/new-game', 'GET'),
            ('/api/daily-puzzle', 'GET'),
            ('/api/weekly-puzzle', 'GET'),
            ('/api/games', 'GET'),
            ('/api/best-times', 'GET'),
            ('/api/stats', 'GET'),
        ]
        for path, method in endpoints:
            res = self.client.open(path, method=method)
            self.assertEqual(res.content_type, 'application/json',
                           f"{path} {method} did not return JSON")

    def test_error_responses_have_error_field(self):
        """Error responses should have an 'error' field."""
        res = self.client.get('/api/games/nonexistent-id')
        self.assertEqual(res.status_code, 404)
        self.assertIn('error', res.get_json())

    def test_success_responses_have_ok_field(self):
        """Success responses for mutations should have 'ok' field."""
        # Create game
        res = self.client.post('/api/games', data=json.dumps({'difficulty': 30}),
                             content_type='application/json')
        game_id = res.get_json()['game_id']

        # Update game
        res = self.client.put(f'/api/games/{game_id}',
                            data=json.dumps({'elapsed': 100}),
                            content_type='application/json')
        self.assertTrue(res.get_json()['ok'])

        # Delete game
        res = self.client.delete(f'/api/games/{game_id}')
        self.assertTrue(res.get_json()['ok'])

    def test_game_id_format(self):
        """Game IDs should be non-empty strings."""
        res = self.client.post('/api/games', data=json.dumps({'difficulty': 30}),
                             content_type='application/json')
        game_id = res.get_json()['game_id']
        self.assertIsInstance(game_id, str)
        self.assertGreater(len(game_id), 0)

    def test_list_games_returns_array(self):
        """List games should return a 'games' array."""
        res = self.client.get('/api/games')
        data = res.get_json()
        self.assertIn('games', data)
        self.assertIsInstance(data['games'], list)

    def test_stats_returns_dict(self):
        """Stats should return a dictionary."""
        res = self.client.get('/api/stats')
        self.assertIsInstance(res.get_json(), dict)

    def test_new_game_returns_puzzle_and_solution(self):
        """New game should return puzzle and solution."""
        res = self.client.get('/api/new-game?difficulty=30')
        data = res.get_json()
        self.assertIn('puzzle', data)
        self.assertIn('solution', data)

    def test_best_times_returns_dict(self):
        """Best times should return a dictionary."""
        res = self.client.get('/api/best-times')
        self.assertIsInstance(res.get_json(), dict)

    def test_solve_returns_solved_board(self):
        """Solve should return a 'solved' field."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/solve',
                             data=json.dumps({'board': puzzle}),
                             content_type='application/json')
        self.assertIn('solved', res.get_json())

    def test_hint_returns_coordinates(self):
        """Hint should return row, col, value."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint',
                             data=json.dumps({'board': puzzle}),
                             content_type='application/json')
        data = res.get_json()
        self.assertIn('row', data)
        self.assertIn('col', data)
        self.assertIn('value', data)

    def test_validate_returns_valid_field(self):
        """Validate should return a 'valid' field."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/validate',
                             data=json.dumps({'board': puzzle}),
                             content_type='application/json')
        self.assertIn('valid', res.get_json())

    def test_export_returns_encoded(self):
        """Export should return an encoded string."""
        res = self.client.post('/api/games', data=json.dumps({'difficulty': 30}),
                             content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}/export')
        self.assertIn('share_code', res.get_json())

    def test_archive_returns_archived_field(self):
        """Archive should return 'archived' field."""
        res = self.client.post('/api/games', data=json.dumps({'difficulty': 30}),
                             content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.put(f'/api/games/{game_id}/archive',
                            data=json.dumps({'archived': True}),
                            content_type='application/json')
        self.assertIn('archived', res.get_json())

    def test_clone_returns_game_id(self):
        """Clone should return a new game_id."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution, 'difficulty': 30}),
            content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.post(f'/api/games/{game_id}/clone')
        self.assertIn('game_id', res.get_json())


if __name__ == '__main__':
    unittest.main(verbosity=2)
