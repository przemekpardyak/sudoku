"""
Tests for player profile endpoint.
Tests /api/profile which returns a comprehensive player profile.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestPlayerProfile(unittest.TestCase):
    """Tests for player profile endpoint."""

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

    def test_empty_profile(self):
        """Profile with no games should have sensible defaults."""
        res = self.client.get('/api/profile')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['total_games'], 0)
        self.assertEqual(data['completed_games'], 0)
        self.assertEqual(data['achievements'], [])

    def test_profile_has_stats(self):
        """Profile should include key stats."""
        self._create_game(elapsed=100, difficulty=30, mistakes=2, rating=4)
        res = self.client.get('/api/profile')
        data = res.get_json()
        self.assertEqual(data['total_games'], 1)
        self.assertEqual(data['completed_games'], 1)
        self.assertIn('best_time', data)
        self.assertIn('avg_completion_time', data)
        self.assertIn('total_mistakes', data)

    def test_profile_has_achievements(self):
        """Profile should include achievements."""
        self._create_game(elapsed=40, mistakes=0, hintsUsed=0)
        res = self.client.get('/api/profile')
        achievements = res.get_json()['achievements']
        self.assertIn('first_win', achievements)
        self.assertIn('perfect_game', achievements)

    def test_profile_has_streaks(self):
        """Profile should include streak info."""
        for _ in range(3):
            self._create_game(completed=True)
        res = self.client.get('/api/profile')
        data = res.get_json()
        self.assertIn('current_streak', data)
        self.assertIn('best_streak', data)
        self.assertEqual(data['current_streak'], 3)
        self.assertEqual(data['best_streak'], 3)

    def test_profile_has_difficulty_breakdown(self):
        """Profile should include per-difficulty stats."""
        self._create_game(elapsed=100, difficulty=30)
        self._create_game(elapsed=200, difficulty=50)
        res = self.client.get('/api/profile')
        data = res.get_json()
        self.assertIn('by_difficulty', data)

    def test_profile_has_completion_rate(self):
        """Profile should include completion rate."""
        self._create_game(completed=True)
        self._create_game(completed=False)
        res = self.client.get('/api/profile')
        self.assertEqual(res.get_json()['completion_pct'], 50.0)

    def test_profile_has_avg_rating(self):
        """Profile should include average rating."""
        self._create_game(rating=4)
        self._create_game(rating=5)
        res = self.client.get('/api/profile')
        self.assertEqual(res.get_json()['avg_rating'], 4.5)

    def test_profile_has_recommendation(self):
        """Profile should include difficulty recommendation."""
        self._create_game(elapsed=40, difficulty=30)
        res = self.client.get('/api/profile')
        data = res.get_json()
        self.assertIn('recommended_difficulty', data)
        self.assertIn('recommendation_reasoning', data)

    def test_profile_has_level(self):
        """Profile should include a player level based on experience."""
        for _ in range(5):
            self._create_game(completed=True)
        res = self.client.get('/api/profile')
        self.assertIn('level', res.get_json())

    def test_profile_level_increases(self):
        """Player level should increase with more completed games."""
        # First profile with 1 game
        self._create_game(completed=True)
        res1 = self.client.get('/api/profile')
        level1 = res1.get_json()['level']

        # Add more games
        for _ in range(9):
            self._create_game(completed=True)
        res2 = self.client.get('/api/profile')
        level2 = res2.get_json()['level']

        self.assertGreater(level2, level1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
