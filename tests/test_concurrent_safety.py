"""
Tests for concurrent game operations and race conditions.
Tests that simultaneous operations don't corrupt data.
"""
import json
import threading
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestConcurrentSafety(unittest.TestCase):
    """Tests for concurrent operation safety."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_concurrent_creates_all_succeed(self):
        """Concurrent game creates should all produce unique IDs."""
        ids = []
        errors = []
        lock = threading.Lock()

        def create_game():
            try:
                res = self.client.post('/api/games', data=json.dumps({
                    'difficulty': 30, 'elapsed': 100,
                }), content_type='application/json')
                with lock:
                    ids.append(res.get_json()['game_id'])
            except Exception as e:
                with lock:
                    errors.append(str(e))

        threads = [threading.Thread(target=create_game) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(ids), 20)
        self.assertEqual(len(set(ids)), 20)  # All unique

    def test_concurrent_reads_during_write(self):
        """Concurrent reads during a write should not crash."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        errors = []

        def read_game():
            try:
                self.client.get(f'/api/games/{game_id}')
            except Exception as e:
                errors.append(str(e))

        def write_game():
            try:
                self.client.put(f'/api/games/{game_id}', data=json.dumps({
                    'elapsed': 200,
                }), content_type='application/json')
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(10):
            threads.append(threading.Thread(target=read_game))
            threads.append(threading.Thread(target=write_game))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_concurrent_updates_different_fields(self):
        """Concurrent updates to different fields should merge."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100, 'mistakes': 0,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        # Sequential updates to different fields
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'elapsed': 200,
        }), content_type='application/json')
        self.client.put(f'/api/games/{game_id}', data=json.dumps({
            'mistakes': 5,
        }), content_type='application/json')

        game = self.client.get(f'/api/games/{game_id}').get_json()
        self.assertEqual(game['elapsed'], 200)
        self.assertEqual(game['mistakes'], 5)

    def test_concurrent_deletes_safely(self):
        """Concurrent deletes of the same game should not crash."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        errors = []

        def delete_game():
            try:
                self.client.delete(f'/api/games/{game_id}')
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=delete_game) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        # Game should be gone
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 404)

    def test_concurrent_stats_and_create(self):
        """Stats should work during concurrent game creation."""
        errors = []

        def create_and_stats():
            try:
                self.client.post('/api/games', data=json.dumps({
                    'difficulty': 30, 'completed': True, 'elapsed': 100,
                }), content_type='application/json')
                self.client.get('/api/stats')
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=create_and_stats) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        stats = self.client.get('/api/stats').get_json()
        self.assertEqual(stats['total_games'], 10)

    def test_concurrent_leaderboard_and_create(self):
        """Leaderboard should work during concurrent creates."""
        # Create some initial games
        for i in range(5):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': 100 + i * 20,
            }), content_type='application/json')

        errors = []

        def read_leaderboard():
            try:
                self.client.get('/api/leaderboard')
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_leaderboard) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_concurrent_profile_reads(self):
        """Profile reads should work concurrently."""
        for _ in range(3):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30, 'completed': True, 'elapsed': 100,
            }), content_type='application/json')

        errors = []

        def read_profile():
            try:
                self.client.get('/api/profile')
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_profile) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_delete_all_during_list(self):
        """Delete all during a list operation should not crash."""
        for _ in range(10):
            self.client.post('/api/games', data=json.dumps({
                'difficulty': 30,
            }), content_type='application/json')

        errors = []

        def list_games():
            try:
                self.client.get('/api/games')
            except Exception as e:
                errors.append(str(e))

        def delete_all():
            try:
                self.client.delete('/api/games')
            except Exception as e:
                errors.append(str(e))

        t1 = threading.Thread(target=list_games)
        t2 = threading.Thread(target=delete_all)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
