"""
Tests for edge cases in newer endpoints.
Tests boundary conditions for profile, streaks, leaderboard, history, etc.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestNewEndpointEdgeCases(unittest.TestCase):
    """Edge case tests for newer endpoints."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_profile_level_caps_at_100(self):
        """Player level should cap at 100."""
        for _ in range(105):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': 100,
            }), content_type='application/json')
        res = self.client.get('/api/profile')
        self.assertEqual(res.get_json()['level'], 100)

    def test_leaderboard_with_single_game(self):
        """Leaderboard with single game should work."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        res = self.client.get('/api/leaderboard')
        data = res.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['leaderboard'][0]['elapsed'], 100)

    def test_streaks_all_incomplete(self):
        """Streaks with all incomplete games should be zero."""
        for _ in range(5):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': False, 'elapsed': 100,
            }), content_type='application/json')
        res = self.client.get('/api/streaks')
        data = res.get_json()
        self.assertEqual(data['current_streak'], 0)
        self.assertEqual(data['best_streak'], 0)
        self.assertEqual(data['total_completions'], 0)

    def test_history_with_large_limit(self):
        """History with limit larger than game count should return all."""
        for _ in range(3):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'elapsed': 100,
            }), content_type='application/json')
        res = self.client.get('/api/history?limit=1000')
        self.assertEqual(res.get_json()['count'], 3)

    def test_recommend_with_single_game(self):
        """Recommendation with single completed game should work."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        res = self.client.get('/api/recommend-difficulty')
        data = res.get_json()
        self.assertEqual(data['current_difficulty'], 30)
        self.assertEqual(data['recommended_difficulty'], 30)

    def test_stats_export_empty(self):
        """Stats export with no games should have valid structure."""
        res = self.client.get('/api/stats/export')
        data = res.get_json()
        self.assertEqual(data['summary']['total_games'], 0)
        self.assertEqual(data['top_5_fastest'], [])
        self.assertEqual(data['by_difficulty'], {})

    def test_compare_same_game_zero_diffs(self):
        """Comparing a game with itself should show all zero differences."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100, 'mistakes': 2, 'hintsUsed': 1,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/compare?a={game_id}&b={game_id}')
        diffs = res.get_json()['differences']
        for v in diffs.values():
            self.assertEqual(v, 0)

    def test_progress_no_solution(self):
        """Progress should handle game without solution field."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertEqual(res.status_code, 200)

    def test_certificate_performance_levels(self):
        """Certificate should return different performance levels."""
        from sudoku import generate_puzzle
        puzzle, solution = generate_puzzle(difficulty=30)

        # Perfect game
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100, 'mistakes': 0, 'hintsUsed': 0,
        }), content_type='application/json')
        cert = self.client.get(f'/api/games/{res.get_json()["game_id"]}/certificate').get_json()
        self.assertEqual(cert['performance'], 'perfect')

        # Completed with many mistakes
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 500, 'mistakes': 10, 'hintsUsed': 5,
        }), content_type='application/json')
        cert = self.client.get(f'/api/games/{res.get_json()["game_id"]}/certificate').get_json()
        self.assertEqual(cert['performance'], 'completed')

    def test_profile_with_mixed_games(self):
        """Profile should handle mixed completed/incomplete games."""
        for i in range(10):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30,
                'completed': i % 2 == 0,
                'elapsed': 100,
                'mistakes': i,
                'hintsUsed': i // 2,
                'rating': i % 3 + 3,
            }), content_type='application/json')
        res = self.client.get('/api/profile')
        data = res.get_json()
        self.assertEqual(data['total_games'], 10)
        self.assertEqual(data['completed_games'], 5)
        self.assertEqual(data['completion_pct'], 50.0)
        self.assertGreater(data['level'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
