"""
Stress tests for puzzle generation.
Tests generating many puzzles quickly and consistently.
"""
import time
import unittest
from sudoku import generate_puzzle, generate_solved_board, _has_conflicts


class TestPuzzleGenerationStress(unittest.TestCase):
    """Stress tests for puzzle generation."""

    def test_generate_10_easy_puzzles(self):
        """Generate 10 easy puzzles quickly."""
        puzzles = []
        for _ in range(10):
            puzzle, solution = generate_puzzle(difficulty=20)
            puzzles.append((puzzle, solution))
            self.assertFalse(_has_conflicts(puzzle))
            self.assertFalse(_has_conflicts(solution))

    def test_generate_10_medium_puzzles(self):
        """Generate 10 medium puzzles quickly."""
        for _ in range(10):
            puzzle, solution = generate_puzzle(difficulty=30)
            self.assertFalse(_has_conflicts(puzzle))
            self.assertFalse(_has_conflicts(solution))

    def test_generate_5_hard_puzzles(self):
        """Generate 5 hard puzzles quickly."""
        for _ in range(5):
            puzzle, solution = generate_puzzle(difficulty=50)
            self.assertFalse(_has_conflicts(puzzle))
            self.assertFalse(_has_conflicts(solution))

    def test_all_puzzles_are_unique(self):
        """Generated puzzles should be different (with high probability)."""
        puzzles = set()
        for _ in range(10):
            puzzle, _ = generate_puzzle(difficulty=30)
            puzzles.add(str(puzzle))
        # At least 9 out of 10 should be unique
        self.assertGreaterEqual(len(puzzles), 9)

    def test_generate_solved_board_fast(self):
        """Generating a solved board should be fast (<2s)."""
        start = time.time()
        board = generate_solved_board()
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0)
        self.assertFalse(_has_conflicts(board))

    def test_generate_10_solved_boards(self):
        """Generate 10 solved boards quickly."""
        for _ in range(10):
            board = generate_solved_board()
            self.assertFalse(_has_conflicts(board))

    def test_puzzles_have_correct_empty_count(self):
        """Puzzles should have approximately the requested number of empty cells."""
        for difficulty in [20, 30, 40]:
            puzzle, _ = generate_puzzle(difficulty=difficulty)
            empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
            # Allow ±3 tolerance
            self.assertGreaterEqual(empty, difficulty - 3)
            self.assertLessEqual(empty, difficulty + 3)

    def test_puzzle_and_solution_same_dimensions(self):
        """Puzzle and solution should have the same dimensions."""
        puzzle, solution = generate_puzzle(difficulty=30)
        self.assertEqual(len(puzzle), 9)
        self.assertEqual(len(solution), 9)
        for i in range(9):
            self.assertEqual(len(puzzle[i]), 9)
            self.assertEqual(len(solution[i]), 9)

    def test_puzzle_cells_subset_of_solution(self):
        """Puzzle cells should match solution where puzzle is non-zero."""
        puzzle, solution = generate_puzzle(difficulty=30)
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] != 0:
                    self.assertEqual(puzzle[r][c], solution[r][c])

    def test_all_values_in_range(self):
        """All puzzle values should be 0-9."""
        puzzle, solution = generate_puzzle(difficulty=30)
        for r in range(9):
            for c in range(9):
                self.assertGreaterEqual(puzzle[r][c], 0)
                self.assertLessEqual(puzzle[r][c], 9)
                self.assertGreaterEqual(solution[r][c], 0)
                self.assertLessEqual(solution[r][c], 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
