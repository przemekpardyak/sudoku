"""Integration tests for the Flask app's game persistence API."""
import json
import unittest

from app import app
from storage import get_storage, InMemoryStorage


class TestGamePersistenceAPI(unittest.TestCase):
    """Integration tests for /api/games endpoints."""

    def setUp(self):
        # Use in-memory storage for tests
        import storage as storage_module
        storage_module._storage = InMemoryStorage()

        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

        self.sample_state = {
            "puzzle": [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                       [0, 3, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 9, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0]],
            "solution": [[5, 7, 1, 2, 4, 3, 6, 8, 9],
                         [8, 3, 2, 5, 7, 9, 1, 4, 6],
                         [4, 6, 9, 1, 2, 8, 3, 5, 7],
                         [1, 2, 3, 4, 5, 6, 7, 8, 9],
                         [2, 4, 5, 7, 8, 1, 9, 3, 6],
                         [3, 8, 7, 9, 6, 5, 2, 1, 4],
                         [6, 1, 4, 3, 9, 7, 8, 2, 5],
                         [7, 5, 8, 6, 1, 2, 4, 9, 3],
                         [9, 7, 6, 8, 3, 4, 5, 7, 1]],
            "board": [[5, 0, 1, 0, 0, 0, 0, 0, 0],
                      [0, 3, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 9, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0]],
            "given": [[True, False, True, False, False, False, False, False, False],
                      [False, True, False, False, False, False, False, False, False],
                      [False, False, True, False, False, False, False, False, False],
                      [False, False, False, False, False, False, False, False, False],
                      [False, False, False, False, False, False, False, False, False],
                      [False, False, False, False, False, False, False, False, False],
                      [False, False, False, False, False, False, False, False, False],
                      [False, False, False, False, False, False, False, False, False],
                      [False, False, False, False, False, False, False, False, False]],
            "notes": [[[False] * 9 for _ in range(9)] for _ in range(9)],
            "undoStack": [],
            "redoStack": [],
            "mistakes": 0,
            "elapsed": 0,
            "difficulty": 40,
            "completed": False,
        }

    def test_create_game(self):
        """POST /api/games creates a game and returns 201."""
        res = self.client.post("/api/games",
                               data=json.dumps(self.sample_state),
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("game_id", data)
        self.assertTrue(len(data["game_id"]) > 0)

    def test_get_game(self):
        """GET /api/games/<id> returns the full game state."""
        # Create first
        create_res = self.client.post("/api/games",
                                      data=json.dumps(self.sample_state),
                                      content_type="application/json")
        game_id = create_res.get_json()["game_id"]

        # Retrieve
        res = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["difficulty"], 40)
        self.assertEqual(data["puzzle"][0][0], 5)

    def test_get_nonexistent_game_returns_404(self):
        """GET /api/games/<nonexistent> returns 404."""
        res = self.client.get("/api/games/nonexistent-id")
        self.assertEqual(res.status_code, 404)

    def test_save_game(self):
        """PUT /api/games/<id> updates the game state."""
        # Create
        create_res = self.client.post("/api/games",
                                      data=json.dumps(self.sample_state),
                                      content_type="application/json")
        game_id = create_res.get_json()["game_id"]

        # Update
        updated = dict(self.sample_state)
        updated["mistakes"] = 5
        updated["elapsed"] = 300
        res = self.client.put(f"/api/games/{game_id}",
                              data=json.dumps(updated),
                              content_type="application/json")
        self.assertEqual(res.status_code, 200)

        # Verify
        get_res = self.client.get(f"/api/games/{game_id}")
        data = get_res.get_json()
        self.assertEqual(data["mistakes"], 5)
        self.assertEqual(data["elapsed"], 300)

    def test_list_games(self):
        """GET /api/games returns a list of game metadata."""
        # Create a few games
        for i in range(3):
            state = dict(self.sample_state)
            state["mistakes"] = i
            self.client.post("/api/games",
                              data=json.dumps(state),
                              content_type="application/json")

        res = self.client.get("/api/games")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("games", data)
        self.assertEqual(len(data["games"]), 3)
        # Metadata only
        for game in data["games"]:
            self.assertIn("game_id", game)
            self.assertIn("difficulty", game)
            self.assertIn("mistakes", game)
            self.assertNotIn("board", game)
            self.assertNotIn("solution", game)

    def test_delete_game(self):
        """DELETE /api/games/<id> removes the game."""
        # Create
        create_res = self.client.post("/api/games",
                                      data=json.dumps(self.sample_state),
                                      content_type="application/json")
        game_id = create_res.get_json()["game_id"]

        # Delete
        res = self.client.delete(f"/api/games/{game_id}")
        self.assertEqual(res.status_code, 200)

        # Verify it's gone
        get_res = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(get_res.status_code, 404)

    def test_delete_nonexistent_returns_404(self):
        """DELETE /api/games/<nonexistent> returns 404."""
        res = self.client.delete("/api/games/nonexistent-id")
        self.assertEqual(res.status_code, 404)

    def test_save_nonexistent_returns_404(self):
        """PUT /api/games/<nonexistent> returns 404."""
        res = self.client.put("/api/games/nonexistent-id",
                              data=json.dumps(self.sample_state),
                              content_type="application/json")
        self.assertEqual(res.status_code, 404)

    def test_full_roundtrip_with_undo_redo(self):
        """Create, save with undo/redo stacks, retrieve — verify stacks intact."""
        state = dict(self.sample_state)
        state["undoStack"] = [
            {
                "board": [[5, 7, 1] + [0]*6] + [[0]*9]*8,
                "notes": [[[False]*9]*9]*9,
                "given": [[True, True, True] + [False]*6] + [[False]*9]*8,
                "mistakes": 1,
            }
        ]
        state["redoStack"] = []

        # Create
        create_res = self.client.post("/api/games",
                                      data=json.dumps(state),
                                      content_type="application/json")
        game_id = create_res.get_json()["game_id"]

        # Retrieve
        res = self.client.get(f"/api/games/{game_id}")
        data = res.get_json()
        self.assertEqual(len(data["undoStack"]), 1)
        self.assertEqual(data["undoStack"][0]["mistakes"], 1)

    def test_index_page_loads(self):
        """GET / returns the game page HTML."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Sudoku", res.data)

    def test_new_game_endpoint(self):
        """GET /api/new-game returns a puzzle and solution."""
        res = self.client.get("/api/new-game?difficulty=30")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("puzzle", data)
        self.assertIn("solution", data)
        self.assertEqual(len(data["puzzle"]), 9)
        self.assertEqual(len(data["solution"]), 9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
