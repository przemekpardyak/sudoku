"""
Tests for the game archive/unarchive API endpoint.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestArchiveGame(unittest.TestCase):
    """Tests for the archive/unarchive endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self):
        state = {'difficulty': 40, 'elapsed': 100, 'completed': False}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_archive_game(self):
        """Archiving a game should set archived=True."""
        game_id = self._create_game()
        res = self.client.put(f'/api/games/{game_id}/archive',
                            data=json.dumps({'archived': True}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['archived'])

    def test_unarchive_game(self):
        """Unarchiving a game should set archived=False."""
        game_id = self._create_game()
        # Archive first
        self.client.put(f'/api/games/{game_id}/archive',
                       data=json.dumps({'archived': True}),
                       content_type='application/json')
        # Unarchive
        res = self.client.put(f'/api/games/{game_id}/archive',
                            data=json.dumps({'archived': False}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.get_json()['archived'])

    def test_archive_default_true(self):
        """Default archive action (no body) should set archived=True."""
        game_id = self._create_game()
        res = self.client.put(f'/api/games/{game_id}/archive',
                            content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['archived'])

    def test_archive_nonexistent_game(self):
        """Archiving a nonexistent game should return 404."""
        res = self.client.put('/api/games/nonexistent-id/archive',
                            data=json.dumps({'archived': True}),
                            content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_archived_field_in_list(self):
        """Archived games should show archived=True in list."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}/archive',
                       data=json.dumps({'archived': True}),
                       content_type='application/json')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        archived_game = [g for g in games if g['game_id'] == game_id][0]
        self.assertTrue(archived_game['archived'])

    def test_not_archived_by_default(self):
        """New games should not be archived by default."""
        game_id = self._create_game()
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertFalse(game['archived'])

    def test_archived_game_still_accessible(self):
        """An archived game should still be accessible via get_game."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}/archive',
                       data=json.dumps({'archived': True}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 200)
        game = res.get_json()
        self.assertTrue(game.get('archived', False))


if __name__ == '__main__':
    unittest.main(verbosity=2)
