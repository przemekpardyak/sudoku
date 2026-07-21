"""
Tests for the auto-notes (pencil mark auto-fill) feature.
Tests the validation logic that determines which numbers are possible
for a given cell.
"""
import random
import unittest
from sudoku import (
    _is_valid, create_empty_board, generate_solved_board,
    generate_puzzle, _has_conflicts,
)


class TestAutoNotesLogic(unittest.TestCase):
    """Tests for the logic behind the auto-notes feature.

    The auto-notes feature fills in pencil marks for all possible numbers
    in each empty cell. A number is 'possible' if it doesn't conflict with
    any existing number in the same row, column, or 3x3 box.
    """

    def setUp(self):
        random.seed(42)
        self.puzzle, self.solution = generate_puzzle(difficulty=30)

    def test_possible_numbers_for_empty_cell(self):
        """For an empty cell, possible numbers should not conflict with existing values."""
        # Find first empty cell
        r, c = 0, 0
        for i in range(9):
            for j in range(9):
                if self.puzzle[i][j] == 0:
                    r, c = i, j
                    break
            else:
                continue
            break

        # Check each number 1-9
        for n in range(1, 10):
            is_possible = _is_valid(self.puzzle, r, c, n)
            if is_possible:
                # If possible, placing n should not create a conflict
                board_copy = [row[:] for row in self.puzzle]
                board_copy[r][c] = n
                self.assertFalse(_has_conflicts(board_copy),
                    f"Number {n} was marked as possible but creates a conflict at ({r},{c})")

    def test_all_empty_cells_have_at_least_one_possible(self):
        """Every empty cell in a valid puzzle should have at least one possible number."""
        for r in range(9):
            for c in range(9):
                if self.puzzle[r][c] == 0:
                    has_possible = False
                    for n in range(1, 10):
                        if _is_valid(self.puzzle, r, c, n):
                            has_possible = True
                            break
                    self.assertTrue(has_possible,
                        f"Cell ({r},{c}) has no possible numbers — puzzle may be invalid")

    def test_given_numbers_block_conflicting_possibilities(self):
        """A number already in the same row/col/box should not be possible."""
        for r in range(9):
            for c in range(9):
                if self.puzzle[r][c] == 0:
                    # Check row numbers
                    for cc in range(9):
                        val = self.puzzle[r][cc]
                        if val != 0:
                            self.assertFalse(_is_valid(self.puzzle, r, c, val),
                                f"Number {val} should not be possible at ({r},{c}) — it's in the same row at ({r},{cc})")
                    # Check column numbers
                    for rr in range(9):
                        val = self.puzzle[rr][c]
                        if val != 0:
                            self.assertFalse(_is_valid(self.puzzle, r, c, val),
                                f"Number {val} should not be possible at ({r},{c}) — it's in the same column at ({rr},{c})")

    def test_solution_number_always_possible_for_empty_cell(self):
        """The correct solution number should always be a possible number."""
        for r in range(9):
            for c in range(9):
                if self.puzzle[r][c] == 0:
                    correct = self.solution[r][c]
                    self.assertTrue(_is_valid(self.puzzle, r, c, correct),
                        f"Correct answer {correct} for cell ({r},{c}) is marked as impossible — puzzle is inconsistent")

    def test_possible_count_decreases_as_cells_filled(self):
        """As more cells are filled, the number of possible numbers should decrease."""
        # Find two empty cells
        empty_cells = [(r, c) for r in range(9) for c in range(9) if self.puzzle[r][c] == 0]
        if len(empty_cells) < 2:
            return  # Not enough empty cells

        r1, c1 = empty_cells[0]
        possible_before = sum(1 for n in range(1, 10) if _is_valid(self.puzzle, r1, c1, n))

        # Fill another cell in the same row
        for r2, c2 in empty_cells[1:]:
            if r2 == r1:
                board_copy = [row[:] for row in self.puzzle]
                board_copy[r2][c2] = self.solution[r2][c2]
                possible_after = sum(1 for n in range(1, 10) if _is_valid(board_copy, r1, c1, n))
                self.assertLessEqual(possible_after, possible_before,
                    "Filling a cell should not increase possibilities for another cell")
                break

    def test_solved_board_has_no_possibilities(self):
        """A fully solved board should have no empty cells to check."""
        solved = generate_solved_board()
        empty = sum(1 for r in range(9) for c in range(9) if solved[r][c] == 0)
        self.assertEqual(empty, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
