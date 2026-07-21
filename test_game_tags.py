"""
Tests for game tags functionality.
Users can add custom tags to games for organization.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameTags(unittest.TestCase):
    """Tests for game tagging."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, tags=None):
        state = {'difficulty': 40, 'elapsed': 100}
        if tags:
            state['tags'] = tags
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_tags_in_game_state(self):
        """Tags should be stored and retrieved with the game."""
        game_id = self._create_game(tags=['favorite', 'hard'])
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertIn('tags', game)
        self.assertEqual(set(game['tags']), {'favorite', 'hard'})

    def test_tags_in_list(self):
        """Tags should appear in the games list summary."""
        game_id = self._create_game(tags=['daily'])
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertIn('tags', game)
        self.assertIn('daily', game['tags'])

    def test_update_tags(self):
        """Tags should be updatable via PUT."""
        game_id = self._create_game(tags=['old'])
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'tags': ['new', 'updated']}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(set(game['tags']), {'new', 'updated'})

    def test_empty_tags_by_default(self):
        """Games without tags should have an empty list."""
        game_id = self._create_game()
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game.get('tags', []), [])

    def test_add_tag_via_merge(self):
        """Adding tags via PUT should merge, not replace other fields."""
        game_id = self._create_game(tags=['a'])
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'tags': ['a', 'b'], 'elapsed': 200}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(set(game['tags']), {'a', 'b'})
        self.assertEqual(game['elapsed'], 200)

    def test_clear_tags(self):
        """Tags can be cleared by setting to empty list."""
        game_id = self._create_game(tags=['x', 'y'])
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'tags': []}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['tags'], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
