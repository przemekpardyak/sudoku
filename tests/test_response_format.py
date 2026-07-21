"""
Tests for API response format consistency.
Verifies all endpoints return consistent JSON structure.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestResponseFormat(unittest.TestCase):
    """Tests for API response format consistency."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_all_get_endpoints_return_json(self):
        """All GET API endpoints should return JSON."""
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
            self.assertEqual(res.content_type, 'application/json',
                           f"Endpoint {ep} returned {res.content_type}")

    def test_error_responses_have_error_field(self):
        """All error responses should have an 'error' field."""
        # 404 on nonexistent game
        res = self.client.get('/api/games/nonexistent')
        self.assertIn('error', res.get_json())

        # 404 on nonexistent certificate
        res = self.client.get('/api/games/nonexistent/certificate')
        self.assertIn('error', res.get_json())

        # 404 on nonexistent progress
        res = self.client.get('/api/games/nonexistent/progress')
        self.assertIn('error', res.get_json())

    def test_create_returns_201(self):
        """Creating a game should return 201."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_create_returns_game_id(self):
        """Create response should include game_id."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        self.assertIn('game_id', res.get_json())

    def test_list_returns_games_array(self):
        """Games list should return a 'games' array."""
        res = self.client.get('/api/games')
        self.assertIn('games', res.get_json())
        self.assertIsInstance(res.get_json()['games'], list)

    def test_stats_returns_all_fields(self):
        """Stats should return all expected fields."""
        res = self.client.get('/api/stats')
        data = res.get_json()
        expected = ['total_games', 'completed_games', 'completion_rate',
                    'total_time', 'total_mistakes', 'total_hints',
                    'avg_completion_time', 'best_time', 'avg_mistakes',
                    'avg_rating', 'by_difficulty', 'achievements']
        for field in expected:
            self.assertIn(field, data, f"Missing field: {field}")

    def test_profile_returns_all_fields(self):
        """Profile should return all expected fields."""
        res = self.client.get('/api/profile')
        data = res.get_json()
        expected = ['total_games', 'completed_games', 'completion_pct',
                    'total_time', 'total_mistakes', 'total_hints',
                    'best_time', 'avg_completion_time', 'avg_rating',
                    'by_difficulty', 'achievements', 'current_streak',
                    'best_streak', 'recommended_difficulty',
                    'recommendation_reasoning', 'level']
        for field in expected:
            self.assertIn(field, data, f"Missing field: {field}")

    def test_leaderboard_returns_leaderboard_array(self):
        """Leaderboard should return a 'leaderboard' array."""
        res = self.client.get('/api/leaderboard')
        self.assertIn('leaderboard', res.get_json())
        self.assertIn('count', res.get_json())

    def test_history_returns_history_array(self):
        """History should return a 'history' array."""
        res = self.client.get('/api/history')
        self.assertIn('history', res.get_json())
        self.assertIn('count', res.get_json())
        self.assertIn('total', res.get_json())

    def test_streaks_returns_all_fields(self):
        """Streaks should return all expected fields."""
        res = self.client.get('/api/streaks')
        data = res.get_json()
        for field in ['current_streak', 'best_streak', 'total_completions',
                      'total_games', 'completion_rate']:
            self.assertIn(field, data)

    def test_solve_returns_solved_board(self):
        """Solve should return 'solved' field."""
        from sudoku import generate_puzzle
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/solve', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        self.assertIn('solved', res.get_json())

    def test_validate_returns_validity(self):
        """Validate should return 'valid' field."""
        from sudoku import generate_puzzle
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/validate', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        self.assertIn('valid', res.get_json())

    def test_hint_returns_row_col_value(self):
        """Hint should return row, col, value."""
        from sudoku import generate_puzzle
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/hint', data=json.dumps({
            'board': puzzle,
        }), content_type='application/json')
        data = res.get_json()
        self.assertIn('row', data)
        self.assertIn('col', data)
        self.assertIn('value', data)

    def test_analyze_returns_metrics(self):
        """Analyze should return all metrics."""
        from sudoku import generate_puzzle
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
        }), content_type='application/json')
        data = res.get_json()
        for field in ['empty_cells', 'filled_cells', 'has_conflicts',
                      'unique_solution', 'difficulty_rating']:
            self.assertIn(field, data)

    def test_new_game_returns_puzzle_and_solution(self):
        """New game should return puzzle and solution."""
        res = self.client.get('/api/new-game?difficulty=30')
        data = res.get_json()
        self.assertIn('puzzle', data)
        self.assertIn('solution', data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
