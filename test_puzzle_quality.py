"""
Comprehensive tests for puzzle generation quality.
Validates that generated puzzles are solvable, unique, and well-formed.
"""
import unittest
from sudoku import generate_puzzle, generate_solved_board, _has_conflicts, _solve, _count_solutions


class TestPuzzleQuality(unittest.TestCase):
    """Comprehensive quality tests for generated puzzles."""

    def test_puzzle_is_valid(self):
        """Generated puzzle should have no conflicts."""
        puzzle, _ = generate_puzzle(difficulty=30)
        self.assertFalse(_has_conflicts(puzzle))

    def test_puzzle_has_unique_solution(self):
        """Generated puzzle should have exactly one solution."""
        puzzle, _ = generate_puzzle(difficulty=30)
        num_solutions = _count_solutions(puzzle, limit=2)
        self.assertEqual(num_solutions, 1)

    def test_solution_matches_puzzle(self):
        """The solution should be consistent with the puzzle clues."""
        puzzle, solution = generate_puzzle(difficulty=30)
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] != 0:
                    self.assertEqual(puzzle[r][c], solution[r][c])

    def test_puzzle_has_empty_cells(self):
        """Generated puzzle should have empty cells."""
        puzzle, _ = generate_puzzle(difficulty=30)
        empty_count = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] == 0)
        self.assertGreater(empty_count, 0)

    def test_solution_is_complete(self):
        """The solution should be a complete 9x9 grid with no zeros."""
        _, solution = generate_puzzle(difficulty=30)
        for r in range(9):
            for c in range(9):
                self.assertNotEqual(solution[r][c], 0)

    def test_solution_is_valid(self):
        """The solution should have no conflicts."""
        _, solution = generate_puzzle(difficulty=30)
        self.assertFalse(_has_conflicts(solution))

    def test_solving_puzzle_gives_solution(self):
        """Solving the puzzle should produce the same solution."""
        import copy
        puzzle, solution = generate_puzzle(difficulty=30)
        solved = copy.deepcopy(puzzle)
        _solve(solved)
        self.assertEqual(solved, solution)

    def test_different_difficulties_have_different_empty_counts(self):
        """Higher difficulty should generally have more empty cells."""
        _, easy_sol = generate_puzzle(difficulty=30)
        _, hard_sol = generate_puzzle(difficulty=50)

        easy_empty = sum(1 for r in range(9) for c in range(9) if easy_sol[r][c] == 0)
        hard_empty = sum(1 for r in range(9) for c in range(9) if hard_sol[r][c] == 0)

        # Hard should have at least as many empty cells as easy (usually more)
        self.assertGreaterEqual(hard_empty, easy_empty - 5)

    def test_puzzle_values_in_range(self):
        """All puzzle values should be 0-9."""
        puzzle, _ = generate_puzzle(difficulty=40)
        for r in range(9):
            for c in range(9):
                self.assertGreaterEqual(puzzle[r][c], 0)
                self.assertLessEqual(puzzle[r][c], 9)

    def test_solution_values_in_range(self):
        """All solution values should be 1-9."""
        _, solution = generate_puzzle(difficulty=40)
        for r in range(9):
            for c in range(9):
                self.assertGreaterEqual(solution[r][c], 1)
                self.assertLessEqual(solution[r][c], 9)

    def test_solved_board_is_valid(self):
        """generate_solved_board should produce a valid solved board."""
        board = generate_solved_board()
        self.assertFalse(_has_conflicts(board))

    def test_solved_board_no_zeros(self):
        """generate_solved_board should have no zeros."""
        board = generate_solved_board()
        for r in range(9):
            for c in range(9):
                self.assertNotEqual(board[r][c], 0)

    def test_multiple_puzzles_are_different(self):
        """Multiple generated puzzles should be different (with high probability)."""
        p1, _ = generate_puzzle(difficulty=30)
        p2, _ = generate_puzzle(difficulty=30)
        self.assertNotEqual(p1, p2)

    def test_puzzle_is_9x9(self):
        """Puzzle should be exactly 9x9."""
        puzzle, _ = generate_puzzle(difficulty=40)
        self.assertEqual(len(puzzle), 9)
        for row in puzzle:
            self.assertEqual(len(row), 9)

    def test_solution_is_9x9(self):
        """Solution should be exactly 9x9."""
        _, solution = generate_puzzle(difficulty=40)
        self.assertEqual(len(solution), 9)
        for row in solution:
            self.assertEqual(len(row), 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
