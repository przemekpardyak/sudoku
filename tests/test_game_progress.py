"""
Tests for game progress tracking endpoint.
Tests /api/games/<id>/progress which returns detailed progress metrics.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestGameProgress(unittest.TestCase):
    """Tests for game progress endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def _create_game_with_board(self, puzzle=None, solution=None, board=None):
        if puzzle is None:
            puzzle, solution = generate_puzzle(difficulty=30)
        if board is None:
            board = copy.deepcopy(puzzle)
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': board,
            'difficulty': 30,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        return res.get_json()['game_id'], puzzle, solution

    def test_progress_fresh_game(self):
        """Fresh game should have 0% progress."""
        game_id, puzzle, solution = self._create_game_with_board()
        res = self.client.get(f'/api/games/{game_id}/progress')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['filled'], 0)
        self.assertEqual(data['total_empty'], 81 - sum(1 for r in range(9) for c in range(9) if puzzle[r][c] != 0))
        self.assertEqual(data['progress_pct'], 0)

    def test_progress_partial_game(self):
        """Partially filled game should show partial progress."""
        game_id, puzzle, solution = self._create_game_with_board()
        # Fill 5 cells
        board = copy.deepcopy(puzzle)
        filled = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and filled < 5:
                    board[r][c] = solution[r][c]
                    filled += 1
        self.client.put(f'/api/games/{game_id}', data=json.dumps({'board': board}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}/progress')
        data = res.get_json()
        self.assertEqual(data['filled'], 5)
        self.assertGreater(data['progress_pct'], 0)
        self.assertLess(data['progress_pct'], 100)

    def test_progress_completed_game(self):
        """Completed game should show 100% progress."""
        puzzle, solution = generate_puzzle(difficulty=30)
        game_id, _, _ = self._create_game_with_board(
            puzzle=puzzle, solution=solution, board=copy.deepcopy(solution))
        res = self.client.get(f'/api/games/{game_id}/progress')
        data = res.get_json()
        self.assertEqual(data['progress_pct'], 100)

    def test_progress_has_correct_fields(self):
        """Progress should have all required fields."""
        game_id, _, _ = self._create_game_with_board()
        res = self.client.get(f'/api/games/{game_id}/progress')
        data = res.get_json()
        self.assertIn('filled', data)
        self.assertIn('total_cells', data)
        self.assertIn('total_empty', data)
        self.assertIn('progress_pct', data)
        self.assertIn('correct', data)
        self.assertIn('incorrect', data)

    def test_progress_tracks_correct_cells(self):
        """Progress should track how many cells match the solution."""
        game_id, puzzle, solution = self._create_game_with_board()
        # Fill 3 correct cells
        board = copy.deepcopy(puzzle)
        count = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and count < 3:
                    board[r][c] = solution[r][c]
                    count += 1
        self.client.put(f'/api/games/{game_id}', data=json.dumps({'board': board}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}/progress')
        data = res.get_json()
        self.assertEqual(data['correct'], 3)
        self.assertEqual(data['incorrect'], 0)

    def test_progress_tracks_incorrect_cells(self):
        """Progress should track incorrect cells."""
        game_id, puzzle, solution = self._create_game_with_board()
        # Fill 2 incorrect cells
        board = copy.deepcopy(puzzle)
        count = 0
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and count < 2:
                    # Put wrong value (not the solution)
                    wrong = solution[r][c] % 9 + 1
                    if wrong == solution[r][c]:
                        wrong = solution[r][c] + 1 if solution[r][c] < 9 else 1
                    board[r][c] = wrong
                    count += 1
        self.client.put(f'/api/games/{game_id}', data=json.dumps({'board': board}),
                       content_type='application/json')
        res = self.client.get(f'/api/games/{game_id}/progress')
        data = res.get_json()
        self.assertEqual(data['incorrect'], 2)

    def test_progress_nonexistent_game(self):
        """Progress for nonexistent game should return 404."""
        res = self.client.get('/api/games/nonexistent/progress')
        self.assertEqual(res.status_code, 404)

    def test_progress_total_cells_is_81(self):
        """Total cells should always be 81."""
        game_id, _, _ = self._create_game_with_board()
        res = self.client.get(f'/api/games/{game_id}/progress')
        self.assertEqual(res.get_json()['total_cells'], 81)


if __name__ == '__main__':
    unittest.main(verbosity=2)
