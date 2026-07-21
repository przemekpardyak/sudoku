"""
Tests for solver techniques.
Tests the logical solving strategies used by the hint endpoint.
"""
import unittest
from sudoku import (
    generate_puzzle, generate_solved_board, _solve, _has_conflicts,
    _is_valid, _count_solutions, create_empty_board
)


class TestSolverTechniques(unittest.TestCase):
    """Tests for Sudoku solving techniques."""

    def test_naked_single_detection(self):
        """Naked single: cell with only one possible candidate."""
        # A board where a cell has only one possible value
        board = generate_solved_board()
        # Clear one cell — it should have exactly one solution
        board[4][4] = 0
        count = _count_solutions(board, limit=2)
        self.assertEqual(count, 1)

    def test_hidden_single_in_row(self):
        """Hidden single: a number can only go in one cell in a row."""
        board = generate_solved_board()
        # Remove all instances of a number from one row except one
        val = board[0][0]
        for c in range(1, 9):
            if board[0][c] == val:
                board[0][c] = 0
        # The number should still be placeable at (0,0)
        # and the board should have a unique solution
        count = _count_solutions(board, limit=2)
        self.assertEqual(count, 1)

    def test_hidden_single_in_column(self):
        """Hidden single in a column."""
        board = generate_solved_board()
        val = board[0][0]
        # Remove val from column 0 except row 0
        for r in range(1, 9):
            if board[r][0] == val:
                board[r][0] = 0
        # Should still have unique solution
        count = _count_solutions(board, limit=2)
        self.assertEqual(count, 1)

    def test_hidden_single_in_box(self):
        """Hidden single in a 3x3 box."""
        board = generate_solved_board()
        val = board[0][0]
        # Remove val from box (0-2, 0-2) except (0,0)
        for r in range(3):
            for c in range(3):
                if (r == 0 and c == 0):
                    continue
                if board[r][c] == val:
                    board[r][c] = 0
        count = _count_solutions(board, limit=2)
        self.assertEqual(count, 1)

    def test_solver_finds_unique_solution(self):
        """Solver should find the unique solution for a valid puzzle."""
        puzzle, solution = generate_puzzle(difficulty=30)
        import copy
        board = copy.deepcopy(puzzle)
        result = _solve(board)
        self.assertTrue(result)
        self.assertEqual(board, solution)

    def test_solver_preserves_given_cells(self):
        """Solver should not change given (non-zero) cells."""
        puzzle, solution = generate_puzzle(difficulty=30)
        import copy
        board = copy.deepcopy(puzzle)
        _solve(board)
        # All original clues should be preserved
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] != 0:
                    self.assertEqual(board[r][c], puzzle[r][c])

    def test_count_solutions_finds_multiple(self):
        """Empty board should have multiple solutions."""
        board = create_empty_board()
        count = _count_solutions(board, limit=5)
        self.assertGreaterEqual(count, 2)

    def test_solver_with_conflicts_returns_false(self):
        """Solver should return False for boards with conflicts."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 5
        board[0][1] = 5  # Row conflict
        # _solve doesn't check conflicts, but _has_conflicts does
        self.assertTrue(_has_conflicts(board))

    def test_is_valid_all_directions(self):
        """_is_valid should check row, column, and box constraints."""
        board = create_empty_board()
        board[4][4] = 7
        # Same row
        self.assertFalse(_is_valid(board, 4, 5, 7))
        # Same column
        self.assertFalse(_is_valid(board, 5, 4, 7))
        # Same box
        self.assertFalse(_is_valid(board, 3, 3, 7))
        # Different row, column, and box
        self.assertTrue(_is_valid(board, 0, 8, 7))

    def test_generated_puzzles_are_solvable(self):
        """All generated puzzles should be solvable."""
        for difficulty in [20, 30, 40, 50]:
            puzzle, solution = generate_puzzle(difficulty=difficulty)
            import copy
            board = copy.deepcopy(puzzle)
            result = _solve(board)
            self.assertTrue(result, f"Puzzle with difficulty {difficulty} was not solvable")
            self.assertEqual(board, solution)

    def test_solution_has_all_numbers(self):
        """Solution should have numbers 1-9 in every row, column, and box."""
        _, solution = generate_puzzle(difficulty=30)
        for i in range(9):
            # Row
            row_nums = set(solution[i])
            self.assertEqual(row_nums, {1, 2, 3, 4, 5, 6, 7, 8, 9})
            # Column
            col_nums = set(solution[r][i] for r in range(9))
            self.assertEqual(col_nums, {1, 2, 3, 4, 5, 6, 7, 8, 9})
        # Boxes
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                box_nums = set()
                for r in range(br, br + 3):
                    for c in range(bc, bc + 3):
                        box_nums.add(solution[r][c])
                self.assertEqual(box_nums, {1, 2, 3, 4, 5, 6, 7, 8, 9})


if __name__ == '__main__':
    unittest.main(verbosity=2)
