"""
Tests for API documentation and endpoint coverage.
Verifies that all documented endpoints exist and work.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestAPIDocumentation(unittest.TestCase):
    """Tests verifying API endpoint coverage matches documentation."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_all_documented_get_endpoints(self):
        """All documented GET endpoints should be accessible."""
        endpoints = [
            ('/', 200),  # Root HTML page
            ('/api/new-game?difficulty=30', 200),
            ('/api/daily-puzzle', 200),
            ('/api/weekly-puzzle', 200),
            ('/api/games', 200),
            ('/api/best-times', 200),
            ('/api/stats', 200),
            ('/api/leaderboard', 200),
            ('/api/recommend-difficulty', 200),
            ('/api/stats/export', 200),
            ('/api/history', 200),
            ('/api/streaks', 200),
            ('/api/profile', 200),
        ]
        for path, expected_status in endpoints:
            res = self.client.get(path)
            self.assertEqual(res.status_code, expected_status,
                           f"GET {path} returned {res.status_code}, expected {expected_status}")

    def test_all_documented_post_endpoints(self):
        """All documented POST endpoints should work."""
        # Create game
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 201)
        game_id = res.get_json()['game_id']

        # Clone game
        res = self.client.post(f'/api/games/{game_id}/clone')
        self.assertEqual(res.status_code, 201)

        # Import game
        export_res = self.client.get(f'/api/games/{game_id}/export')
        share_code = export_res.get_json()['share_code']
        res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 201)

        # Solve
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/solve', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # Hint
        res = self.client.post('/api/hint', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # Validate
        res = self.client.post('/api/validate', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # Analyze
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_all_documented_put_endpoints(self):
        """All documented PUT endpoints should work."""
        # Create a game first
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
            'completed': True,
            'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Update game
        res = self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'elapsed': 200,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # Archive
        res = self.client.put(f'/api/games/{game_id}/archive', data=json.dumps({
            'archived': True,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # Rate
        res = self.client.put(f'/api/games/{game_id}/rate', data=json.dumps({
            'rating': 5,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 200)

    def test_all_documented_delete_endpoints(self):
        """All documented DELETE endpoints should work."""
        # Create a game
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Delete single
        res = self.client.delete(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 200)

        # Create more and delete all
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')

        res = self.client.delete('/api/games')
        self.assertEqual(res.status_code, 200)

    def test_all_game_sub_endpoints(self):
        """All game-specific sub-endpoints should work."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
            'board': solution,
            'difficulty': 30,
            'completed': True,
            'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # GET game
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 200)

        # GET progress
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertEqual(res.status_code, 200)

        # GET certificate
        res = self.client.get(f'/api/games/{game_id}/certificate')
        self.assertEqual(res.status_code, 200)

        # GET export
        res = self.client.get(f'/api/games/{game_id}/export')
        self.assertEqual(res.status_code, 200)

        # GET compare
        res = self.client.get(f'/api/games/compare?a={game_id}&b={game_id}')
        self.assertEqual(res.status_code, 200)

    def test_endpoint_count(self):
        """Verify we have a comprehensive set of endpoints."""
        # Count all routes
        routes = [rule.rule for rule in self.app.url_map.iter_rules()
                  if rule.rule.startswith('/api/')]
        # Should have at least 20 API routes
        self.assertGreaterEqual(len(routes), 20,
                               f"Only {len(routes)} API routes found: {routes}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
