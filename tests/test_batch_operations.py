"""
Tests for batch game operations.
Tests bulk delete, bulk archive, and batch stats.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestBatchOperations(unittest.TestCase):
    """Tests for batch game operations."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_games(self, count=5):
        ids = []
        for _ in range(count):
            res = self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'elapsed': 100, 'completed': True,
            }), content_type='application/json')
            ids.append(res.get_json()['game_id'])
        return ids

    def test_delete_all_games(self):
        """Delete all games should remove everything."""
        self._create_games(5)
        res = self.client.delete('/api/games')
        self.assertEqual(res.status_code, 200)
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 0)

    def test_delete_all_resets_stats(self):
        """After deleting all games, stats should be zero."""
        self._create_games(3)
        self.client.delete('/api/games')
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_games'], 0)
        self.assertEqual(stats['completed_games'], 0)

    def test_delete_all_resets_leaderboard(self):
        """After deleting all, leaderboard should be empty."""
        self._create_games(3)
        self.client.delete('/api/games')
        res = self.client.get('/api/leaderboard')
        self.assertEqual(res.get_json()['count'], 0)

    def test_delete_all_resets_streaks(self):
        """After deleting all, streaks should be zero."""
        self._create_games(3)
        self.client.delete('/api/games')
        res = self.client.get('/api/streaks')
        data = res.get_json()
        self.assertEqual(data['current_streak'], 0)
        self.assertEqual(data['best_streak'], 0)

    def test_delete_all_resets_history(self):
        """After deleting all, history should be empty."""
        self._create_games(3)
        self.client.delete('/api/games')
        res = self.client.get('/api/history')
        self.assertEqual(res.get_json()['count'], 0)

    def test_individual_delete_preserves_others(self):
        """Deleting one game should not affect others."""
        ids = self._create_games(3)
        self.client.delete(f'/api/games/{ids[0]}')
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertEqual(len(games), 2)
        remaining_ids = [g['game_id'] for g in games]
        self.assertNotIn(ids[0], remaining_ids)
        self.assertIn(ids[1], remaining_ids)
        self.assertIn(ids[2], remaining_ids)

    def test_create_multiple_games_in_sequence(self):
        """Multiple sequential creates should all succeed with unique IDs."""
        ids = self._create_games(10)
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)  # All unique

    def test_stats_after_partial_deletion(self):
        """Stats should reflect remaining games after partial deletion."""
        ids = self._create_games(5)
        self.client.delete(f'/api/games/{ids[0]}')
        self.client.delete(f'/api/games/{ids[1]}')
        res = self.client.get('/api/stats')
        self.assertEqual(res.get_json()['total_games'], 3)

    def test_leaderboard_after_partial_deletion(self):
        """Leaderboard should only show remaining games."""
        ids = self._create_games(5)
        # Delete the fastest game
        self.client.delete(f'/api/games/{ids[0]}')
        res = self.client.get('/api/leaderboard')
        self.assertEqual(res.get_json()['count'], 4)

    def test_streaks_after_partial_deletion(self):
        """Streaks should recalculate after deletion."""
        ids = self._create_games(3)
        self.client.delete(f'/api/games/{ids[1]}')
        res = self.client.get('/api/streaks')
        data = res.get_json()
        # Should have 2 completions (deleted one in the middle)
        self.assertEqual(data['total_completions'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
