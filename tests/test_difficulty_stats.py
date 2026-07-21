"""
Tests for the by_difficulty breakdown in the stats endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestDifficultyStats(unittest.TestCase):
    """Tests for per-difficulty statistics."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, difficulty, elapsed=0, mistakes=0, completed=False):
        state = {
            'difficulty': difficulty,
            'elapsed': elapsed,
            'mistakes': mistakes,
            'completed': completed,
        }
        self.client.post('/api/games', data=json.dumps(state),
                         content_type='application/json')

    def test_by_difficulty_exists(self):
        """Stats should include a by_difficulty field."""
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertIn('by_difficulty', stats)

    def test_by_difficulty_has_all_levels(self):
        """by_difficulty should have entries for all 4 difficulty levels."""
        res = self.client.get('/api/stats')
        stats = res.get_json()
        bd = stats['by_difficulty']
        for level in ['easy', 'medium', 'hard', 'expert']:
            self.assertIn(level, bd)

    def test_empty_by_difficulty(self):
        """by_difficulty should show zeros when no games exist."""
        res = self.client.get('/api/stats')
        stats = res.get_json()
        for level in ['easy', 'medium', 'hard', 'expert']:
            self.assertEqual(stats['by_difficulty'][level]['total'], 0)
            self.assertEqual(stats['by_difficulty'][level]['completed'], 0)
            self.assertEqual(stats['by_difficulty'][level]['best_time'], 0)

    def test_easy_stats(self):
        """Easy difficulty stats should reflect easy games."""
        self._create_game(30, elapsed=100, mistakes=2, completed=True)
        self._create_game(30, elapsed=80, mistakes=0, completed=True)
        res = self.client.get('/api/stats')
        stats = res.get_json()
        easy = stats['by_difficulty']['easy']
        self.assertEqual(easy['total'], 2)
        self.assertEqual(easy['completed'], 2)
        self.assertEqual(easy['best_time'], 80)
        self.assertEqual(easy['avg_time'], 90.0)
        self.assertEqual(easy['avg_mistakes'], 1.0)

    def test_mixed_difficulties(self):
        """Each difficulty level should be tracked independently."""
        self._create_game(30, elapsed=100, completed=True)
        self._create_game(40, elapsed=200, completed=True)
        self._create_game(50, elapsed=300, completed=False)
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['by_difficulty']['easy']['total'], 1)
        self.assertEqual(stats['by_difficulty']['easy']['completed'], 1)
        self.assertEqual(stats['by_difficulty']['medium']['total'], 1)
        self.assertEqual(stats['by_difficulty']['medium']['completed'], 1)
        self.assertEqual(stats['by_difficulty']['hard']['total'], 1)
        self.assertEqual(stats['by_difficulty']['hard']['completed'], 0)
        self.assertEqual(stats['by_difficulty']['expert']['total'], 0)

    def test_best_time_per_difficulty(self):
        """Best time should be per-difficulty, not global."""
        self._create_game(30, elapsed=50, completed=True)
        self._create_game(30, elapsed=100, completed=True)
        self._create_game(40, elapsed=200, completed=True)
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['by_difficulty']['easy']['best_time'], 50)
        self.assertEqual(stats['by_difficulty']['medium']['best_time'], 200)

    def test_incomplete_games_not_in_completed(self):
        """Incomplete games should count in total but not completed."""
        self._create_game(30, elapsed=50, completed=False)
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['by_difficulty']['easy']['total'], 1)
        self.assertEqual(stats['by_difficulty']['easy']['completed'], 0)
        self.assertEqual(stats['by_difficulty']['easy']['best_time'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
