"""
Tests for API rate limiting and concurrent request handling.
"""
import json
import threading
import time
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestAPIResilience(unittest.TestCase):
    """Tests for API resilience under concurrent load."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_concurrent_create_games(self):
        """Multiple concurrent game creations should all succeed."""
        results = []
        errors = []

        def create_game():
            try:
                res = self.client.post('/api/games', data=json.dumps(
                    {'difficulty': 30, 'elapsed': 100}),
                    content_type='application/json')
                results.append(res.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=create_game) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)
        for code in results:
            self.assertEqual(code, 201)

    def test_concurrent_read_write(self):
        """Concurrent reads and writes should not interfere."""
        # Create a game first
        res = self.client.post('/api/games', data=json.dumps(
            {'difficulty': 30, 'elapsed': 100}),
            content_type='application/json')
        game_id = res.get_json()['game_id']

        errors = []

        def read_game():
            try:
                res = self.client.get(f'/api/games/{game_id}')
                if res.status_code != 200:
                    errors.append(f"Read failed: {res.status_code}")
            except Exception as e:
                errors.append(str(e))

        def write_game():
            try:
                self.client.put(f'/api/games/{game_id}', data=json.dumps(
                    {'elapsed': 200}),
                    content_type='application/json')
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=read_game))
            threads.append(threading.Thread(target=write_game))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_rapid_sequential_updates(self):
        """Rapid sequential updates should all apply."""
        res = self.client.post('/api/games', data=json.dumps(
            {'difficulty': 30, 'elapsed': 0}),
            content_type='application/json')
        game_id = res.get_json()['game_id']

        for i in range(20):
            self.client.put(f'/api/games/{game_id}', data=json.dumps(
                {'elapsed': i * 10}),
                content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.get_json()['elapsed'], 190)

    def test_delete_during_read(self):
        """Deleting a game while reading should not crash."""
        res = self.client.post('/api/games', data=json.dumps(
            {'difficulty': 30, 'elapsed': 100}),
            content_type='application/json')
        game_id = res.get_json()['game_id']

        errors = []

        def read_game():
            try:
                self.client.get(f'/api/games/{game_id}')
            except Exception as e:
                errors.append(str(e))

        def delete_game():
            try:
                self.client.delete(f'/api/games/{game_id}')
            except Exception as e:
                errors.append(str(e))

        t1 = threading.Thread(target=read_game)
        t2 = threading.Thread(target=delete_game)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)

    def test_stats_under_load(self):
        """Stats endpoint should handle multiple concurrent calls."""
        for _ in range(5):
            self.client.post('/api/games', data=json.dumps(
                {'difficulty': 30, 'elapsed': 100, 'completed': True}),
                content_type='application/json')

        results = []
        errors = []

        def get_stats():
            try:
                res = self.client.get('/api/stats')
                results.append(res.status_code)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=get_stats) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        for code in results:
            self.assertEqual(code, 200)

    def test_concurrent_different_games(self):
        """Concurrent operations on different games should not interfere."""
        game_ids = []
        for _ in range(3):
            res = self.client.post('/api/games', data=json.dumps(
                {'difficulty': 30, 'elapsed': 0}),
                content_type='application/json')
            game_ids.append(res.get_json()['game_id'])

        def update_game(gid, elapsed):
            self.client.put(f'/api/games/{gid}', data=json.dumps(
                {'elapsed': elapsed}),
                content_type='application/json')

        threads = []
        for i, gid in enumerate(game_ids):
            threads.append(threading.Thread(target=update_game, args=(gid, (i+1)*100)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for i, gid in enumerate(game_ids):
            res = self.client.get(f'/api/games/{gid}')
            self.assertEqual(res.get_json()['elapsed'], (i+1)*100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
