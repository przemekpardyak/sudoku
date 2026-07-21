"""
Tests for the progress tracking API — progress percentage in game summaries.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module


class TestProgressTracking(unittest.TestCase):
    """Tests for progress tracking in game summaries."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_fresh_game_progress_zero(self):
        """A fresh game should show 0/N progress (no cells filled by user)."""
        puzzle = [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                  [0, 3, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6
        board = [row[:] for row in puzzle]
        state = {
            'puzzle': puzzle,
            'board': board,
            'difficulty': 40, 'mistakes': 0, 'elapsed': 0, 'completed': False,
        }
        self.client.post('/api/games', data=json.dumps(state),
                         content_type='application/json')

        res = self.client.get('/api/games')
        game = res.get_json()['games'][0]
        self.assertTrue(game['progress'].startswith('0/'))

    def test_partial_progress(self):
        """A partially solved game should show filled/total format."""
        puzzle = [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                  [0, 3, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6
        board = [row[:] for row in puzzle]
        board[0][1] = 7  # user fills one cell
        state = {
            'puzzle': puzzle,
            'board': board,
            'difficulty': 40, 'mistakes': 0, 'elapsed': 10, 'completed': False,
        }
        self.client.post('/api/games', data=json.dumps(state),
                         content_type='application/json')

        res = self.client.get('/api/games')
        game = res.get_json()['games'][0]
        # Should show 1/N (1 cell filled by user out of N empty)
        self.assertTrue(game['progress'].startswith('1/'))

    def test_completed_game_progress_full(self):
        """A completed game should show N/N progress."""
        puzzle = [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                  [0, 3, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6
        solution = [[5, 7, 1, 2, 4, 3, 6, 8, 9],
                    [8, 3, 2, 5, 7, 9, 1, 4, 6],
                    [4, 6, 9, 1, 2, 8, 3, 5, 7]] + [[1] * 9] * 6
        state = {
            'puzzle': puzzle,
            'board': solution,
            'difficulty': 40, 'mistakes': 0, 'elapsed': 300, 'completed': True,
        }
        self.client.post('/api/games', data=json.dumps(state),
                         content_type='application/json')

        res = self.client.get('/api/games')
        game = res.get_json()['games'][0]
        parts = game['progress'].split('/')
        self.assertEqual(parts[0], parts[1], "Completed game should have N/N progress")


if __name__ == '__main__':
    unittest.main(verbosity=2)
