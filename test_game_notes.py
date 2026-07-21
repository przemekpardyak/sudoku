"""
Tests for game notes functionality.
Users can add text notes to games for personal reminders.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameNotes(unittest.TestCase):
    """Tests for game notes."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, notes=None):
        state = {'difficulty': 40, 'elapsed': 100}
        if notes is not None:
            state['notes'] = notes
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_notes_stored_and_retrieved(self):
        """Notes should be stored and retrieved with the game."""
        game_id = self._create_game(notes='Hard puzzle, took forever')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['notes'], 'Hard puzzle, took forever')

    def test_notes_in_list(self):
        """Notes should appear in the games list summary."""
        game_id = self._create_game(notes='My note')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertEqual(game['notes'], 'My note')

    def test_update_notes(self):
        """Notes should be updatable via PUT."""
        game_id = self._create_game(notes='old note')
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'notes': 'new note'}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['notes'], 'new note')

    def test_empty_notes_by_default(self):
        """Games without notes should have empty string."""
        game_id = self._create_game()
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json().get('notes', ''), '')

    def test_clear_notes(self):
        """Notes can be cleared by setting to empty string."""
        game_id = self._create_game(notes='some note')
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'notes': ''}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['notes'], '')

    def test_long_notes(self):
        """Long notes should be stored without truncation."""
        long_note = 'A' * 500
        game_id = self._create_game(notes=long_note)
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(len(res.get_json()['notes']), 500)

    def test_notes_preserve_other_fields(self):
        """Adding notes should not clear other fields."""
        game_id = self._create_game(notes='test')
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'notes': 'updated', 'elapsed': 200}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['notes'], 'updated')
        self.assertEqual(game['elapsed'], 200)
        self.assertEqual(game['difficulty'], 40)


if __name__ == '__main__':
    unittest.main(verbosity=2)
