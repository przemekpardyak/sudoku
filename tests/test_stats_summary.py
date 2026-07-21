"""
Tests for the stats summary display in the games modal.
Verifies the /api/stats endpoint returns everything the UI needs.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestStatsSummary(unittest.TestCase):
    """Tests for stats summary data used by the games modal."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_stats_returns_all_fields_for_ui(self):
        """Stats should return all fields needed by the UI summary."""
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 30, 'elapsed': 100, 'completed': True}),
            content_type='application/json')
        res = self.client.get('/api/stats')
        stats = res.get_json()
        required_fields = [
            'total_games', 'completed_games', 'best_time',
            'by_difficulty'
        ]
        for field in required_fields:
            self.assertIn(field, stats, f"Missing field: {field}")

    def test_by_difficulty_has_completed_total(self):
        """Each difficulty entry should have completed and total."""
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 30, 'elapsed': 50, 'completed': True}),
            content_type='application/json')
        res = self.client.get('/api/stats')
        stats = res.get_json()
        easy = stats['by_difficulty']['easy']
        self.assertIn('completed', easy)
        self.assertIn('total', easy)
        self.assertEqual(easy['total'], 1)
        self.assertEqual(easy['completed'], 1)

    def test_best_time_display(self):
        """Best time should be a number for display."""
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 30, 'elapsed': 120, 'completed': True}),
            content_type='application/json')
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertIsInstance(stats['best_time'], int)
        self.assertEqual(stats['best_time'], 120)

    def test_empty_stats_display(self):
        """When no games, stats should return zeros for UI display."""
        res = self.client.get('/api/stats')
        stats = res.get_json()
        self.assertEqual(stats['total_games'], 0)
        self.assertEqual(stats['completed_games'], 0)
        self.assertEqual(stats['best_time'], 0)

    def test_by_difficulty_only_shows_nonzero(self):
        """UI should be able to filter out difficulty levels with 0 games."""
        self.client.post('/api/games', data=json.dumps(
            {'difficulty': 40, 'elapsed': 100}),
            content_type='application/json')
        res = self.client.get('/api/stats')
        stats = res.get_json()
        # Easy should have 0 total
        self.assertEqual(stats['by_difficulty']['easy']['total'], 0)
        # Medium should have 1
        self.assertEqual(stats['by_difficulty']['medium']['total'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
