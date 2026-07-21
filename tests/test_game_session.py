"""
Tests for game session tracking.
Tests start_time and end_time fields for tracking play sessions.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameSession(unittest.TestCase):
    """Tests for game session tracking."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, **kwargs):
        state = {'difficulty': 40, 'elapsed': 100, **kwargs}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_session_start_time_stored(self):
        """session_start should be stored when provided."""
        game_id = self._create_game(session_start='2026-07-21T10:00:00Z')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['session_start'], '2026-07-21T10:00:00Z')

    def test_session_end_time_stored(self):
        """session_end should be stored when provided."""
        game_id = self._create_game(session_end='2026-07-21T10:30:00Z')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['session_end'], '2026-07-21T10:30:00Z')

    def test_update_session_start(self):
        """session_start should be updatable via PUT."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'session_start': '2026-07-21T11:00:00Z'}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['session_start'], '2026-07-21T11:00:00Z')

    def test_update_session_end(self):
        """session_end should be updatable via PUT."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'session_end': '2026-07-21T11:30:00Z'}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['session_end'], '2026-07-21T11:30:00Z')

    def test_session_times_preserve_other_fields(self):
        """Updating session times should not clear other fields."""
        game_id = self._create_game(elapsed=200)
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'session_start': '2026-07-21T12:00:00Z'}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['session_start'], '2026-07-21T12:00:00Z')
        self.assertEqual(game['elapsed'], 200)

    def test_session_not_in_summary(self):
        """Session times should not be in list summary (too detailed)."""
        game_id = self._create_game(session_start='2026-07-21T10:00:00Z')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        # Session times are full-game fields, not summary fields
        self.assertNotIn('session_start', game)

    def test_both_session_times(self):
        """Both session_start and session_end can be set together."""
        game_id = self._create_game()
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({
                           'session_start': '2026-07-21T10:00:00Z',
                           'session_end': '2026-07-21T10:45:00Z',
                       }),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['session_start'], '2026-07-21T10:00:00Z')
        self.assertEqual(game['session_end'], '2026-07-21T10:45:00Z')


if __name__ == '__main__':
    unittest.main(verbosity=2)
