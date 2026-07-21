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


def _has_conflicts(board: list[list[int]]) -> bool:
    """Check if the board has any duplicate non-zero values in rows, columns, or boxes."""
    # Check rows and columns
    for i in range(9):
        row_vals = [v for v in board[i] if v != 0]
        col_vals = [board[r][i] for r in range(9) if board[r][i] != 0]
        if len(row_vals) != len(set(row_vals)) or len(col_vals) != len(set(col_vals)):
            return True
    # Check 3x3 boxes
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            box = [board[br + dr][bc + dc] for dr in range(3) for dc in range(3) if board[br + dr][bc + dc] != 0]
            if len(box) != len(set(box)):
                return True
    return False


def _solve(board: list[list[int]]) -> bool:
    """Solve the board in place using backtracking. Returns True if solved."""
    if _has_conflicts(board):
        return False
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


def _count_solutions(board: list[list[int]], limit: int = 2) -> int:
    """Count solutions (up to limit) via backtracking. Does not mutate board."""
    if _has_conflicts(board):
        return 0
    work = [row[:] for row in board]
    count = 0

    def backtrack() -> bool:
        nonlocal count
        for row in range(9):
            for col in range(9):
                if work[row][col] == 0:
                    for num in range(1, 10):
                        if _is_valid(work, row, col, num):
                            work[row][col] = num
                            if backtrack():
                                work[row][col] = 0
                                if count >= limit:
                                    return True
                            else:
                                work[row][col] = 0
                    return False
        count += 1
        return True

    backtrack()
    return count


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
        The puzzle is guaranteed to have a unique solution.
    """
    solution = generate_solved_board()
    puzzle = [row[:] for row in solution]

    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)

    removed = 0
    for r, c in cells:
        if removed >= difficulty:
            break
        # Temporarily remove the cell and check uniqueness
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        if _count_solutions(puzzle, limit=2) == 1:
            # Unique solution preserved — keep the removal
            removed += 1
        else:
            # Removing this cell creates ambiguity — restore it
            puzzle[r][c] = backup

    return puzzle, solution
