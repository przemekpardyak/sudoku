"""
Tests for puzzle difficulty validation across all difficulty levels.
Ensures that generate_puzzle produces puzzles with exactly the right number
of empty cells for each difficulty level.
"""
import unittest
from sudoku import generate_puzzle, _count_solutions, _has_conflicts


class TestDifficultyValidation(unittest.TestCase):
    """Tests that puzzle generation respects difficulty levels."""

    def test_easy_has_30_empty(self):
        """Easy difficulty (30) should produce ~30 empty cells (±3)."""
        puzzle, solution = generate_puzzle(difficulty=30)
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertGreaterEqual(empty, 27, f"Easy should have ≥27 empty, got {empty}")
        self.assertLessEqual(empty, 30, f"Easy should have ≤30 empty, got {empty}")

    def test_medium_has_40_empty(self):
        """Medium difficulty (40) should produce ~40 empty cells (±3)."""
        puzzle, solution = generate_puzzle(difficulty=40)
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertGreaterEqual(empty, 37, f"Medium should have ≥37 empty, got {empty}")
        self.assertLessEqual(empty, 40, f"Medium should have ≤40 empty, got {empty}")

    def test_hard_has_50_empty(self):
        """Hard difficulty (50) should produce ~50 empty cells (±3)."""
        puzzle, solution = generate_puzzle(difficulty=50)
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertGreaterEqual(empty, 47, f"Hard should have ≥47 empty, got {empty}")
        self.assertLessEqual(empty, 50, f"Hard should have ≤50 empty, got {empty}")

    def test_expert_has_58_empty(self):
        """Expert difficulty (58) should produce ~58 empty cells (±3)."""
        puzzle, solution = generate_puzzle(difficulty=58)
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertGreaterEqual(empty, 53, f"Expert should have ≥53 empty, got {empty}")
        self.assertLessEqual(empty, 58, f"Expert should have ≤58 empty, got {empty}")

    def test_all_difficulties_produce_valid_puzzles(self):
        """All difficulty levels should produce puzzles with unique solutions."""
        for diff in [30, 40, 50, 58]:
            with self.subTest(difficulty=diff):
                puzzle, solution = generate_puzzle(difficulty=diff)
                self.assertFalse(_has_conflicts(puzzle),
                                f"Difficulty {diff} puzzle has conflicts")
                self.assertEqual(_count_solutions(puzzle, limit=2), 1,
                                f"Difficulty {diff} puzzle is not unique")

    def test_puzzle_is_subset_of_solution(self):
        """Puzzle should be a subset of the solution."""
        for diff in [30, 40, 50, 58]:
            with self.subTest(difficulty=diff):
                puzzle, solution = generate_puzzle(difficulty=diff)
                for r in range(9):
                    for c in range(9):
                        if puzzle[r][c] != 0:
                            self.assertEqual(puzzle[r][c], solution[r][c],
                                           f"Mismatch at ({r},{c}) for difficulty {diff}")

    def test_solution_is_complete(self):
        """Solution should have no empty cells."""
        for diff in [30, 40, 50, 58]:
            with self.subTest(difficulty=diff):
                puzzle, solution = generate_puzzle(difficulty=diff)
                for r in range(9):
                    for c in range(9):
                        self.assertNotEqual(solution[r][c], 0,
                                           f"Solution has 0 at ({r},{c}) for difficulty {diff}")

    def test_solution_is_valid(self):
        """Solution should be a valid Sudoku — no conflicts."""
        for diff in [30, 40, 50, 58]:
            with self.subTest(difficulty=diff):
                puzzle, solution = generate_puzzle(difficulty=diff)
                self.assertFalse(_has_conflicts(solution),
                                f"Solution for difficulty {diff} has conflicts")

    def test_puzzle_has_at_least_one_empty(self):
        """Even the easiest puzzle should have at least 1 empty cell."""
        puzzle, solution = generate_puzzle(difficulty=1)
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertGreaterEqual(empty, 1)

    def test_zero_difficulty_produces_solved_board(self):
        """Difficulty 0 should produce a fully solved board."""
        puzzle, solution = generate_puzzle(difficulty=0)
        empty = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertEqual(empty, 0)

    def test_puzzle_is_9x9(self):
        """Puzzle should be a 9x9 grid."""
        for diff in [30, 40, 50, 58]:
            with self.subTest(difficulty=diff):
                puzzle, solution = generate_puzzle(difficulty=diff)
                self.assertEqual(len(puzzle), 9)
                self.assertEqual(len(solution), 9)
                for row in puzzle:
                    self.assertEqual(len(row), 9)
                for row in solution:
                    self.assertEqual(len(row), 9)

    def test_multiple_puzzles_different(self):
        """Multiple puzzles at the same difficulty should be different."""
        puzzles = set()
        for _ in range(5):
            puzzle, _ = generate_puzzle(difficulty=30)
            puzzles.add(tuple(tuple(row) for row in puzzle))
        self.assertGreater(len(puzzles), 1, "Generated puzzles should not all be identical")

    def test_all_values_in_range(self):
        """All puzzle values should be 0-9."""
        for diff in [30, 40, 50, 58]:
            with self.subTest(difficulty=diff):
                puzzle, solution = generate_puzzle(difficulty=diff)
                for r in range(9):
                    for c in range(9):
                        self.assertGreaterEqual(puzzle[r][c], 0)
                        self.assertLessEqual(puzzle[r][c], 9)
                        self.assertGreaterEqual(solution[r][c], 1)
                        self.assertLessEqual(solution[r][c], 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
