"""
Tests for API endpoint discovery and consistency.
Verifies all endpoints respond and have consistent response format.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestAPIDiscovery(unittest.TestCase):
    """Tests for API endpoint discovery."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_root_page(self):
        """Root endpoint should return HTML."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/html', res.content_type)

    def test_new_game_endpoint(self):
        """New game endpoint should return JSON."""
        res = self.client.get('/api/new-game?difficulty=30')
        self.assertEqual(res.status_code, 200)
        self.assertIn('puzzle', res.get_json())
        self.assertIn('solution', res.get_json())

    def test_daily_puzzle_endpoint(self):
        """Daily puzzle endpoint should return JSON."""
        res = self.client.get('/api/daily-puzzle')
        self.assertEqual(res.status_code, 200)
        self.assertIn('puzzle', res.get_json())

    def test_weekly_puzzle_endpoint(self):
        """Weekly puzzle endpoint should return JSON."""
        res = self.client.get('/api/weekly-puzzle')
        self.assertEqual(res.status_code, 200)
        self.assertIn('puzzle', res.get_json())

    def test_games_list_endpoint(self):
        """Games list endpoint should return JSON."""
        res = self.client.get('/api/games')
        self.assertEqual(res.status_code, 200)
        self.assertIn('games', res.get_json())

    def test_stats_endpoint(self):
        """Stats endpoint should return JSON."""
        res = self.client.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        self.assertIn('total_games', res.get_json())

    def test_best_times_endpoint(self):
        """Best times endpoint should return JSON."""
        res = self.client.get('/api/best-times')
        self.assertEqual(res.status_code, 200)

    def test_leaderboard_endpoint(self):
        """Leaderboard endpoint should return JSON."""
        res = self.client.get('/api/leaderboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn('leaderboard', res.get_json())

    def test_recommend_difficulty_endpoint(self):
        """Recommend difficulty endpoint should return JSON."""
        res = self.client.get('/api/recommend-difficulty')
        self.assertEqual(res.status_code, 200)
        self.assertIn('recommended_difficulty', res.get_json())

    def test_stats_export_endpoint(self):
        """Stats export endpoint should return JSON."""
        res = self.client.get('/api/stats/export')
        self.assertEqual(res.status_code, 200)
        self.assertIn('summary', res.get_json())

    def test_history_endpoint(self):
        """History endpoint should return JSON."""
        res = self.client.get('/api/history')
        self.assertEqual(res.status_code, 200)
        self.assertIn('history', res.get_json())

    def test_all_get_endpoints_return_200(self):
        """All GET endpoints should return 200 on empty database."""
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
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Endpoint {ep} returned {res.status_code}")

    def test_all_post_endpoints_require_json(self):
        """All POST endpoints should handle missing body gracefully."""
        res = self.client.post('/api/games', content_type='application/json')
        self.assertEqual(res.status_code, 400)

        res = self.client.post('/api/games/import', content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_404_returns_json_error(self):
        """404 should return JSON with error field."""
        res = self.client.get('/api/games/nonexistent')
        self.assertEqual(res.status_code, 404)
        self.assertIn('error', res.get_json())

    def test_unknown_endpoint_returns_404(self):
        """Unknown API endpoint should return 404."""
        res = self.client.get('/api/unknown')
        self.assertEqual(res.status_code, 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
