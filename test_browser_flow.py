"""
Integration test that simulates the browser flow:
1. Load page → new game starts → game should be saved to server
2. Play moves → auto-save should fire
3. Open Load Games → game should appear in list
4. Resume game → state should be restored

This test uses the Flask test client to simulate the browser's fetch() calls.
"""
import json
import unittest
from app import app
from storage import InMemoryStorage, get_storage
import storage as storage_module


class TestBrowserFlow(unittest.TestCase):
    """Simulate the full browser experience: new game, play, save, resume."""

    def setUp(self):
        storage_module._storage = InMemoryStorage()
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_new_game_creates_server_record(self):
        """When a new game starts, POST /api/games should create a record."""
        # Step 1: Get a new puzzle (simulates GET /api/new-game)
        res = self.client.get('/api/new-game?difficulty=40')
        self.assertEqual(res.status_code, 200)
        puzzle_data = res.get_json()
        puzzle = puzzle_data['puzzle']
        solution = puzzle_data['solution']

        # Step 2: Create game on server (simulates createGameOnServer())
        state = {
            'puzzle': puzzle,
            'solution': solution,
            'board': [row[:] for row in puzzle],
            'given': [[v != 0 for v in row] for row in puzzle],
            'notes': [[[False] * 9 for _ in range(9)] for _ in range(9)],
            'undoStack': [],
            'redoStack': [],
            'mistakes': 0,
            'elapsed': 0,
            'difficulty': 40,
            'completed': False,
        }
        res = self.client.post('/api/games',
                               data=json.dumps(state),
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)
        game_id = res.get_json()['game_id']
        self.assertTrue(game_id)

        # Step 3: Game should appear in list immediately
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]['game_id'], game_id)

    def test_play_move_saves_to_server(self):
        """After playing a move, PUT /api/games/<id> should save the new state."""
        # Create game
        puzzle = [[5, 0, 1, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 8
        solution = [[5, 7, 1, 2, 4, 3, 6, 8, 9]] + [[1] * 9] * 8
        state = {
            'puzzle': puzzle, 'solution': solution,
            'board': [row[:] for row in puzzle],
            'given': [[v != 0 for v in row] for row in puzzle],
            'notes': [[[False] * 9] * 9] * 9,
            'undoStack': [], 'redoStack': [],
            'mistakes': 0, 'elapsed': 0, 'difficulty': 40, 'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Simulate playing a move
        state['board'][0][1] = 7
        state['mistakes'] = 0
        state['elapsed'] = 15
        state['undoStack'] = [{
            'board': [row[:] for row in puzzle],
            'notes': [[[False] * 9] * 9] * 9,
            'given': [[v != 0 for v in row] for row in puzzle],
            'mistakes': 0,
        }]

        res = self.client.put(f'/api/games/{game_id}', data=json.dumps(state),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)

        # Verify state was saved
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['board'][0][1], 7)
        self.assertEqual(game['elapsed'], 15)
        self.assertEqual(len(game['undoStack']), 1)

    def test_resume_game_restores_full_state(self):
        """Resuming a game should restore board, notes, undo/redo stacks, timer."""
        # Create and play
        puzzle = [[5, 0, 1, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 8
        solution = [[5, 7, 1, 2, 4, 3, 6, 8, 9]] + [[1] * 9] * 8
        board = [row[:] for row in puzzle]
        board[0][1] = 7
        board[1][0] = 8
        notes = [[[False] * 9] * 9] * 9
        notes[0][2][3] = True  # pencil mark
        undo = [{'board': puzzle, 'notes': [[[False]*9]*9]*9,
                 'given': [[v != 0 for v in row] for row in puzzle], 'mistakes': 0}]
        redo = []
        state = {
            'puzzle': puzzle, 'solution': solution, 'board': board,
            'given': [[v != 0 for v in row] for row in puzzle],
            'notes': notes, 'undoStack': undo, 'redoStack': redo,
            'mistakes': 2, 'elapsed': 120, 'difficulty': 40, 'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Resume: GET the game
        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertEqual(game['board'][0][1], 7)
        self.assertEqual(game['board'][1][0], 8)
        self.assertTrue(game['notes'][0][2][3])
        self.assertEqual(game['mistakes'], 2)
        self.assertEqual(game['elapsed'], 120)
        self.assertEqual(len(game['undoStack']), 1)
        self.assertEqual(len(game['redoStack']), 0)

    def test_delete_game_removes_from_list(self):
        """After deleting, the game should not appear in the list."""
        state = {'difficulty': 40, 'mistakes': 0, 'elapsed': 0}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Delete
        res = self.client.delete(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 200)

        # Not in list
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertEqual(len(games), 0)

        # Not retrievable
        res = self.client.get(f'/api/games/{game_id}')
        self.assertEqual(res.status_code, 404)

    def test_multiple_games_in_list(self):
        """Multiple games should all appear in the list, ordered by updated_at."""
        for i in range(3):
            state = {'difficulty': 30 + i * 10, 'mistakes': i, 'elapsed': i * 100}
            self.client.post('/api/games', data=json.dumps(state),
                             content_type='application/json')

        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertEqual(len(games), 3)
        # Should have different difficulties
        diffs = [g['difficulty'] for g in games]
        self.assertIn(30, diffs)
        self.assertIn(40, diffs)
        self.assertIn(50, diffs)

    def test_completed_game_saved(self):
        """A completed game should be saved with completed=True."""
        state = {
            'puzzle': [[5, 0], [0, 3]],
            'solution': [[5, 7], [8, 3]],
            'board': [[5, 7], [8, 3]],
            'difficulty': 40, 'mistakes': 2, 'elapsed': 300,
            'completed': True,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        res = self.client.get(f'/api/games/{game_id}')
        game = res.get_json()
        self.assertTrue(game['completed'])

        # Also check in list view
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        self.assertTrue(games[0]['completed'])

    def test_save_with_empty_state(self):
        """Saving with minimal state should not crash."""
        state = {'difficulty': 40}
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')
        self.assertEqual(res.status_code, 201)

    def test_progress_shows_correctly(self):
        """Progress should show solved/total_empty format."""
        puzzle = [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                  [0, 3, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 9, 0, 0, 0, 0, 0, 0]] + [[0] * 9] * 6
        board = [row[:] for row in puzzle]
        board[0][1] = 7  # user fills one cell
        state = {
            'puzzle': puzzle,
            'board': board,
            'difficulty': 40, 'mistakes': 0, 'elapsed': 10, 'completed': False,
        }
        res = self.client.post('/api/games', data=json.dumps(state),
                               content_type='application/json')

        res = self.client.get('/api/games')
        game = res.get_json()['games'][0]
        # puzzle has 77 empty cells, user filled 1
        self.assertEqual(game['progress'], '1/77')

    def test_update_nonexistent_returns_404(self):
        """PUT to a non-existent game ID should return 404."""
        res = self.client.put('/api/games/nonexistent',
                              data=json.dumps({'mistakes': 1}),
                              content_type='application/json')
        self.assertEqual(res.status_code, 404)

    def test_create_and_immediately_list(self):
        """Game should be visible in list immediately after creation."""
        # Create
        res = self.client.post('/api/games',
                               data=json.dumps({'difficulty': 30}),
                               content_type='application/json')
        game_id = res.get_json()['game_id']

        # Immediately list
        res = self.client.get('/api/games')
        games = res.get_json()['games']
        found = [g for g in games if g['game_id'] == game_id]
        self.assertEqual(len(found), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
