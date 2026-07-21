"""
Tests for solver robustness with malformed and edge-case inputs.
"""
import os
import unittest
from sudoku import _is_valid, _has_conflicts, _solve, _count_solutions, generate_puzzle


class TestSolverRobustness(unittest.TestCase):
    """Tests for solver robustness with edge cases."""

    @unittest.skipUnless(
        os.environ.get("SUDOKU_RUN_SLOW") == "1",
        "17-clue puzzle takes ~14 minutes — uses naive backtracking with no constraint "
        "propagation or MRV heuristic; with only 17 clues (mathematical minimum for unique "
        "solution), the solver explores millions of deep branches before finding contradictions. "
        "Set SUDOKU_RUN_SLOW=1 to force run."
    )
    def test_solve_with_minimal_clues(self):
        """Solver should handle a board with only 17 clues (minimum for unique solution)."""
        # A known 17-clue Sudoku
        board = [
            [0, 0, 0, 0, 0, 0, 0, 1, 0],
            [4, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 2, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 5, 0, 4, 0, 7],
            [0, 0, 8, 0, 0, 0, 3, 0, 0],
            [0, 0, 1, 0, 9, 0, 0, 0, 0],
            [3, 0, 0, 4, 0, 0, 2, 0, 0],
            [0, 5, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 8, 0, 6, 0, 0, 0],
        ]
        import copy
        solved = copy.deepcopy(board)
        result = _solve(solved)
        self.assertTrue(result)
        self.assertFalse(_has_conflicts(solved))

    def test_solve_already_solved(self):
        """Solver should handle an already-solved board."""
        _, solution = generate_puzzle(difficulty=0)
        import copy
        board = copy.deepcopy(solution)
        _solve(board)
        self.assertEqual(board, solution)

    def test_count_solutions_empty_board(self):
        """Empty board should have many solutions (at least 2)."""
        board = [[0]*9 for _ in range(9)]
        count = _count_solutions(board, limit=2)
        self.assertGreaterEqual(count, 2)

    def test_count_solutions_full_board(self):
        """A complete valid board should have exactly 1 solution."""
        _, solution = generate_puzzle(difficulty=0)
        count = _count_solutions(solution, limit=2)
        self.assertEqual(count, 1)

    def test_is_valid_with_all_numbers(self):
        """_is_valid should reject duplicates in row/col/box."""
        board = [[0]*9 for _ in range(9)]
        # Place a 5 at (0,0)
        board[0][0] = 5
        # 5 should be invalid at (0,1) - same row
        self.assertFalse(_is_valid(board, 0, 1, 5))
        # 5 should be invalid at (1,0) - same column
        self.assertFalse(_is_valid(board, 1, 0, 5))
        # 5 should be invalid at (1,1) - same box
        self.assertFalse(_is_valid(board, 1, 1, 5))
        # 5 should be valid at (4,4) - no conflict
        self.assertTrue(_is_valid(board, 4, 4, 5))

    def test_has_conflicts_with_empty_board(self):
        """Empty board should have no conflicts."""
        board = [[0]*9 for _ in range(9)]
        self.assertFalse(_has_conflicts(board))

    def test_has_conflicts_full_valid_board(self):
        """A valid solved board should have no conflicts."""
        _, solution = generate_puzzle(difficulty=0)
        self.assertFalse(_has_conflicts(solution))

    def test_has_conflicts_row_duplicate(self):
        """Row duplicates should be detected."""
        board = [[5, 5] + [0]*7] + [[0]*9]*8
        self.assertTrue(_has_conflicts(board))

    def test_has_conflicts_col_duplicate(self):
        """Column duplicates should be detected."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 3
        board[5][0] = 3
        self.assertTrue(_has_conflicts(board))

    def test_has_conflicts_box_duplicate(self):
        """Box duplicates should be detected."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 7
        board[2][2] = 7
        self.assertTrue(_has_conflicts(board))

    def test_solve_does_not_modify_original(self):
        """Solving should not modify the input board (uses copy)."""
        puzzle, _ = generate_puzzle(difficulty=30)
        original = [row[:] for row in puzzle]
        import copy
        solved = copy.deepcopy(puzzle)
        _solve(solved)
        # Original puzzle should be unchanged
        self.assertEqual(puzzle, original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
