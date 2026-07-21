"""
Tests for cross-endpoint consistency.
Verifies that data returned by different endpoints is consistent.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestCrossEndpointConsistency(unittest.TestCase):
    """Tests for data consistency across different endpoints."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, completed=True, elapsed=100, difficulty=30,
                     mistakes=1, hintsUsed=1, rating=4):
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
            'mistakes': mistakes,
            'hintsUsed': hintsUsed,
            'rating': rating,
        }), content_type='application/json')
        return res.get_json()['game_id']

    def test_stats_matches_profile(self):
        """Stats and profile endpoints should return consistent numbers."""
        self._create_game(elapsed=100, difficulty=30, mistakes=2, rating=4)
        stats = self.client.get('/api/stats').get_json()
        profile = self.client.get('/api/profile').get_json()
        self.assertEqual(stats['total_games'], profile['total_games'])
        self.assertEqual(stats['completed_games'], profile['completed_games'])
        self.assertEqual(stats['total_mistakes'], profile['total_mistakes'])
        self.assertEqual(stats['total_hints'], profile['total_hints'])
        self.assertEqual(stats['best_time'], profile['best_time'])
        self.assertEqual(stats['avg_rating'], profile['avg_rating'])
        self.assertEqual(stats['achievements'], profile['achievements'])

    def test_streaks_match_profile(self):
        """Streaks endpoint should match profile streaks."""
        self._create_game(completed=True)
        self._create_game(completed=True)
        self._create_game(completed=False)
        streaks = self.client.get('/api/streaks').get_json()
        profile = self.client.get('/api/profile').get_json()
        self.assertEqual(streaks['current_streak'], profile['current_streak'])
        self.assertEqual(streaks['best_streak'], profile['best_streak'])
        self.assertEqual(streaks['total_completions'], profile['completed_games'])

    def test_leaderboard_matches_games_list(self):
        """Leaderboard entries should match completed games in list."""
        for i in range(5):
            self._create_game(elapsed=50 + i * 20)
        leaderboard = self.client.get('/api/leaderboard').get_json()['leaderboard']
        games = self.client.get('/api/games').get_json()['games']
        completed_games = [g for g in games if g.get('completed')]
        self.assertEqual(len(leaderboard), len(completed_games))
        # Fastest should be first in leaderboard
        lb_times = [e['elapsed'] for e in leaderboard]
        self.assertEqual(lb_times, sorted(lb_times))

    def test_history_matches_games_list(self):
        """History entries should match games list."""
        self._create_game()
        self._create_game()
        history = self.client.get('/api/history').get_json()
        games = self.client.get('/api/games').get_json()['games']
        self.assertEqual(history['count'], len(games))
        self.assertEqual(history['total'], len(games))

    def test_stats_export_matches_stats(self):
        """Stats export summary should match stats endpoint."""
        self._create_game(elapsed=100, difficulty=30, mistakes=2, hintsUsed=1)
        stats = self.client.get('/api/stats').get_json()
        export = self.client.get('/api/stats/export').get_json()
        self.assertEqual(stats['total_games'], export['summary']['total_games'])
        self.assertEqual(stats['completed_games'], export['summary']['completed_games'])
        self.assertEqual(stats['total_time'], export['summary']['total_time'])
        self.assertEqual(stats['total_mistakes'], export['summary']['total_mistakes'])
        self.assertEqual(stats['achievements'], export['achievements'])

    def test_recommend_matches_profile(self):
        """Recommendation endpoint should match profile recommendation."""
        self._create_game(elapsed=40, difficulty=30)
        rec = self.client.get('/api/recommend-difficulty').get_json()
        profile = self.client.get('/api/profile').get_json()
        self.assertEqual(rec['recommended_difficulty'], profile['recommended_difficulty'])

    def test_game_get_matches_list_summary(self):
        """Full game GET should be consistent with list summary."""
        game_id = self._create_game(elapsed=100, difficulty=30)
        full = self.client.get(f'/api/games/{game_id}').get_json()
        games = self.client.get('/api/games').get_json()['games']
        summary = [g for g in games if g['game_id'] == game_id][0]
        self.assertEqual(full['difficulty'], summary['difficulty'])
        self.assertEqual(full['elapsed'], summary['elapsed'])
        self.assertEqual(full['completed'], summary['completed'])

    def test_progress_matches_certificate(self):
        """Progress and certificate should be consistent for completed games."""
        puzzle, solution = generate_puzzle_for_test()
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
            'board': solution,
            'difficulty': 30,
            'completed': True,
            'elapsed': 100,
            'mistakes': 1,
            'hintsUsed': 0,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        progress = self.client.get(f'/api/games/{game_id}/progress').get_json()
        cert = self.client.get(f'/api/games/{game_id}/certificate').get_json()
        self.assertEqual(progress['filled'], progress['total_empty'])  # All filled
        self.assertEqual(progress['progress_pct'], 100)
        self.assertTrue(cert['completed'])

    def test_stats_count_after_delete_all(self):
        """All endpoints should show zero after delete all."""
        self._create_game()
        self._create_game()
        self.client.delete('/api/games')
        stats = self.client.get('/api/stats').get_json()
        profile = self.client.get('/api/profile').get_json()
        streaks = self.client.get('/api/streaks').get_json()
        history = self.client.get('/api/history').get_json()
        self.assertEqual(stats['total_games'], 0)
        self.assertEqual(profile['total_games'], 0)
        self.assertEqual(streaks['total_games'], 0)
        self.assertEqual(history['total'], 0)


def generate_puzzle_for_test():
    from sudoku import generate_puzzle
    return generate_puzzle(difficulty=30)


if __name__ == '__main__':
    unittest.main(verbosity=2)
