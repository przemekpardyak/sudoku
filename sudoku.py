"""Sudoku puzzle generator and solver."""
import random


def create_empty_board() -> list[list[int]]:
    """Return a 9x9 board filled with zeros."""
    return [[0 for _ in range(9)] for _ in range(9)]


def _is_valid(board: list[list[int]], row: int, col: int, num: int) -> bool:
    """Check whether num can be placed at board[row][col]."""
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
    box_row, box_col = (row // 3) * 3, (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if board[r][c] == num:
                return False
    return True


def _solve(board: list[list[int]]) -> bool:
    """Solve the board in place using backtracking. Returns True if solved."""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if _is_valid(board, row, col, num):
                        board[row][col] = num
                        if _solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True


def generate_solved_board() -> list[list[int]]:
    """Generate a fully solved, randomized sudoku board."""
    board = create_empty_board()

    def fill_diagonal_boxes() -> None:
        for i in range(0, 9, 3):
            nums = list(range(1, 10))
            random.shuffle(nums)
            idx = 0
            for r in range(i, i + 3):
                for c in range(i, i + 3):
                    board[r][c] = nums[idx]
                    idx += 1

    fill_diagonal_boxes()
    _solve(board)
    return board


def generate_puzzle(difficulty: int = 40) -> tuple[list[list[int]], list[list[int]]]:
    """Generate a sudoku puzzle and its solution.

    Args:
        difficulty: Number of cells to remove (higher = harder).

    Returns:
        Tuple of (puzzle, solution) where puzzle has zeros for empty cells.
    """
    solution = generate_solved_board()
    puzzle = [row[:] for row in solution]

    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)

    removed = 0
    for r, c in cells:
        if removed >= difficulty:
            break
        puzzle[r][c] = 0
        removed += 1

    return puzzle, solution
