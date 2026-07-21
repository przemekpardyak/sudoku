"""
Tests for the achievements system.
Tests achievement detection based on game completion stats.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestAchievements(unittest.TestCase):
    """Tests for game achievements."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, completed=True, elapsed=100, mistakes=0, hintsUsed=0, difficulty=40):
        state = {
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
            'mistakes': mistakes,
            'hintsUsed': hintsUsed,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def _get_achievements(self):
        """Get achievements from the stats endpoint."""
        res = self.client.get('/api/stats')
        return res.get_json().get('achievements', [])

    def test_first_win_achievement(self):
        """First completed game should unlock 'First Win' achievement."""
        self._create_game(completed=True)
        achievements = self._get_achievements()
        self.assertIn('first_win', achievements)

    def test_no_achievements_without_completed_games(self):
        """No completed games means no achievements."""
        self._create_game(completed=False)
        achievements = self._get_achievements()
        self.assertEqual(len(achievements), 0)

    def test_perfect_game_achievement(self):
        """Completing with 0 mistakes and 0 hints unlocks 'Perfect Game'."""
        self._create_game(completed=True, mistakes=0, hintsUsed=0)
        achievements = self._get_achievements()
        self.assertIn('perfect_game', achievements)

    def test_speed_run_achievement(self):
        """Completing in under 60s unlocks 'Speed Run'."""
        self._create_game(completed=True, elapsed=45)
        achievements = self._get_achievements()
        self.assertIn('speed_run', achievements)

    def test_no_hints_achievement(self):
        """Completing without hints unlocks 'No Hints'."""
        self._create_game(completed=True, hintsUsed=0, mistakes=2)
        achievements = self._get_achievements()
        self.assertIn('no_hints', achievements)

    def test_ten_games_achievement(self):
        """Completing 10 games unlocks 'Dedicated'."""
        for _ in range(10):
            self._create_game(completed=True)
        achievements = self._get_achievements()
        self.assertIn('dedicated', achievements)

    def test_expert_winner_achievement(self):
        """Completing an expert puzzle unlocks 'Expert Winner'."""
        self._create_game(completed=True, difficulty=58)
        achievements = self._get_achievements()
        self.assertIn('expert_winner', achievements)

    def test_multiple_achievements(self):
        """Multiple achievements can be unlocked at once."""
        self._create_game(completed=True, elapsed=30, mistakes=0, hintsUsed=0, difficulty=30)
        achievements = self._get_achievements()
        self.assertIn('first_win', achievements)
        self.assertIn('perfect_game', achievements)
        self.assertIn('speed_run', achievements)
        self.assertIn('no_hints', achievements)


if __name__ == '__main__':
    unittest.main(verbosity=2)
