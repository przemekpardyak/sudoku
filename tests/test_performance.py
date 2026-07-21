"""
Performance tests for puzzle generation and solving.
Ensures generation and solving complete within acceptable time limits.
"""
import time
import unittest
from sudoku import generate_puzzle, generate_solved_board, _solve, _count_solutions, _has_conflicts


class TestPerformance(unittest.TestCase):
    """Performance tests for core Sudoku operations."""

    def test_generate_easy_under_2s(self):
        """Easy puzzle generation should complete in under 2 seconds."""
        start = time.time()
        generate_puzzle(difficulty=30)
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"Easy generation took {elapsed:.2f}s")

    def test_generate_medium_under_2s(self):
        """Medium puzzle generation should complete in under 2 seconds."""
        start = time.time()
        generate_puzzle(difficulty=40)
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"Medium generation took {elapsed:.2f}s")

    def test_generate_hard_under_3s(self):
        """Hard puzzle generation should complete in under 3 seconds."""
        start = time.time()
        generate_puzzle(difficulty=50)
        elapsed = time.time() - start
        self.assertLess(elapsed, 3.0, f"Hard generation took {elapsed:.2f}s")

    def test_generate_expert_under_30s(self):
        """Expert puzzle generation should complete in under 30 seconds.

        Note: Expert (58 cells removed) is slow because each cell removal
        requires a uniqueness check via _count_solutions. This is expected
        for high-difficulty puzzles with many cells removed.
        """
        start = time.time()
        generate_puzzle(difficulty=58)
        elapsed = time.time() - start
        self.assertLess(elapsed, 30.0, f"Expert generation took {elapsed:.2f}s")

    def test_generate_solved_board_under_1s(self):
        """Generating a solved board should be under 1 second."""
        start = time.time()
        generate_solved_board()
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0, f"Solved board generation took {elapsed:.2f}s")

    def test_solve_empty_board_under_1s(self):
        """Solving an empty board should be under 1 second."""
        board = [[0] * 9 for _ in range(9)]
        start = time.time()
        _solve(board)
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0, f"Solving empty board took {elapsed:.2f}s")

    def test_count_solutions_under_2s(self):
        """Counting solutions for a hard puzzle should be under 2 seconds."""
        puzzle, _ = generate_puzzle(difficulty=50)
        start = time.time()
        _count_solutions(puzzle, limit=2)
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, f"Counting solutions took {elapsed:.2f}s")

    def test_has_conflicts_under_1ms(self):
        """Conflict detection should be nearly instant."""
        board = generate_solved_board()
        start = time.time()
        _has_conflicts(board)
        elapsed = time.time() - start
        self.assertLess(elapsed, 0.001, f"Conflict detection took {elapsed:.4f}s")

    def test_multiple_generations_under_10s(self):
        """Generating 5 puzzles should complete in under 10 seconds total."""
        start = time.time()
        for _ in range(5):
            generate_puzzle(difficulty=40)
        elapsed = time.time() - start
        self.assertLess(elapsed, 10.0, f"5 puzzles took {elapsed:.2f}s")

    def test_seed_reproducible_fast(self):
        """Seeded puzzle generation should be fast and reproducible."""
        import random
        random.seed("perf-test")
        start = time.time()
        p1, s1 = generate_puzzle(difficulty=40)
        elapsed1 = time.time() - start

        random.seed("perf-test")
        start = time.time()
        p2, s2 = generate_puzzle(difficulty=40)
        elapsed2 = time.time() - start

        self.assertEqual(p1, p2)
        self.assertLess(elapsed1, 2.0)
        self.assertLess(elapsed2, 2.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
