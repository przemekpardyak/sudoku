"""
Tests for win detection and board check functionality.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
from sudoku import generate_puzzle, _solve
import storage as storage_module


class TestWinDetection(unittest.TestCase):
    """Tests for game completion detection."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_completed_game_saved_with_completed_flag(self):
        """A completed game should be saved with completed=True."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'board': solution,
            'solution': solution,
            'given': [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)],
            'notes': [[[False] * 9 for _ in range(9)] for _ in range(9)],
            'undoStack': [], 'redoStack': [],
            'mistakes': 0, 'elapsed': 120, 'difficulty': 30, 'completed': True,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertTrue(game['completed'])

    def test_incomplete_game_saved_with_completed_false(self):
        """An incomplete game should be saved with completed=False."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'board': puzzle,  # Not solved
            'solution': solution,
            'difficulty': 30, 'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertFalse(game['completed'])

    def test_completed_game_shows_in_list(self):
        """Completed games should be visible in the games list."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle,
            'board': solution,
            'difficulty': 30, 'completed': True, 'elapsed': 60,
        }
        self.client.post('/api/games', data=json.dumps(state),
                         content_type='application/json')

        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertEqual(len(games), 1)
        self.assertTrue(games[0]['completed'])

    def test_best_times_only_completed(self):
        """Best times should only count completed games."""
        puzzle, solution = generate_puzzle(difficulty=30)
        # Completed game with time 60
        state1 = {
            'puzzle': puzzle, 'board': solution,
            'difficulty': 30, 'completed': True, 'elapsed': 60,
        }
        self.client.post('/api/games', data=json.dumps(state1),
                         content_type='application/json')

        # Incomplete game with time 10 (should not count)
        state2 = {
            'puzzle': puzzle, 'board': puzzle,
            'difficulty': 30, 'completed': False, 'elapsed': 10,
        }
        self.client.post('/api/games', data=json.dumps(state2),
                         content_type='application/json')

        res = self.client.get('/api/best-times')
        best = res.get_json()
        self.assertIn('30', best)
        self.assertEqual(best['30'], 60)

    def test_update_game_to_completed(self):
        """Updating a game to completed should persist the flag."""
        puzzle, solution = generate_puzzle(difficulty=30)
        state = {
            'puzzle': puzzle, 'board': puzzle,
            'difficulty': 30, 'completed': False, 'elapsed': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Update to completed
        update = {
            'puzzle': puzzle, 'board': solution,
            'difficulty': 30, 'completed': True, 'elapsed': 120,
        }
        self.client.put(f'/api/games/{game_id}', data=json.dumps(update),
                       content_type='application/json')

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertTrue(game['completed'])
        self.assertEqual(game['elapsed'], 120)

    def test_completed_game_board_matches_solution(self):
        """A completed game's board should match the solution."""
        puzzle, solution = generate_puzzle(difficulty=40)
        state = {
            'puzzle': puzzle, 'board': solution, 'solution': solution,
            'difficulty': 40, 'completed': True, 'elapsed': 300,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['board'], game['solution'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
