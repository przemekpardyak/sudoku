"""
Tests for query parameter handling across all endpoints.
Tests that query parameters are parsed correctly and edge cases handled.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestQueryParameters(unittest.TestCase):
    """Tests for query parameter handling."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_games(self, count=5, completed=True, difficulty=30):
        for _ in range(count):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': difficulty, 'completed': completed, 'elapsed': 100,
            }), content_type='application/json')

    def test_games_limit_default(self):
        """Default limit should return all games (up to default)."""
        self._create_games(3)
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 3)

    def test_games_limit_1(self):
        """Limit=1 should return only 1 game."""
        self._create_games(5)
        res = self.client.get('/api/games?limit=1')
        self.assertEqual(len(res.get_json()['games']), 1)

    def test_games_limit_0(self):
        """Limit=0 should return empty list."""
        self._create_games(3)
        res = self.client.get('/api/games?limit=0')
        self.assertEqual(len(res.get_json()['games']), 0)

    def test_games_limit_negative(self):
        """Negative limit should be handled gracefully."""
        self._create_games(3)
        res = self.client.get('/api/games?limit=-5')
        self.assertIn(res.status_code, [200, 400])

    def test_games_limit_non_numeric(self):
        """Non-numeric limit should be handled gracefully."""
        self._create_games(3)
        res = self.client.get('/api/games?limit=abc')
        self.assertIn(res.status_code, [200, 400])

    def test_games_limit_large(self):
        """Large limit should return all games."""
        self._create_games(3)
        res = self.client.get('/api/games?limit=10000')
        self.assertEqual(len(res.get_json()['games']), 3)

    def test_leaderboard_limit(self):
        """Leaderboard should respect limit parameter."""
        self._create_games(10)
        res = self.client.get('/api/leaderboard?limit=3')
        self.assertEqual(res.get_json()['count'], 3)

    def test_leaderboard_difficulty_filter(self):
        """Leaderboard should filter by difficulty."""
        self._create_games(3, difficulty=30)
        self._create_games(2, difficulty=40)
        res = self.client.get('/api/leaderboard?difficulty=30')
        data = res.get_json()
        self.assertTrue(all(e['difficulty'] == 30 for e in data['leaderboard']))

    def test_history_limit(self):
        """History should respect limit parameter."""
        self._create_games(10)
        res = self.client.get('/api/history?limit=3')
        self.assertEqual(res.get_json()['count'], 3)

    def test_history_completed_filter(self):
        """History should filter by completed status."""
        self._create_games(3, completed=True)
        self._create_games(2, completed=False)
        res = self.client.get('/api/history?completed=true')
        data = res.get_json()
        self.assertTrue(all(e['completed'] for e in data['history']))

    def test_history_difficulty_filter(self):
        """History should filter by difficulty."""
        self._create_games(3, difficulty=30)
        self._create_games(2, difficulty=40)
        res = self.client.get('/api/history?difficulty=30')
        data = res.get_json()
        self.assertTrue(all(e['difficulty'] == 30 for e in data['history']))

    def test_new_game_with_seed(self):
        """New game with seed should be reproducible."""
        res1 = self.client.get('/api/new-game?difficulty=30&seed=test123')
        res2 = self.client.get('/api/new-game?difficulty=30&seed=test123')
        self.assertEqual(res1.get_json()['puzzle'], res2.get_json()['puzzle'])

    def test_new_game_different_seeds(self):
        """Different seeds should produce different puzzles."""
        res1 = self.client.get('/api/new-game?difficulty=30&seed=seed1')
        res2 = self.client.get('/api/new-game?difficulty=30&seed=seed2')
        self.assertNotEqual(res1.get_json()['puzzle'], res2.get_json()['puzzle'])

    def test_new_game_no_seed_different(self):
        """New game without seed should usually produce different puzzles."""
        puzzles = set()
        for _ in range(5):
            res = self.client.get('/api/new-game?difficulty=30')
            puzzles.add(str(res.get_json()['puzzle']))
        self.assertGreaterEqual(len(puzzles), 4)

    def test_daily_puzzle_same_result(self):
        """Daily puzzle should return same result on same day."""
        res1 = self.client.get('/api/daily-puzzle')
        res2 = self.client.get('/api/daily-puzzle')
        self.assertEqual(res1.get_json()['puzzle'], res2.get_json()['puzzle'])

    def test_weekly_puzzle_same_result(self):
        """Weekly puzzle should return same result on same week."""
        res1 = self.client.get('/api/weekly-puzzle')
        res2 = self.client.get('/api/weekly-puzzle')
        self.assertEqual(res1.get_json()['puzzle'], res2.get_json()['puzzle'])

    def test_compare_missing_a(self):
        """Compare with only b parameter should return 400."""
        self._create_games(1)
        games = self.client.get('/api/games').get_json()['games']
        gid = games[0]['game_id']
        res = self.client.get(f'/api/games/compare?b={gid}')
        self.assertEqual(res.status_code, 400)

    def test_compare_missing_b(self):
        """Compare with only a parameter should return 400."""
        self._create_games(1)
        games = self.client.get('/api/games').get_json()['games']
        gid = games[0]['game_id']
        res = self.client.get(f'/api/games/compare?a={gid}')
        self.assertEqual(res.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
