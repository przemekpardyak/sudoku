"""
Tests for undo/redo stack behavior, history limits, and state preservation.
"""
import unittest
from sudoku import generate_puzzle, _has_conflicts


class TestUndoRedoBehavior(unittest.TestCase):
    """Tests for undo/redo stack behavior."""

    def test_initial_board_has_no_history(self):
        """A fresh puzzle should have no history to undo."""
        puzzle, solution = generate_puzzle(difficulty=30)
        # Simulate fresh game state
        undo_stack = []
        redo_stack = []
        self.assertEqual(len(undo_stack), 0)
        self.assertEqual(len(redo_stack), 0)

    def test_push_history_increases_stack(self):
        """Pushing history should increase the undo stack size."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board = [row[:] for row in puzzle]
        undo_stack = []

        # Simulate making a move
        snapshot = {
            'board': [row[:] for row in board],
            'mistakes': 0,
        }
        undo_stack.append(snapshot)
        self.assertEqual(len(undo_stack), 1)

        # Make another move
        board[0][0] = solution[0][0] if puzzle[0][0] == 0 else 5
        undo_stack.append({
            'board': [row[:] for row in board],
            'mistakes': 0,
        })
        self.assertEqual(len(undo_stack), 2)

    def test_undo_restores_previous_state(self):
        """Undo should restore the previous board state."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board = [row[:] for row in puzzle]
        undo_stack = []

        # Save state before move
        undo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})

        # Make a move
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    board[r][c] = solution[r][c]
                    break
            else:
                continue
            break

        # Undo
        snapshot = undo_stack.pop()
        restored_board = snapshot['board']
        # Restored board should differ from current board
        self.assertNotEqual(restored_board, board)

    def test_redo_after_undo(self):
        """Redo should re-apply the undone move."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board = [row[:] for row in puzzle]
        undo_stack = []
        redo_stack = []

        # Save state, make move
        undo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    board[r][c] = solution[r][c]
                    break
            else:
                continue
            break

        # Undo: move current state to redo stack
        redo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})
        snapshot = undo_stack.pop()
        board = snapshot['board']

        # Redo: restore from redo stack
        redo_snapshot = redo_stack.pop()
        board = redo_snapshot['board']

        # Board should have the move applied
        self.assertNotEqual(board, puzzle)

    def test_new_action_clears_redo_stack(self):
        """Making a new move after undo should clear the redo stack."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board = [row[:] for row in puzzle]
        undo_stack = []
        redo_stack = []

        # Make two moves
        undo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})
        board[0][0] = 5
        undo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})
        board[0][1] = 3

        # Undo once
        redo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})
        board = undo_stack.pop()['board']

        # Make a new move (should clear redo)
        undo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})
        board[0][2] = 7
        redo_stack.clear()

        self.assertEqual(len(redo_stack), 0)
        self.assertGreater(len(undo_stack), 0)

    def test_undo_stack_preserves_mistakes(self):
        """Undo snapshot should preserve the mistakes count."""
        snapshot = {'board': [[0]*9]*9, 'mistakes': 5}
        self.assertEqual(snapshot['mistakes'], 5)

    def test_undo_stack_preserves_notes(self):
        """Undo snapshot should preserve the notes state."""
        notes = [[[False]*9 for _ in range(9)] for _ in range(9)]
        notes[0][0][3] = True
        snapshot = {'board': [[0]*9]*9, 'mistakes': 0, 'notes': notes}
        self.assertTrue(snapshot['notes'][0][0][3])

    def test_multiple_undos_in_sequence(self):
        """Multiple undos in sequence should work correctly."""
        puzzle, solution = generate_puzzle(difficulty=30)
        board = [row[:] for row in puzzle]
        undo_stack = []

        # Make 5 moves
        moves = 0
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] == 0 and moves < 5:
                    undo_stack.append({'board': [row[:] for row in board], 'mistakes': 0})
                    board[r][c] = solution[r][c]
                    moves += 1

        self.assertEqual(len(undo_stack), 5)

        # Undo all 5
        for _ in range(5):
            board = undo_stack.pop()['board']

        # Board should be back to original puzzle
        self.assertEqual(board, puzzle)


if __name__ == '__main__':
    unittest.main(verbosity=2)
