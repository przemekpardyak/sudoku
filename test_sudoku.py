"""Unit tests for sudoku.py — puzzle generation, solver, and uniqueness."""
import random
import unittest

from sudoku import (
    create_empty_board,
    generate_puzzle,
    generate_solved_board,
    _count_solutions,
    _is_valid,
    _solve,
)


# ---------- Helpers ----------

def is_valid_solution(board: list[list[int]]) -> bool:
    """Check that a full 9x9 board is a valid solved Sudoku."""
    # All cells filled 1-9
    for r in range(9):
        for c in range(9):
            if not (1 <= board[r][c] <= 9):
                return False

    # Rows
    for r in range(9):
        if sorted(board[r]) != list(range(1, 10)):
            return False

    # Columns
    for c in range(9):
        if sorted(board[r][c] for r in range(9)) != list(range(1, 10)):
            return False

    # 3x3 boxes
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            box = [board[br + dr][bc + dc] for dr in range(3) for dc in range(3)]
            if sorted(box) != list(range(1, 10)):
                return False
    return True


def empty_count(board: list[list[int]]) -> int:
    return sum(1 for r in range(9) for c in range(9) if board[r][c] == 0)


# ---------- Tests ----------

class TestCreateEmptyBoard(unittest.TestCase):
    """Tests for create_empty_board()."""

    def test_dimensions(self):
        board = create_empty_board()
        self.assertEqual(len(board), 9)
        for row in board:
            self.assertEqual(len(row), 9)

    def test_all_zeros(self):
        board = create_empty_board()
        for row in board:
            for val in row:
                self.assertEqual(val, 0)

    def test_independent_rows(self):
        """Mutating one row must not affect others."""
        board = create_empty_board()
        board[0][0] = 5
        self.assertEqual(board[1][0], 0)


class TestIsValid(unittest.TestCase):
    """Tests for _is_valid()."""

    def setUp(self):
        self.board = create_empty_board()

    def test_empty_board_allows_anything(self):
        for num in range(1, 10):
            self.assertTrue(_is_valid(self.board, 4, 4, num))

    def test_row_conflict(self):
        self.board[0][0] = 5
        self.assertFalse(_is_valid(self.board, 0, 8, 5))

    def test_col_conflict(self):
        self.board[0][0] = 5
        self.assertFalse(_is_valid(self.board, 8, 0, 5))

    def test_box_conflict(self):
        self.board[0][0] = 5
        self.assertFalse(_is_valid(self.board, 2, 2, 5))

    def test_no_conflict_different_row_col_box(self):
        self.board[0][0] = 5
        self.assertTrue(_is_valid(self.board, 3, 3, 5))

    def test_boundary_values(self):
        self.assertTrue(_is_valid(self.board, 0, 0, 1))
        self.assertTrue(_is_valid(self.board, 0, 0, 9))


class TestSolve(unittest.TestCase):
    """Tests for _solve()."""

    def test_solves_empty_board(self):
        board = create_empty_board()
        self.assertTrue(_solve(board))
        self.assertTrue(is_valid_solution(board))

    def test_solves_partial_board(self):
        board = create_empty_board()
        board[0][0] = 5
        board[4][4] = 3
        self.assertTrue(_solve(board))
        self.assertTrue(is_valid_solution(board))
        # Original clues preserved
        self.assertEqual(board[0][0], 5)
        self.assertEqual(board[4][4], 3)

    def test_unsolvable_returns_false(self):
        board = create_empty_board()
        # Create an impossible conflict: two 5s in the same row
        board[0][0] = 5
        board[0][1] = 5
        self.assertFalse(_solve(board))

    def test_does_not_leave_invalid_state(self):
        board = create_empty_board()
        _solve(board)
        self.assertTrue(is_valid_solution(board))


class TestCountSolutions(unittest.TestCase):
    """Tests for _count_solutions()."""

    def test_empty_board_has_many_solutions(self):
        board = create_empty_board()
        self.assertEqual(_count_solutions(board, limit=2), 2)

    def test_solved_board_has_one_solution(self):
        board = generate_solved_board()
        self.assertEqual(_count_solutions(board), 1)

    def test_limit_stops_early(self):
        board = create_empty_board()
        # With limit=1, should stop at first solution
        self.assertEqual(_count_solutions(board, limit=1), 1)

    def test_does_not_mutate_board(self):
        board = create_empty_board()
        board[0][0] = 5
        _count_solutions(board, limit=2)
        # Original board untouched
        self.assertEqual(board[0][0], 5)
        self.assertEqual(empty_count(board), 80)

    def test_ambiguous_puzzle_has_multiple(self):
        """A board with too few clues should have multiple solutions."""
        board = create_empty_board()
        board[0][0] = 5  # only one clue → many solutions
        self.assertEqual(_count_solutions(board, limit=2), 2)


class TestGenerateSolvedBoard(unittest.TestCase):
    """Tests for generate_solved_board()."""

    def test_returns_valid_solution(self):
        board = generate_solved_board()
        self.assertTrue(is_valid_solution(board))

    def test_produces_different_boards(self):
        """Two calls should (almost certainly) produce different boards."""
        random.seed(42)
        b1 = generate_solved_board()
        random.seed(99)
        b2 = generate_solved_board()
        self.assertNotEqual(b1, b2)

    def test_diagonal_boxes_filled_before_solve(self):
        """Diagonal boxes should be permutations of 1-9."""
        random.seed(7)
        board = generate_solved_board()
        for i in (0, 3, 6):
            box = [board[i + dr][i + dc] for dr in range(3) for dc in range(3)]
            self.assertEqual(sorted(box), list(range(1, 10)))


class TestGeneratePuzzle(unittest.TestCase):
    """Tests for generate_puzzle()."""

    def test_returns_tuple_of_two(self):
        result = generate_puzzle()
        self.assertEqual(len(result), 2)

    def test_puzzle_is_subset_of_solution(self):
        puzzle, solution = generate_puzzle(difficulty=30)
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] != 0:
                    self.assertEqual(puzzle[r][c], solution[r][c])

    def test_solution_is_valid(self):
        _, solution = generate_puzzle()
        self.assertTrue(is_valid_solution(solution))

    def test_difficulty_removes_cells(self):
        puzzle, _ = generate_puzzle(difficulty=40)
        self.assertEqual(empty_count(puzzle), 40)

    def test_easy_difficulty(self):
        puzzle, _ = generate_puzzle(difficulty=30)
        self.assertEqual(empty_count(puzzle), 30)

    def test_default_difficulty(self):
        puzzle, _ = generate_puzzle()
        self.assertEqual(empty_count(puzzle), 40)

    def test_unique_solution(self):
        """Every generated puzzle must have exactly one solution."""
        for diff in [30, 40, 50]:
            with self.subTest(difficulty=diff):
                puzzle, _ = generate_puzzle(difficulty=diff)
                self.assertEqual(_count_solutions(puzzle, limit=2), 1)

    def test_high_difficulty_may_not_reach_target(self):
        """Expert difficulty may not remove all requested cells while
        maintaining uniqueness — just verify it removes a reasonable amount."""
        puzzle, _ = generate_puzzle(difficulty=58)
        removed = empty_count(puzzle)
        self.assertGreaterEqual(removed, 50)
        self.assertEqual(_count_solutions(puzzle, limit=2), 1)

    def test_puzzle_has_no_duplicates_in_units(self):
        """No row, column, or box should have duplicate non-zero values."""
        puzzle, _ = generate_puzzle(difficulty=40)
        # Rows
        for r in range(9):
            vals = [v for v in puzzle[r] if v != 0]
            self.assertEqual(len(vals), len(set(vals)))
        # Columns
        for c in range(9):
            vals = [puzzle[r][c] for r in range(9) if puzzle[r][c] != 0]
            self.assertEqual(len(vals), len(set(vals)))
        # Boxes
        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                box = [puzzle[br + dr][bc + dc] for dr in range(3) for dc in range(3) if puzzle[br + dr][bc + dc] != 0]
                self.assertEqual(len(box), len(set(box)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
