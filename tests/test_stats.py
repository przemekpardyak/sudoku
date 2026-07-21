"""
Tests for the /api/stats endpoint — player statistics.
Also tests DELETE /api/games (clear all games).
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestStats(unittest.TestCase):
    """Tests for player statistics."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_empty_stats(self):
        """Stats with no games should show zeros."""
        res = self.client.get('/api/stats')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['total_games'], 0)
        self.assertEqual(data['completed_games'], 0)
        self.assertEqual(data['total_time'], 0)

    def test_stats_with_games(self):
        """Stats should count all games."""
        for i in range(3):
            state = {
                'difficulty': 30 + i * 10,
                'mistakes': i,
                'elapsed': (i + 1) * 100,
                'completed': i == 2,  # only last one completed
            }
            self.client.post('/api/games', data=json.dumps(state),
                            content_type='application/json')

        res = self.client.get('/api/stats')
        data = res.get_json()
        self.assertEqual(data['total_games'], 3)
        self.assertEqual(data['completed_games'], 1)
        self.assertEqual(data['total_time'], 600)  # 100+200+300

    def test_stats_completion_rate(self):
        """Completion rate should be completed/total."""
        for i in range(4):
            state = {
                'difficulty': 40,
                'mistakes': 0,
                'elapsed': 60,
                'completed': i < 2,  # 2 of 4 completed
            }
            self.client.post('/api/games', data=json.dumps(state),
                            content_type='application/json')

        res = self.client.get('/api/stats')
        data = res.get_json()
        self.assertEqual(data['total_games'], 4)
        self.assertEqual(data['completed_games'], 2)
        self.assertAlmostEqual(data['completion_rate'], 0.5)

    def test_stats_total_mistakes(self):
        """Stats should sum total mistakes across all games."""
        for i in range(3):
            state = {
                'difficulty': 40,
                'mistakes': i + 1,  # 1, 2, 3
                'elapsed': 100,
                'completed': False,
            }
            self.client.post('/api/games', data=json.dumps(state),
                            content_type='application/json')

        res = self.client.get('/api/stats')
        data = res.get_json()
        self.assertEqual(data['total_mistakes'], 6)

    def test_stats_avg_time_completed(self):
        """Stats should show average time for completed games."""
        for t in [100, 200, 300]:
            state = {
                'difficulty': 40, 'mistakes': 0, 'elapsed': t, 'completed': True
            }
            self.client.post('/api/games', data=json.dumps(state),
                            content_type='application/json')

        res = self.client.get('/api/stats')
        data = res.get_json()
        self.assertEqual(data['avg_completion_time'], 200)


class TestClearAllGames(unittest.TestCase):
    """Tests for DELETE /api/games — clear all games."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_delete_all_with_no_games(self):
        """Deleting when no games exist should return 0."""
        res = self.client.delete('/api/games')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['deleted_count'], 0)

    def test_delete_all_removes_all_games(self):
        """Deleting should remove all games."""
        for i in range(5):
            self.client.post('/api/games',
                            data=json.dumps({'difficulty': 40, 'mistakes': i}),
                            content_type='application/json')

        res = self.client.delete('/api/games')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['deleted_count'], 5)

        # Verify empty
        res = self.client.get('/api/games')
        self.assertEqual(len(res.get_json()['games']), 0)

    def test_delete_all_then_create_works(self):
        """Should be able to create games after clearing all."""
        self.client.post('/api/games',
                        data=json.dumps({'difficulty': 40}),
                        content_type='application/json')
        self.client.delete('/api/games')

        res = self.client.post('/api/games',
                              data=json.dumps({'difficulty': 30}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 201)


if __name__ == '__main__':
    unittest.main(verbosity=2)
