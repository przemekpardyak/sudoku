"""
Tests for API response format consistency across all endpoints.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestAPIResponseFormat(unittest.TestCase):
    """Tests for API response format consistency."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_new_game_has_puzzle_and_solution(self):
        """New game response should have puzzle and solution arrays."""
        res = self.client.get('/api/new-game?difficulty=30')
        data = res.get_json()
        self.assertIn('puzzle', data)
        self.assertIn('solution', data)
        self.assertEqual(len(data['puzzle']), 9)
        self.assertEqual(len(data['solution']), 9)

    def test_daily_puzzle_has_date_and_seed(self):
        """Daily puzzle response should have date and seed fields."""
        res = self.client.get('/api/daily-puzzle')
        data = res.get_json()
        self.assertIn('date', data)
        self.assertIn('seed', data)
        self.assertIn('puzzle', data)
        self.assertIn('solution', data)

    def test_games_list_has_games_array(self):
        """Games list response should have a games array."""
        res = self.client.get('/api/games')
        data = res.get_json()
        self.assertIn('games', data)
        self.assertIsInstance(data['games'], list)

    def test_create_game_returns_game_id(self):
        """Creating a game should return a game_id."""
        res = self.client.post('/api/games', data=json.dumps({'difficulty': 40}),
                               content_type='application/json')
        data = res.get_json()
        self.assertIn('game_id', data)
        self.assertTrue(len(data['game_id']) > 0)

    def test_get_game_returns_full_state(self):
        """Getting a game should return the full state including board."""
        state = {'difficulty': 40, 'elapsed': 50, 'mistakes': 2,
                 'board': [[1]*9]*9, 'puzzle': [[0]*9]*9}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertIn('board', game)
        self.assertIn('elapsed', game)
        self.assertIn('mistakes', game)

    def test_stats_has_all_fields(self):
        """Stats response should have all expected fields."""
        res = self.client.get('/api/stats')
        data = res.get_json()
        for field in ['total_games', 'completed_games', 'completion_rate',
                      'total_time', 'total_mistakes', 'total_hints',
                      'avg_completion_time']:
            self.assertIn(field, data, f"Stats should include {field}")

    def test_best_times_returns_dict(self):
        """Best times should return a dict (not array)."""
        res = self.client.get('/api/best-times')
        data = res.get_json()
        self.assertIsInstance(data, dict)

    def test_export_returns_share_code(self):
        """Export should return a share_code string."""
        state = {'difficulty': 40, 'elapsed': 50}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}/export')
        data = res.get_json()
        self.assertIn('share_code', data)
        self.assertIsInstance(data['share_code'], str)

    def test_error_responses_have_error_field(self):
        """Error responses should have an 'error' field."""
        # 404 on nonexistent game
        res = self.client.get('/api/games/nonexistent')
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertIn('error', data)

    def test_content_type_is_json(self):
        """All API responses should have JSON content type."""
        endpoints = ['/api/new-game', '/api/daily-puzzle', '/api/games', '/api/stats',
                     '/api/best-times']
        for endpoint in endpoints:
            res = self.client.get(endpoint)
            self.assertIn('application/json', res.content_type,
                         f"{endpoint} should return JSON")


if __name__ == '__main__':
    unittest.main(verbosity=2)
