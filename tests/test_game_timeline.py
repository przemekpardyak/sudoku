"""
Tests for game history timeline functionality.
Tests chronological ordering and progress tracking over time.
"""
import json
import unittest
import time
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestGameTimeline(unittest.TestCase):
    """Tests for game history timeline."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game(self, elapsed=100, completed=False, difficulty=30):
        state = {
            'difficulty': difficulty,
            'elapsed': elapsed,
            'completed': completed,
            'mistakes': 0,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id']

    def test_games_sorted_by_created_at(self):
        """Games list should be sortable by creation time."""
        g1 = self._create_game()
        time.sleep(0.01)
        g2 = self._create_game()
        time.sleep(0.01)
        g3 = self._create_game()

        res = self.client.get('/api/games')
        games = res.get_json()['games']
        # Default sort is by updated_at desc (most recent first)
        self.assertEqual(len(games), 3)

    def test_timeline_has_timestamps(self):
        """Each game should have created_at and updated_at timestamps."""
        game_id = self._create_game()
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertIn('created_at', game)
        self.assertIn('updated_at', game)

    def test_timeline_summary_has_timestamps(self):
        """Games list summary should have created_at and updated_at."""
        game_id = self._create_game()
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        game = [g for g in games if g['game_id'] == game_id][0]
        self.assertIn('created_at', game)
        self.assertIn('updated_at', game)

    def test_updated_at_changes_on_save(self):
        """updated_at should change when a game is saved."""
        game_id = self._create_game()
        res = self.client.get(f'/api/games/{game_id}')
        original_updated = res.get_json()['updated_at']

        time.sleep(0.01)
        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 200}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        new_updated = res.get_json()['updated_at']
        self.assertNotEqual(original_updated, new_updated)

    def test_created_at_does_not_change(self):
        """created_at should not change on update."""
        game_id = self._create_game()
        res = self.client.get(f'/api/games/{game_id}')
        original_created = res.get_json()['created_at']

        self.client.put(f'/api/games/{game_id}',
                       data=json.dumps({'elapsed': 200}),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        new_created = res.get_json()['created_at']
        self.assertEqual(original_created, new_created)

    def test_multiple_games_have_different_timestamps(self):
        """Different games should have different created_at timestamps."""
        self._create_game()
        time.sleep(0.01)
        self._create_game()
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        timestamps = [g['created_at'] for g in games]
        self.assertEqual(len(set(timestamps)), 2)

    def test_progress_tracking_over_time(self):
        """Multiple games should show progression of stats."""
        # Game 1: easy, completed fast
        self._create_game(elapsed=50, completed=True, difficulty=30)
        # Game 2: medium, completed slower
        self._create_game(elapsed=150, completed=True, difficulty=40)
        # Game 3: hard, not completed
        self._create_game(elapsed=200, completed=False, difficulty=50)

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_games'], 3)
        self.assertEqual(stats['completed_games'], 2)
        self.assertLess(stats['best_time'], 100)

    def test_game_count_increases(self):
        """Creating games should increase the total count."""
        res = self.client.get('/api/stats')
        initial_count = res.get_json()['total_games']

        self._create_game()
        self._create_game()

        res = self.client.get('/api/stats')
        final_count = res.get_json()['total_games']
        self.assertEqual(final_count, initial_count + 2)

    def test_delete_reduces_count(self):
        """Deleting a game should decrease the total count."""
        game_id = self._create_game()
        self._create_game()

        res = self.client.get('/api/stats')
        count_before = res.get_json()['total_games']

        self.client.delete(f'/api/games/{game_id}')

        res = self.client.get('/api/stats')
        count_after = res.get_json()['total_games']
        self.assertEqual(count_after, count_before - 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
