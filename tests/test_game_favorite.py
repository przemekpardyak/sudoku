"""
Tests for game favorite/bookmark functionality.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameFavorite(unittest.TestCase):
    """Tests for game favorite toggle."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self):
        res = self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 100}),
            content_type='application/json')
        return res.get_json()['game_id']

    def test_favorite_game(self):
        """Can favorite a game via PUT."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'favorite': True}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertTrue(res.get_json()['favorite'])

    def test_unfavorite_game(self):
        """Can unfavorite a game."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'favorite': True}),
                       content_type='application/json')
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'favorite': False}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertFalse(res.get_json()['favorite'])

    def test_not_favorite_by_default(self):
        """Games should not be favorited by default."""
        game_id = self._create_game()
        res = self.client.get(f'/api/games/{game_id}')
        self.assertFalse(res.get_json().get('favorite', False))

    def test_favorite_in_list(self):
        """Favorite should appear in list."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'favorite': True}),
                       content_type='application/json')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertTrue(game['favorite'])

    def test_favorite_preserves_other_fields(self):
        """Favoriting should not clear other fields."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'favorite': True, 'elapsed': 200}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertTrue(game['favorite'])
        self.assertEqual(game['elapsed'], 200)
        self.assertEqual(game['difficulty'], 40)

    def test_filter_favorites(self):
        """Can filter favorites from the games list."""
        g1 = self._create_game()
        self._create_game()
        self.client.put(f'/api/games/{g1}',
                       data=json.dumps({'favorite': True}),
                       content_type='application/json')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        favorites = [g for g in games if g.get('favorite')]
        non_favorites = [g for g in games if not g.get('favorite')]
        self.assertEqual(len(favorites), 1)
        self.assertEqual(len(non_favorites), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
