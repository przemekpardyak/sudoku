"""
Tests for the enhanced stats endpoint — best_time, avg_mistakes, total_hints.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestEnhancedStats(unittest.TestCase):
    """Tests for enhanced stats fields."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_best_time_with_no_completed(self):
        """best_time should be 0 when no games are completed."""
        state = {'difficulty': 40, 'elapsed': 100, 'completed': False}
        self.client.post('/api/games', data=json.dumps(state),
                         content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['best_time'], 0)

    def test_best_time_with_completed(self):
        """best_time should return the fastest completion time."""
        # Completed game with time 120
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 120, 'completed': True}),
            content_type='application/json')
        # Completed game with time 60 (faster)
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 60, 'completed': True}),
            content_type='application/json')
        # Incomplete game (should not count)
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 10, 'completed': False}),
            content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['best_time'], 60)

    def test_avg_mistakes_with_completed(self):
        """avg_mistakes should be the average mistakes per completed game."""
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 100, 'completed': True, 'mistakes': 5}),
            content_type='application/json')
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 200, 'completed': True, 'mistakes': 15}),
            content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['avg_mistakes'], 10.0)

    def test_avg_mistakes_no_completed(self):
        """avg_mistakes should be 0 when no games are completed."""
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 100, 'completed': False, 'mistakes': 5}),
            content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['avg_mistakes'], 0)

    def test_total_hints_sum(self):
        """total_hints should sum hintsUsed across all games."""
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'hintsUsed': 3}),
            content_type='application/json')
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'hintsUsed': 7}),
            content_type='application/json')

        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_hints'], 10)

    def test_stats_empty(self):
        """Stats with no games should return zeros."""
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_games'], 0)
        self.assertEqual(stats['completed_games'], 0)
        self.assertEqual(stats['best_time'], 0)
        self.assertEqual(stats['avg_mistakes'], 0)
        self.assertEqual(stats['total_hints'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
