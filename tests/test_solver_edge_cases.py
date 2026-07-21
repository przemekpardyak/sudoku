"""
Tests for the _has_conflicts() function and solver edge cases.
"""
import random
import unittest
from sudoku import (
    _has_conflicts, _solve, _count_solutions, _is_valid,
    create_empty_board, generate_solved_board, generate_puzzle,
)


class TestHasConflicts(unittest.TestCase):
    """Tests for _has_conflicts() — pre-check for the solver."""

    def test_empty_board_no_conflicts(self):
        board = create_empty_board()
        self.assertFalse(_has_conflicts(board))

    def test_solved_board_no_conflicts(self):
        random.seed(42)
        board = generate_solved_board()
        self.assertFalse(_has_conflicts(board))

    def test_row_conflict_detected(self):
        board = create_empty_board()
        board[0][0] = 5
        board[0][5] = 5
        self.assertTrue(_has_conflicts(board))

    def test_column_conflict_detected(self):
        board = create_empty_board()
        board[0][0] = 7
        board[5][0] = 7
        self.assertTrue(_has_conflicts(board))

    def test_box_conflict_detected(self):
        board = create_empty_board()
        board[0][0] = 3
        board[1][1] = 3  # same 3x3 box
        self.assertTrue(_has_conflicts(board))

    def test_no_conflict_different_boxes(self):
        board = create_empty_board()
        board[0][0] = 5  # box (0,0)
        board[3][3] = 5  # box (3,3) — different box
        self.assertFalse(_has_conflicts(board))

    def test_multiple_conflicts(self):
        board = create_empty_board()
        board[0][0] = 5
        board[0][1] = 5  # row conflict
        board[5][5] = 9
        board[6][5] = 9  # column conflict
        self.assertTrue(_has_conflicts(board))

    def test_single_value_no_conflict(self):
        board = create_empty_board()
        board[4][4] = 7
        self.assertFalse(_has_conflicts(board))


class TestSolverEdgeCases(unittest.TestCase):
    """Tests for solver edge cases after _has_conflicts fix."""

    def test_solve_unsolvable_conflict_returns_immediately(self):
        """Board with a direct conflict should return False instantly."""
        board = create_empty_board()
        board[0][0] = 5
        board[0][1] = 5
        self.assertFalse(_solve(board))

    def test_count_solutions_conflict_returns_zero(self):
        """_count_solutions should return 0 for a conflicting board."""
        board = create_empty_board()
        board[0][0] = 5
        board[0][1] = 5
        self.assertEqual(_count_solutions(board, limit=2), 0)

    def test_count_solutions_empty_board_still_works(self):
        """Empty board should still have many solutions (not blocked by pre-check)."""
        board = create_empty_board()
        self.assertEqual(_count_solutions(board, limit=2), 2)

    def test_solve_valid_partial_board(self):
        """A valid partial board should still be solvable."""
        board = create_empty_board()
        board[0][0] = 5
        board[1][1] = 3
        board[2][2] = 7
        self.assertTrue(_solve(board))

    def test_generate_puzzle_not_blocked_by_conflict_check(self):
        """Puzzle generation should work normally with the pre-check."""
        random.seed(42)
        puzzle, solution = generate_puzzle(difficulty=30)
        # Verify puzzle has empty cells
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertEqual(empty, 30)
        # Verify uniqueness
        self.assertEqual(_count_solutions(puzzle, limit=2), 1)


class TestSolverPerformance(unittest.TestCase):
    """Tests to ensure solver performance is acceptable."""

    def test_unsolvable_returns_quickly(self):
        """Unsolvable board should return in under 1 second."""
        import time
        board = create_empty_board()
        board[0][0] = 5
        board[0][1] = 5
        start = time.time()
        result = _solve(board)
        elapsed = time.time() - start
        self.assertFalse(result)
        self.assertLess(elapsed, 1.0, "Solver should return in under 1 second for conflicting board")

    def test_generate_puzzle_under_5_seconds(self):
        """Puzzle generation should complete in under 5 seconds."""
        import time
        random.seed(42)
        start = time.time()
        generate_puzzle(difficulty=40)
        elapsed = time.time() - start
        self.assertLess(elapsed, 5.0, "Puzzle generation should be under 5 seconds")


if __name__ == '__main__':
    unittest.main(verbosity=2)
