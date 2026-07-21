"""
Tests for puzzle analysis functionality.
Tests the /api/analyze endpoint that provides detailed puzzle metrics.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestPuzzleAnalysis(unittest.TestCase):
    """Tests for puzzle analysis endpoint."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_analyze_puzzle(self):
        """Analyze endpoint should return puzzle metrics."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
        }), content_type='application/json')
        data = res.get_json()
        self.assertEqual(res.status_code, 200)
        self.assertIn('empty_cells', data)
        self.assertIn('filled_cells', data)
        self.assertIn('difficulty_rating', data)

    def test_analyze_empty_puzzle(self):
        """Analyzing an empty puzzle should return 81 empty cells."""
        empty = [[0]*9 for _ in range(9)]
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': empty,
        }), content_type='application/json')
        data = res.get_json()
        self.assertEqual(data['empty_cells'], 81)
        self.assertEqual(data['filled_cells'], 0)

    def test_analyze_full_puzzle(self):
        """Analyzing a full puzzle should return 81 filled cells."""
        _, solution = generate_puzzle(difficulty=0)
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': solution,
        }), content_type='application/json')
        data = res.get_json()
        self.assertEqual(data['filled_cells'], 81)
        self.assertEqual(data['empty_cells'], 0)

    def test_analyze_clue_count(self):
        """Analysis should report correct number of clues."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
        }), content_type='application/json')
        data = res.get_json()
        filled = sum(1 for r in range(9) for c in range(9) if puzzle[r][c] != 0)
        self.assertEqual(data['filled_cells'], filled)
        self.assertEqual(data['empty_cells'], 81 - filled)

    def test_analyze_has_unique_solution(self):
        """Analysis should check if puzzle has unique solution."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
            'solution': solution,
        }), content_type='application/json')
        data = res.get_json()
        self.assertIn('unique_solution', data)
        self.assertTrue(data['unique_solution'])

    def test_analyze_difficulty_rating(self):
        """Analysis should include a difficulty rating."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
        }), content_type='application/json')
        data = res.get_json()
        self.assertIn('difficulty_rating', data)
        # Rating should be between 1 and 5
        self.assertGreaterEqual(data['difficulty_rating'], 1)
        self.assertLessEqual(data['difficulty_rating'], 5)

    def test_analyze_invalid_board(self):
        """Analyzing an invalid board should return 400."""
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': 'not an array',
        }), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_analyze_wrong_dimensions(self):
        """Analyzing wrong dimensions should return 400."""
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': [[1, 2], [3, 4]],
        }), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_analyze_with_conflicts(self):
        """Analysis should detect conflicts in the puzzle."""
        board = [[0]*9 for _ in range(9)]
        board[0][0] = 5
        board[0][1] = 5  # Conflict in row
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': board,
        }), content_type='application/json')
        data = res.get_json()
        self.assertTrue(data['has_conflicts'])

    def test_analyze_no_conflicts(self):
        """Valid puzzle should have no conflicts."""
        puzzle, _ = generate_puzzle(difficulty=30)
        res = self.client.post('/api/analyze', data=json.dumps({
            'puzzle': puzzle,
        }), content_type='application/json')
        data = res.get_json()
        self.assertFalse(data['has_conflicts'])

    def test_analyze_missing_body(self):
        """Missing body should return 400."""
        res = self.client.post('/api/analyze', content_type='application/json')
        self.assertEqual(res.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
