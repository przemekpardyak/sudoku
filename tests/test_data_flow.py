"""
Tests for data flow integrity across operations.
Verifies that data flows correctly through create, update, list, and analytics.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestDataFlow(unittest.TestCase):
    """Tests for data flow integrity across operations."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_difficulty_flows_to_stats(self):
        """Difficulty set at creation should appear in stats by_difficulty."""
        for d in [20, 30, 40]:
            self.client.post('/api/games', data=json.dumps({
                'difficulty': d, 'completed': True, 'elapsed': 100,
            }), content_type='application/json')
        res = self.client.get('/api/stats')
        by_diff = res.get_json()['by_difficulty']
        self.assertIn('easy', by_diff)
        self.assertIn('medium', by_diff)
        self.assertIn('hard', by_diff)

    def test_elapsed_flows_to_leaderboard(self):
        """Elapsed time set at creation should appear in leaderboard."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 42,
        }), content_type='application/json')
        res = self.client.get('/api/leaderboard')
        self.assertEqual(res.get_json()['leaderboard'][0]['elapsed'], 42)

    def test_mistakes_flows_to_stats(self):
        """Mistakes should flow from game to stats."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100, 'mistakes': 7,
        }), content_type='application/json')
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['total_mistakes'], 7)

    def test_hints_flows_to_stats(self):
        """Hints used should flow from game to stats."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100, 'hintsUsed': 3,
        }), content_type='application/json')
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['total_hints'], 3)

    def test_rating_flows_to_profile(self):
        """Rating should flow from game to profile avg_rating."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100, 'rating': 4,
        }), content_type='application/json')
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100, 'rating': 5,
        }), content_type='application/json')
        res = self.client.get('/api/profile')
        self.assertEqual(res.get_json()['avg_rating'], 4.5)

    def test_completion_flows_to_streaks(self):
        """Completion should flow to streaks."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        res = self.client.get('/api/streaks')
        self.assertEqual(res.get_json()['current_streak'], 1)
        self.assertEqual(res.get_json()['total_completions'], 1)

    def test_tags_flows_to_search(self):
        """Tags should be searchable in games list."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'tags': ['special'],
        }), content_type='application/json')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertTrue(any('special' in g.get('tags', []) for g in games))

    def test_created_at_flows_to_history(self):
        """Created_at should be in history entries."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100,
        }), content_type='application/json')
        res = self.client.get('/api/history')
        entry = res.get_json()['history'][0]
        self.assertIn('created_at', entry)

    def test_difficulty_flows_to_recommendation(self):
        """Difficulty should flow to recommendation engine."""
        self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        res = self.client.get('/api/recommend-difficulty')
        self.assertEqual(res.get_json()['current_difficulty'], 30)

    def test_progress_flows_to_certificate(self):
        """Progress should be 100% when certificate is available."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        progress = self.client.get(f'/api/games/{game_id}/progress').get_json()
        cert = self.client.get(f'/api/games/{game_id}/certificate').get_json()
        self.assertEqual(progress['progress_pct'], 100)
        self.assertTrue(cert['completed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
