"""
Final health check tests.
Quick smoke tests to verify the service is healthy.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestHealthCheck(unittest.TestCase):
    """Quick health check tests."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_root_returns_html(self):
        """Root should return HTML page."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

    def test_all_endpoints_respond(self):
        """All endpoints should respond quickly."""
        endpoints = [
            '/api/new-game?difficulty=30',
            '/api/daily-puzzle',
            '/api/weekly-puzzle',
            '/api/games',
            '/api/best-times',
            '/api/stats',
            '/api/leaderboard',
            '/api/recommend-difficulty',
            '/api/stats/export',
            '/api/history',
            '/api/streaks',
            '/api/profile',
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Endpoint {ep} failed")

    def test_create_and_retrieve(self):
        """Basic create and retrieve should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        gid = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{gid}')
        self.assertEqual(res.status_code, 200)

    def test_solve_works(self):
        """Solver should work."""
        from sudoku import generate_puzzle
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/solve', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('solved', res.get_json())

    def test_stats_returns_valid_structure(self):
        """Stats should return valid structure."""
        res = self.client.get('/api/stats')
        data = res.get_json()
        self.assertIn('total_games', data)
        self.assertIn('completed_games', data)
        self.assertIn('achievements', data)

    def test_no_leaks_between_tests(self):
        """Storage should be clean at start of each test."""
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 0)

    def test_all_error_responses_are_json(self):
        """All error responses should be JSON."""
        res = self.client.get('/api/games/nonexistent')
        self.assertEqual(res.content_type, 'application/json')
        self.assertIn('error', res.get_json())

    def test_app_is_configured(self):
        """App should be properly configured."""
        self.assertIsNotNone(app)


if __name__ == '__main__':
    unittest.main(verbosity=2)
