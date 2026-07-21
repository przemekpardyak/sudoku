"""
Tests for export/import integrity with complex game states.
Tests that all game fields survive the export → import roundtrip.
"""
import json
import copy
import unittest
from app import app
from storage import InMemoryStorage
import storage as storage_module
from sudoku import generate_puzzle


class TestExportImportIntegrity(unittest.TestCase):
    """Tests for export/import data integrity."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_export_import_preserves_puzzle(self):
        """Puzzle should survive export/import."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': copy.deepcopy(puzzle), 'difficulty': 30,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{game_id}/export')
        share_code = export.get_json()['share_code']

        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        imported_id = import_res.get_json()['game_id']

        imported = self.client.get(f'/api/games/{imported_id}').get_json()
        self.assertEqual(imported['puzzle'], puzzle)

    def test_export_import_preserves_solution(self):
        """Solution should survive export/import."""
        puzzle, solution = generate_puzzle(difficulty=30)
        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': solution, 'difficulty': 30,
            'completed': True, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{game_id}/export')
        share_code = export.get_json()['share_code']

        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        imported_id = import_res.get_json()['game_id']

        imported = self.client.get(f'/api/games/{imported_id}').get_json()
        self.assertEqual(imported['solution'], solution)

    def test_export_import_preserves_metadata(self):
        """Metadata (difficulty, elapsed, mistakes) should survive."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 40, 'elapsed': 250, 'mistakes': 3,
            'hintsUsed': 2, 'completed': True, 'rating': 4,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{game_id}/export')
        share_code = export.get_json()['share_code']

        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': share_code,
        }), content_type='application/json')
        imported = self.client.get(f'/api/games/{import_res.get_json()["game_id"]}').get_json()

        self.assertEqual(imported['difficulty'], 40)
        self.assertEqual(imported['elapsed'], 250)
        self.assertEqual(imported['mistakes'], 3)
        self.assertEqual(imported['hintsUsed'], 2)
        self.assertTrue(imported['completed'])
        self.assertEqual(imported['rating'], 4)

    def test_export_import_preserves_tags(self):
        """Tags should survive export/import."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'tags': ['fun', 'quick', 'challenge'],
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{game_id}/export')
        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': export.get_json()['share_code'],
        }), content_type='application/json')
        imported = self.client.get(f'/api/games/{import_res.get_json()["game_id"]}').get_json()

        self.assertEqual(imported['tags'], ['fun', 'quick', 'challenge'])

    def test_export_import_preserves_notes(self):
        """Notes should survive export/import."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'notes': 'This was a challenging puzzle!',
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{game_id}/export')
        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': export.get_json()['share_code'],
        }), content_type='application/json')
        imported = self.client.get(f'/api/games/{import_res.get_json()["game_id"]}').get_json()

        self.assertEqual(imported['notes'], 'This was a challenging puzzle!')

    def test_export_import_different_ids(self):
        """Exported and imported games should have different IDs."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30,
        }), content_type='application/json')
        original_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{original_id}/export')
        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': export.get_json()['share_code'],
        }), content_type='application/json')
        imported_id = import_res.get_json()['game_id']

        self.assertNotEqual(original_id, imported_id)

    def test_export_import_multiple_times(self):
        """Importing the same share code multiple times should create unique games."""
        res = self.client.post('/api/games', data=json.dumps({
            'difficulty': 30, 'elapsed': 100,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{game_id}/export')
        share_code = export.get_json()['share_code']

        ids = set()
        for _ in range(3):
            import_res = self.client.post('/api/games/import', data=json.dumps({
                'share_code': share_code,
            }), content_type='application/json')
            ids.add(import_res.get_json()['game_id'])

        self.assertEqual(len(ids), 3)

    def test_export_import_full_state(self):
        """Full game state with all fields should survive roundtrip."""
        puzzle, solution = generate_puzzle(difficulty=40)
        board = copy.deepcopy(puzzle)
        # Fill some cells
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and (r + c) % 3 == 0:
                    board[r][c] = solution[r][c]

        res = self.client.post('/api/games', data=json.dumps({
            'puzzle': puzzle, 'solution': solution,
            'board': board, 'difficulty': 40,
            'elapsed': 180, 'mistakes': 2, 'hintsUsed': 1,
            'completed': False, 'tags': ['hard'],
            'notes': 'In progress', 'favorite': True,
        }), content_type='application/json')
        game_id = res.get_json()['game_id']

        export = self.client.get(f'/api/games/{game_id}/export')
        import_res = self.client.post('/api/games/import', data=json.dumps({
            'share_code': export.get_json()['share_code'],
        }), content_type='application/json')
        imported = self.client.get(f'/api/games/{import_res.get_json()["game_id"]}').get_json()

        self.assertEqual(imported['difficulty'], 40)
        self.assertEqual(imported['elapsed'], 180)
        self.assertEqual(imported['mistakes'], 2)
        self.assertEqual(imported['hintsUsed'], 1)
        self.assertFalse(imported['completed'])
        self.assertEqual(imported['tags'], ['hard'])
        self.assertEqual(imported['notes'], 'In progress')
        self.assertTrue(imported['favorite'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
