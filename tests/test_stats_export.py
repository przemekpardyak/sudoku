"""
Tests for the stats export endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestStatsExport(unittest.TestCase):
    """Tests for the stats export endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, completed=True, elapsed=100, difficulty=30,
                     mistakes=0, hintsUsed=0, rating=0):
        self.client.post('/api/games', data=json.dumps({
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
            'mistakes': mistakes,
            'hintsUsed': hintsUsed,
            'rating': rating,
        }), content_type='application/json')

    def test_empty_export(self):
        """Export with no games should return valid structure."""
        res = self.client.get('/api/stats/export')
        data = res.get_json()
        self.assertEqual(data['summary']['total_games'], 0)
        self.assertEqual(data['summary']['completed_games'], 0)
        self.assertEqual(data['top_5_fastest'], [])
        self.assertEqual(data['achievements'], [])

    def test_export_has_summary(self):
        """Export should have summary with key stats."""
        self._create_game(elapsed=100, difficulty=30)
        res = self.client.get('/api/stats/export')
        summary = res.get_json()['summary']
        self.assertIn('total_games', summary)
        self.assertIn('completed_games', summary)
        self.assertIn('completion_rate', summary)
        self.assertIn('total_time', summary)
        self.assertIn('total_mistakes', summary)
        self.assertIn('total_hints', summary)
        self.assertIn('best_time', summary)
        self.assertIn('avg_completion_time', summary)
        self.assertIn('avg_mistakes', summary)
        self.assertIn('avg_rating', summary)

    def test_export_has_by_difficulty(self):
        """Export should have per-difficulty breakdown."""
        self._create_game(elapsed=100, difficulty=30)
        self._create_game(elapsed=200, difficulty=50)
        res = self.client.get('/api/stats/export')
        by_diff = res.get_json()['by_difficulty']
        self.assertIn('30', by_diff)
        self.assertIn('50', by_diff)
        self.assertEqual(by_diff['30']['count'], 1)
        self.assertEqual(by_diff['30']['best_time'], 100)

    def test_export_has_achievements(self):
        """Export should include achievements."""
        self._create_game(elapsed=40, mistakes=0, hintsUsed=0)
        res = self.client.get('/api/stats/export')
        achievements = res.get_json()['achievements']
        self.assertIn('first_win', achievements)
        self.assertIn('perfect_game', achievements)
        self.assertIn('speed_run', achievements)

    def test_export_has_top5(self):
        """Export should include top 5 fastest games."""
        for i in range(10):
            self._create_game(elapsed=50 + i * 20, difficulty=30)
        res = self.client.get('/api/stats/export')
        top5 = res.get_json()['top_5_fastest']
        self.assertEqual(len(top5), 5)
        # Should be sorted by time
        times = [e['elapsed'] for e in top5]
        self.assertEqual(times, sorted(times))
        self.assertEqual(times[0], 50)

    def test_export_summary_values_correct(self):
        """Summary values should be correct."""
        self._create_game(elapsed=100, difficulty=30, mistakes=2, hintsUsed=1)
        self._create_game(elapsed=200, difficulty=30, mistakes=3, hintsUsed=2)
        res = self.client.get('/api/stats/export')
        summary = res.get_json()['summary']
        self.assertEqual(summary['total_games'], 2)
        self.assertEqual(summary['completed_games'], 2)
        self.assertEqual(summary['total_time'], 300)
        self.assertEqual(summary['total_mistakes'], 5)
        self.assertEqual(summary['total_hints'], 3)
        self.assertEqual(summary['best_time'], 100)
        self.assertEqual(summary['avg_completion_time'], 150.0)
        self.assertEqual(summary['avg_mistakes'], 2.5)

    def test_export_includes_incomplete_games_in_count(self):
        """Total games should include incomplete ones."""
        self._create_game(completed=True, elapsed=100)
        self._create_game(completed=False, elapsed=50)
        res = self.client.get('/api/stats/export')
        summary = res.get_json()['summary']
        self.assertEqual(summary['total_games'], 2)
        self.assertEqual(summary['completed_games'], 1)
        self.assertEqual(summary['completion_rate'], 50.0)

    def test_export_by_difficulty_has_stats(self):
        """Per-difficulty entries should have count, best_time, avg_time, avg_mistakes."""
        self._create_game(elapsed=100, difficulty=30, mistakes=1)
        self._create_game(elapsed=200, difficulty=30, mistakes=3)
        res = self.client.get('/api/stats/export')
        d30 = res.get_json()['by_difficulty']['30']
        self.assertEqual(d30['count'], 2)
        self.assertEqual(d30['best_time'], 100)
        self.assertEqual(d30['avg_time'], 150.0)
        self.assertEqual(d30['avg_mistakes'], 2.0)

    def test_export_top5_has_fields(self):
        """Top 5 entries should have game_id, difficulty, elapsed, mistakes."""
        self._create_game(elapsed=50, difficulty=30, mistakes=1)
        res = self.client.get('/api/stats/export')
        entry = res.get_json()['top_5_fastest'][0]
        self.assertIn('game_id', entry)
        self.assertIn('difficulty', entry)
        self.assertIn('elapsed', entry)
        self.assertIn('mistakes', entry)


if __name__ == '__main__':
    unittest.main(verbosity=2)
