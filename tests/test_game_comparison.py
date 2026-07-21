"""
Tests for game comparison endpoint.
Tests /api/games/compare that compares two games' performance.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameComparison(unittest.TestCase):
    """Tests for game comparison endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, elapsed=100, difficulty=30, mistakes=0, hintsUsed=0, completed=True):
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
            'mistakes': mistakes,
            'hintsUsed': hintsUsed,
        }), content_type='application/json')
        return res.get_json()['game_id']

    def test_compare_two_games(self):
        """Should compare two games and return differences."""
        g1 = self._create_game(elapsed=100, difficulty=30, mistakes=2)
        g2 = self._create_game(elapsed=200, difficulty=30, mistakes=5)
        res = self.client.get(f'/api/games/compare?a={g1}&b={g2}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('game_a', data)
        self.assertIn('game_b', data)
        self.assertIn('differences', data)

    def test_compare_shows_time_difference(self):
        """Comparison should show time difference."""
        g1 = self._create_game(elapsed=100)
        g2 = self._create_game(elapsed=200)
        res = self.client.get(f'/api/games/compare?a={g1}&b={g2}')
        diffs = res.get_json()['differences']
        self.assertIn('elapsed', diffs)
        self.assertEqual(diffs['elapsed'], 100)  # g2 - g1

    def test_compare_shows_mistake_difference(self):
        """Comparison should show mistake difference."""
        g1 = self._create_game(mistakes=1)
        g2 = self._create_game(mistakes=4)
        res = self.client.get(f'/api/games/compare?a={g1}&b={g2}')
        diffs = res.get_json()['differences']
        self.assertEqual(diffs['mistakes'], 3)

    def test_compare_shows_hints_difference(self):
        """Comparison should show hints difference."""
        g1 = self._create_game(hintsUsed=0)
        g2 = self._create_game(hintsUsed=3)
        res = self.client.get(f'/api/games/compare?a={g1}&b={g2}')
        diffs = res.get_json()['differences']
        self.assertEqual(diffs['hintsUsed'], 3)

    def test_compare_missing_param(self):
        """Missing parameter should return 400."""
        g1 = self._create_game()
        res = self.client.get(f'/api/games/compare?a={g1}')
        self.assertEqual(res.status_code, 400)

    def test_compare_nonexistent_game(self):
        """Nonexistent game should return 404."""
        g1 = self._create_game()
        res = self.client.get(f'/api/games/compare?a={g1}&b=nonexistent')
        self.assertEqual(res.status_code, 404)

    def test_compare_same_game(self):
        """Comparing a game with itself should show zero differences."""
        g1 = self._create_game(elapsed=100, mistakes=2, hintsUsed=1)
        res = self.client.get(f'/api/games/compare?a={g1}&b={g1}')
        diffs = res.get_json()['differences']
        self.assertEqual(diffs['elapsed'], 0)
        self.assertEqual(diffs['mistakes'], 0)

    def test_compare_has_game_summaries(self):
        """Comparison should include both game summaries."""
        g1 = self._create_game(elapsed=100, difficulty=30)
        g2 = self._create_game(elapsed=200, difficulty=50)
        res = self.client.get(f'/api/games/compare?a={g1}&b={g2}')
        data = res.get_json()
        self.assertEqual(data['game_a']['game_id'], g1)
        self.assertEqual(data['game_b']['game_id'], g2)
        self.assertIn('elapsed', data['game_a'])
        self.assertIn('difficulty', data['game_b'])

    def test_compare_shows_difficulty_difference(self):
        """Comparison should show difficulty difference."""
        g1 = self._create_game(difficulty=30)
        g2 = self._create_game(difficulty=50)
        res = self.client.get(f'/api/games/compare?a={g1}&b={g2}')
        diffs = res.get_json()['differences']
        self.assertEqual(diffs['difficulty'], 20)


if __name__ == '__main__':
    unittest.main(verbosity=2)
