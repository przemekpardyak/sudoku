"""
Tests for board state diff calculation.
Tests the comparison between two board states to find differences.
"""
import unittest
from sudoku import generate_puzzle, _has_conflicts


def board_diff(board_a, board_b):
    """Calculate differences between two boards.
    Returns list of (row, col, old_value, new_value) tuples.
    """
    diffs = []
    for r in range(9):
        for c in range(9):
            if board_a[r][c] != board_b[r][c]:
                diffs.append((r, c, board_a[r][c], board_b[r][c]))
    return diffs


class TestBoardDiff(unittest.TestCase):
    """Tests for board state diff calculation."""

    def test_identical_boards_no_diff(self):
        """Identical boards should have no differences."""
        board = [[0]*9 for _ in range(9)]
        diffs = board_diff(board, board)
        self.assertEqual(len(diffs), 0)

    def test_single_cell_change(self):
        """Changing one cell should produce one diff."""
        board_a = [[0]*9 for _ in range(9)]
        board_b = [row[:] for row in board_a]
        board_b[3][5] = 7
        diffs = board_diff(board_a, board_b)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0], (3, 5, 0, 7))

    def test_multiple_changes(self):
        """Multiple cell changes should all be detected."""
        board_a = [[0]*9 for _ in range(9)]
        board_b = [row[:] for row in board_a]
        board_b[0][0] = 1
        board_b[4][4] = 5
        board_b[8][8] = 9
        diffs = board_diff(board_a, board_b)
        self.assertEqual(len(diffs), 3)

    def test_cell_cleared(self):
        """Clearing a cell (setting to 0) should be detected."""
        board_a = [[5]*9 for _ in range(9)]
        board_b = [row[:] for row in board_a]
        board_b[2][3] = 0
        diffs = board_diff(board_a, board_b)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0], (2, 3, 5, 0))

    def test_cell_replaced(self):
        """Replacing a value should show old and new."""
        board_a = [[3]*9 for _ in range(9)]
        board_b = [row[:] for row in board_a]
        board_b[1][1] = 8
        diffs = board_diff(board_a, board_b)
        self.assertEqual(diffs[0], (1, 1, 3, 8))

    def test_diff_with_puzzle_progress(self):
        """Diff between puzzle and solution shows all empty cells."""
        puzzle, solution = generate_puzzle(difficulty=30)
        diffs = board_diff(puzzle, solution)
        # Number of diffs should equal number of empty cells
        empty_count = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertEqual(len(diffs), empty_count)

    def test_diff_order_consistent(self):
        """Diff should be consistent regardless of call order."""
        board_a = [[0]*9 for _ in range(9)]
        board_b = [row[:] for row in board_a]
        board_b[0][0] = 5
        board_b[5][5] = 3

        diffs_ab = board_diff(board_a, board_b)
        diffs_ba = board_diff(board_b, board_a)

        # Same cells should be different
        self.assertEqual(len(diffs_ab), len(diffs_ba))
        for i, (r, c, old, new) in enumerate(diffs_ab):
            self.assertEqual(diffs_ba[i][0], r)
            self.assertEqual(diffs_ba[i][1], c)
            # Old/new should be swapped
            self.assertEqual(diffs_ba[i][2], new)
            self.assertEqual(diffs_ba[i][3], old)

    def test_full_board_diff(self):
        """Diff between empty and full board should be 81 cells."""
        empty = [[0]*9 for _ in range(9)]
        full = [[(r*3 + r//3 + c) % 9 + 1 for c in range(9)] for r in range(9)]
        diffs = board_diff(empty, full)
        self.assertEqual(len(diffs), 81)


if __name__ == '__main__':
    unittest.main(verbosity=2)
