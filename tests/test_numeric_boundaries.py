"""
Tests for numeric edge cases and boundary values.
Tests that the API handles extreme numeric values correctly.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestNumericBoundaries(unittest.TestCase):
    """Tests for numeric edge cases and boundary values."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_zero_difficulty(self):
        """Difficulty 0 should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 0,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game.get('difficulty'), 0)

    def test_max_difficulty(self):
        """Max difficulty (58) should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 58, 'completed': True, 'elapsed': 600,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game.get('difficulty'), 58)

    def test_zero_elapsed(self):
        """Zero elapsed time should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 0, 'completed': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['elapsed'], 0)

    def test_large_elapsed(self):
        """Very large elapsed time should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 9999999, 'completed': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['elapsed'], 9999999)

    def test_zero_mistakes(self):
        """Zero mistakes should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'mistakes': 0, 'completed': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['mistakes'], 0)

    def test_large_mistakes(self):
        """Large mistake count should work."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'mistakes': 999, 'completed': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']
        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['mistakes'], 999)

    def test_rating_boundaries(self):
        """Rating boundaries 1 and 5 should work."""
        for rating in [1, 5]:
            res = self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': 100, 'rating': rating,
            }), content_type='application/json')
            game_id = res.get_json()['game_id']
            game = self.client.get(f'/api/games/{game_id}').get_json()
            self.assertEqual(game['rating'], rating)

    def test_leaderboard_with_zero_time(self):
        """Leaderboard should handle zero elapsed time."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 0,
        }), content_type='application/json')
        res = self.client.get('/api/leaderboard')
        self.assertEqual(res.get_json()['leaderboard'][0]['elapsed'], 0)

    def test_stats_with_all_zero_values(self):
        """Stats should work with all zero values."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True,
            'elapsed': 0, 'mistakes': 0, 'hintsUsed': 0,
        }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['total_time'], 0)
        self.assertEqual(stats['total_mistakes'], 0)
        self.assertEqual(stats['total_hints'], 0)
        self.assertEqual(stats['best_time'], 0)

    def test_avg_time_with_zero(self):
        """Average time with zero should be 0."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 0,
        }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['avg_completion_time'], 0.0)

    def test_completion_pct_boundaries(self):
        """Completion percentage should handle 0% and 100%."""
        # 0% (no completed games)
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': False,
        }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['completion_rate'], 0.0)

        # 100% (all completed)
        self.client.delete('/api/games')
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['completion_rate'], 1.0)

    def test_recommend_with_extreme_times(self):
        """Recommendation should handle very fast and very slow times."""
        # Very fast
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 1,
        }), content_type='application/json')
        res = self.client.get('/api/recommend-difficulty')
        self.assertGreater(res.get_json()['recommended_difficulty'], 30)

    def test_streak_with_many_completions(self):
        """Streak should handle many completions correctly."""
        for _ in range(20):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': 100,
            }), content_type='application/json')
        res = self.client.get('/api/streaks')
        self.assertEqual(res.get_json()['current_streak'], 20)
        self.assertEqual(res.get_json()['best_streak'], 20)


if __name__ == '__main__':
    unittest.main(verbosity=2)
