"""
Tests for board validation and conflict detection logic.
Tests the sudoku.py _has_conflicts function and related validation.
"""
import random
import unittest
from sudoku import (
    _is_valid, _has_conflicts, create_empty_board,
    generate_solved_board, generate_puzzle, _solve, _count_solutions,
)


class TestBoardValidation(unittest.TestCase):
    """Tests for board validation logic."""

    def test_valid_solved_board(self):
        random.seed(42)
        board = generate_solved_board()
        self.assertFalse(_has_conflicts(board))

    def test_empty_board_is_valid(self):
        board = create_empty_board()
        self.assertFalse(_has_conflicts(board))

    def test_row_conflict_invalid(self):
        board = create_empty_board()
        board[0][0] = 5
        board[0][3] = 5
        self.assertTrue(_has_conflicts(board))

    def test_column_conflict_invalid(self):
        board = create_empty_board()
        board[0][0] = 7
        board[3][0] = 7
        self.assertTrue(_has_conflicts(board))

    def test_box_conflict_invalid(self):
        board = create_empty_board()
        board[0][0] = 3
        board[1][1] = 3
        self.assertTrue(_has_conflicts(board))

    def test_partial_valid_board(self):
        board = create_empty_board()
        board[0][0] = 1
        board[0][3] = 2
        board[0][6] = 3
        board[3][0] = 4
        board[3][3] = 5
        board[3][6] = 6
        board[6][0] = 7
        board[6][3] = 8
        board[6][6] = 9
        self.assertFalse(_has_conflicts(board))

    def test_invalid_placement_detected(self):
        """Placing a number that conflicts should be detected."""
        random.seed(42)
        board = generate_solved_board()
        # Introduce a conflict
        board[0][0] = board[0][1]
        self.assertTrue(_has_conflicts(board))

    def test_is_valid_placement_check(self):
        """_is_valid should check individual placements."""
        board = create_empty_board()
        board[0][0] = 5
        # Placing 5 in same row should be invalid
        self.assertFalse(_is_valid(board, 0, 3, 5))
        # Placing 5 in same column should be invalid
        self.assertFalse(_is_valid(board, 3, 0, 5))
        # Placing 5 in same box should be invalid
        self.assertFalse(_is_valid(board, 1, 1, 5))
        # Placing 5 in a different row/col/box should be valid
        self.assertTrue(_is_valid(board, 3, 3, 5))


class TestPuzzleGenerationQuality(unittest.TestCase):
    """Tests for puzzle generation quality and consistency."""

    def test_easy_puzzle_has_fewer_empty_cells(self):
        random.seed(42)
        easy_puzzle, _ = generate_puzzle(difficulty=30)
        random.seed(42)
        hard_puzzle, _ = generate_puzzle(difficulty=50)
        easy_empty = sum(1 for r in range(9) for c in range(9) if easy_puzzle[r][c] == 0)
        hard_empty = sum(1 for r in range(9) for c in range(9) if hard_puzzle[r][c] == 0)
        self.assertLess(easy_empty, hard_empty)

    def test_all_difficulties_generate_valid_puzzles(self):
        """All supported difficulty levels should produce valid puzzles."""
        for diff in [0, 10, 20, 30, 40, 50, 58]:
            random.seed(42 + diff)
            puzzle, solution = generate_puzzle(difficulty=diff)
            self.assertFalse(_has_conflicts(puzzle))
            self.assertFalse(_has_conflicts(solution))
            for r in range(9):
                for c in range(9):
                    if puzzle[r][c] != 0:
                        self.assertEqual(puzzle[r][c], solution[r][c])

    def test_generated_puzzle_is_solvable(self):
        """Every generated puzzle should be solvable."""
        for diff in [30, 40, 50]:
            random.seed(42 + diff)
            puzzle, solution = generate_puzzle(difficulty=diff)
            board = [row[:] for row in puzzle]
            self.assertTrue(_solve(board))
            self.assertEqual(board, solution)

    def test_solution_matches_generated_puzzle(self):
        """The solution returned by generate_puzzle should solve the puzzle."""
        random.seed(42)
        puzzle, solution = generate_puzzle(difficulty=30)
        board = [row[:] for row in puzzle]
        _solve(board)
        self.assertEqual(board, solution)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases in puzzle generation and solving."""

    def test_empty_board_solve(self):
        """Solving an empty board should produce a valid solution."""
        board = create_empty_board()
        self.assertTrue(_solve(board))
        self.assertFalse(_has_conflicts(board))

    def test_generate_puzzle_with_zero_difficulty(self):
        """Difficulty 0 should produce a full board (no empty cells)."""
        random.seed(42)
        puzzle, solution = generate_puzzle(difficulty=0)
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertEqual(empty, 0)
        self.assertEqual(puzzle, solution)

    def test_generate_puzzle_with_max_difficulty(self):
        """High difficulty should still produce a valid puzzle with unique solution."""
        random.seed(42)
        puzzle, solution = generate_puzzle(difficulty=58)
        self.assertEqual(_count_solutions(puzzle, limit=2), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
