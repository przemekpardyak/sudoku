"""
Tests for the game rating endpoint.
Users can rate completed games 1-5 stars.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameRating(unittest.TestCase):
    """Tests for the game rating API endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, completed=False):
        state = {'difficulty': 40, 'elapsed': 100, 'completed': completed}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_rate_completed_game(self):
        """Rating a completed game should work."""
        game_id = self._create_game(completed=True)
        res = self.client.put(f'/api/games/{game_id}/rate',
                            data=json.dumps({'rating': 5}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['rating'], 5)

    def test_rate_incomplete_game(self):
        """Rating an incomplete game should return 400."""
        game_id = self._create_game(completed=False)
        res = self.client.put(f'/api/games/{game_id}/rate',
                            data=json.dumps({'rating': 3}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_rate_nonexistent_game(self):
        """Rating a nonexistent game should return 404."""
        res = self.client.put('/api/games/nonexistent/rate',
                            data=json.dumps({'rating': 3}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_rating_too_low(self):
        """Rating below 1 should return 400."""
        game_id = self._create_game(completed=True)
        res = self.client.put(f'/api/games/{game_id}/rate',
                            data=json.dumps({'rating': 0}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_rating_too_high(self):
        """Rating above 5 should return 400."""
        game_id = self._create_game(completed=True)
        res = self.client.put(f'/api/games/{game_id}/rate',
                            data=json.dumps({'rating': 6}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_rating_missing_field(self):
        """Missing rating field should return 400."""
        game_id = self._create_game(completed=True)
        res = self.client.put(f'/api/games/{game_id}/rate',
                            data=json.dumps({}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_rating_appears_in_list(self):
        """Rating should appear in the games list."""
        game_id = self._create_game(completed=True)
        self.client.put(f'/api/games/{game_id}/rate',
                       data=json.dumps({'rating': 4}),
                       content_type='application/json')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertEqual(game['rating'], 4)

    def test_rating_default_zero(self):
        """Games without a rating should show 0 in the list."""
        game_id = self._create_game(completed=True)
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertEqual(game['rating'], 0)

    def test_update_rating(self):
        """Rating can be updated."""
        game_id = self._create_game(completed=True)
        self.client.put(f'/api/games/{game_id}/rate',
                       data=json.dumps({'rating': 3}),
                       content_type='application/json')
        res = self.client.put(f'/api/games/{game_id}/rate',
                            data=json.dumps({'rating': 5}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['rating'], 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
