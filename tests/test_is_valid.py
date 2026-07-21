"""
Tests for the _is_valid function — the core validation used by auto-notes.
"""
import random
import unittest
from sudoku import (
    _is_valid, _has_conflicts, create_empty_board,
    generate_solved_board, generate_puzzle,
)


class TestIsValidPlacement(unittest.TestCase):
    """Tests for _is_valid(board, row, col, num) — checks if a number can be placed."""

    def test_valid_placement_empty_board(self):
        """Any number 1-9 should be valid on an empty board."""
        board = create_empty_board()
        for r in range(9):
            for c in range(9):
                for n in range(1, 10):
                    self.assertTrue(_is_valid(board, r, c, n))

    def test_invalid_row_placement(self):
        """Placing a number that exists in the same row should be invalid."""
        board = create_empty_board()
        board[3][0] = 5
        self.assertFalse(_is_valid(board, 3, 5, 5))
        # Different number should be valid
        self.assertTrue(_is_valid(board, 3, 5, 6))

    def test_invalid_column_placement(self):
        """Placing a number that exists in the same column should be invalid."""
        board = create_empty_board()
        board[0][4] = 7
        self.assertFalse(_is_valid(board, 5, 4, 7))
        self.assertTrue(_is_valid(board, 5, 4, 8))

    def test_invalid_box_placement(self):
        """Placing a number that exists in the same 3x3 box should be invalid."""
        board = create_empty_board()
        board[0][0] = 3
        # Same box (rows 0-2, cols 0-2)
        self.assertFalse(_is_valid(board, 2, 2, 3))
        # Different box should be valid
        self.assertTrue(_is_valid(board, 3, 3, 3))

    def test_valid_placement_in_generated_puzzle(self):
        """In a generated puzzle, the solution value should always be a valid placement."""
        random.seed(42)
        puzzle, solution = generate_puzzle(difficulty=30)
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] == 0:
                    self.assertTrue(_is_valid(puzzle, r, c, solution[r][c]),
                        f"Solution value {solution[r][c]} should be valid at ({r},{c})")

    def test_placement_after_filling_cell(self):
        """After placing a number, it should block that number in the same row/col/box."""
        board = create_empty_board()
        # Place 5 at (0,0)
        board[0][0] = 5
        # Should block 5 in same row
        self.assertFalse(_is_valid(board, 0, 3, 5))
        # Should block 5 in same column
        self.assertFalse(_is_valid(board, 3, 0, 5))
        # Should block 5 in same box
        self.assertFalse(_is_valid(board, 2, 2, 5))
        # Should not block 5 in different box
        self.assertTrue(_is_valid(board, 3, 3, 5))

    def test_all_placements_valid_on_solved_board(self):
        """A solved board should have no conflicts (every placement is 'used')."""
        random.seed(42)
        board = generate_solved_board()
        # The board itself should have no conflicts
        self.assertFalse(_has_conflicts(board))


if __name__ == '__main__':
    unittest.main(verbosity=2)
