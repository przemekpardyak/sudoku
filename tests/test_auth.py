"""Tests for the auth module — user registration, password hashing, auth API,
and game scoping by user.

Run with:
    PYTHONUNBUFFERED=1 venv/bin/python3 -m unittest tests.test_auth -v
"""
import json
import unittest

import auth
from auth import (
    create_user,
    authenticate,
    get_user,
    ensure_default_user,
    hash_password,
    verify_password,
    reset_user_store,
)
from storage import InMemoryStorage
import storage as storage_module


class TestPasswordHashing(unittest.TestCase):
    """Tests for the password hashing helpers (hashlib.pbkdf2_hmac)."""

    def test_hash_password_returns_string(self):
        h = hash_password("password")
        self.assertIsInstance(h, str)
        self.assertIn("$", h)  # algo$iterations$salt$hash format

    def test_hash_password_is_salt_based(self):
        """Same password should produce different hashes (random salt)."""
        h1 = hash_password("password")
        h2 = hash_password("password")
        self.assertNotEqual(h1, h2)

    def test_verify_password_correct(self):
        h = hash_password("secret123")
        self.assertTrue(verify_password("secret123", h))

    def test_verify_password_wrong(self):
        h = hash_password("secret123")
        self.assertFalse(verify_password("wrong", h))

    def test_verify_password_empty(self):
        h = hash_password("")
        self.assertTrue(verify_password("", h))
        self.assertFalse(verify_password("x", h))


class TestUserStore(unittest.TestCase):
    """Tests for the in-memory user store CRUD operations."""

    def setUp(self):
        reset_user_store()

    def test_create_user_returns_user_with_id(self):
        user = create_user("alice", "pass123")
        self.assertIn("user_id", user)
        self.assertEqual(user["username"], "alice")
        self.assertTrue(len(user["user_id"]) > 0)

    def test_create_user_stores_hashed_password(self):
        user = create_user("bob", "secret")
        fetched = get_user(user["user_id"])
        self.assertIsNotNone(fetched)
        self.assertNotIn("password", fetched)  # raw password never stored
        self.assertIn("password_hash", fetched)

    def test_create_user_duplicate_raises(self):
        create_user("charlie", "pass1")
        with self.assertRaises(ValueError):
            create_user("charlie", "pass2")

    def test_authenticate_success(self):
        create_user("dave", "mypassword")
        user = authenticate("dave", "mypassword")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "dave")

    def test_authenticate_wrong_password(self):
        create_user("eve", "correct")
        self.assertIsNone(authenticate("eve", "wrong"))

    def test_authenticate_nonexistent_user(self):
        self.assertIsNone(authenticate("ghost", "anything"))

    def test_get_user_nonexistent_returns_none(self):
        self.assertIsNone(get_user("nonexistent-id"))

    def test_get_user_by_id(self):
        created = create_user("frank", "pass")
        fetched = get_user(created["user_id"])
        self.assertEqual(fetched["username"], "frank")


class TestEnsureDefaultUser(unittest.TestCase):
    """Tests for ensure_default_user()."""

    def setUp(self):
        reset_user_store()

    def test_ensure_default_user_creates_if_missing(self):
        ensure_default_user()
        user = authenticate("testuser", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")

    def test_ensure_default_user_idempotent(self):
        ensure_default_user()
        ensure_default_user()  # Should not raise
        user = authenticate("testuser", "password")
        self.assertIsNotNone(user)

    def test_ensure_default_user_does_not_overwrite(self):
        """If testuser exists with a different password, don't overwrite."""
        create_user("testuser", "custompass")
        ensure_default_user()
        # Original password should still work
        user = authenticate("testuser", "custompass")
        self.assertIsNotNone(user)


class TestAuthAPI(unittest.TestCase):
    """Integration tests for /api/register, /api/login, /api/logout, /api/me."""

    def setUp(self):
        reset_user_store()
        storage_module._storage = InMemoryStorage()

        from app import app
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_register_endpoint(self):
        """POST /api/register creates a new user."""
        res = self.client.post("/api/register",
                               data=json.dumps({"username": "newuser", "password": "pass123"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertIn("user_id", data)
        self.assertEqual(data["username"], "newuser")

    def test_register_duplicate_returns_409(self):
        """Registering an existing username should return 409."""
        self.client.post("/api/register",
                         data=json.dumps({"username": "dup", "password": "p1"}),
                         content_type="application/json")
        res = self.client.post("/api/register",
                               data=json.dumps({"username": "dup", "password": "p2"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 409)

    def test_register_missing_fields_returns_400(self):
        res = self.client.post("/api/register",
                               data=json.dumps({"username": "x"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_login_endpoint_success(self):
        """POST /api/login authenticates and sets session."""
        create_user("loginuser", "pass123")
        res = self.client.post("/api/login",
                               data=json.dumps({"username": "loginuser", "password": "pass123"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["username"], "loginuser")

    def test_login_wrong_password_returns_401(self):
        create_user("badlogin", "correct")
        res = self.client.post("/api/login",
                               data=json.dumps({"username": "badlogin", "password": "wrong"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_login_nonexistent_returns_401(self):
        res = self.client.post("/api/login",
                               data=json.dumps({"username": "ghost", "password": "x"}),
                               content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_logout_clears_session(self):
        """POST /api/logout clears the session."""
        create_user("logoutuser", "pass")
        self.client.post("/api/login",
                         data=json.dumps({"username": "logoutuser", "password": "pass"}),
                         content_type="application/json")
        res = self.client.post("/api/logout")
        self.assertEqual(res.status_code, 200)

    def test_me_endpoint_when_not_logged_in(self):
        """GET /api/me returns null user when not logged in."""
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertFalse(data.get("authenticated", True))

    def test_me_endpoint_when_logged_in(self):
        """GET /api/me returns user info when logged in."""
        create_user("meuser", "pass")
        self.client.post("/api/login",
                         data=json.dumps({"username": "meuser", "password": "pass"}),
                         content_type="application/json")
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("authenticated"))
        self.assertEqual(data["username"], "meuser")


class TestGameScoping(unittest.TestCase):
    """Tests that games are scoped by user_id."""

    def setUp(self):
        reset_user_store()
        storage_module._storage = InMemoryStorage()

        from app import app
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

        self.sample_state = {
            "puzzle": [[5, 0, 1] + [0] * 6] + [[0] * 9] * 8,
            "solution": [[5, 7, 1] + [0] * 6] + [[0] * 9] * 8,
            "board": [[5, 0, 1] + [0] * 6] + [[0] * 9] * 8,
            "given": [[True, False, True] + [False] * 6] + [[False] * 9] * 8,
            "notes": [[[False] * 9 for _ in range(9)] for _ in range(9)],
            "undoStack": [],
            "redoStack": [],
            "mistakes": 0,
            "elapsed": 0,
            "difficulty": 40,
            "completed": False,
        }

    def test_game_gets_user_id_when_logged_in(self):
        """Creating a game while logged in attaches user_id."""
        create_user("scope1", "pass")
        self.client.post("/api/login",
                         data=json.dumps({"username": "scope1", "password": "pass"}),
                         content_type="application/json")
        res = self.client.post("/api/games",
                               data=json.dumps(self.sample_state),
                               content_type="application/json")
        game_id = res.get_json()["game_id"]
        game = storage_module._storage.get_game(game_id)
        self.assertIsNotNone(game.get("user_id"))

    def test_list_games_filtered_by_user(self):
        """list_games should only return the current user's games."""
        # Create user A
        create_user("userA", "pass")
        # Create user B
        create_user("userB", "pass")

        # User A creates a game
        self.client.post("/api/login",
                         data=json.dumps({"username": "userA", "password": "pass"}),
                         content_type="application/json")
        res_a = self.client.post("/api/games",
                                 data=json.dumps(self.sample_state),
                                 content_type="application/json")
        game_a_id = res_a.get_json()["game_id"]

        # User B creates a game
        self.client.post("/api/login",
                         data=json.dumps({"username": "userB", "password": "pass"}),
                         content_type="application/json")
        self.client.post("/api/games",
                         data=json.dumps(self.sample_state),
                         content_type="application/json")

        # User A should only see their game
        self.client.post("/api/login",
                         data=json.dumps({"username": "userA", "password": "pass"}),
                         content_type="application/json")
        res = self.client.get("/api/games")
        games = res.get_json()["games"]
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["game_id"], game_a_id)

    def test_storage_list_games_filters_by_user_id(self):
        """Storage layer should filter by user_id when provided."""
        s = InMemoryStorage()
        s.create_game(self.sample_state, user_id="user-1")
        s.create_game(self.sample_state, user_id="user-2")
        s.create_game(self.sample_state, user_id="user-1")

        user1_games = s.list_games(user_id="user-1")
        self.assertEqual(len(user1_games), 2)
        user2_games = s.list_games(user_id="user-2")
        self.assertEqual(len(user2_games), 1)

    def test_storage_list_games_no_filter_returns_all(self):
        """Without user_id filter, all games are returned."""
        s = InMemoryStorage()
        s.create_game(self.sample_state, user_id="user-1")
        s.create_game(self.sample_state, user_id="user-2")
        all_games = s.list_games()
        self.assertEqual(len(all_games), 2)

    def test_migrate_games_to_user(self):
        """migrate_games_to_user assigns user_id to games without one."""
        s = InMemoryStorage()
        # Create games without user_id (simulating legacy data)
        id1 = s.create_game(self.sample_state)
        id2 = s.create_game(self.sample_state)
        s.create_game(self.sample_state, user_id="existing-user")

        count = s.migrate_games_to_user("migrated-user")
        self.assertEqual(count, 2)  # Only the 2 without user_id

        game1 = s.get_game(id1)
        game2 = s.get_game(id2)
        self.assertEqual(game1["user_id"], "migrated-user")
        self.assertEqual(game2["user_id"], "migrated-user")


if __name__ == "__main__":
    unittest.main(verbosity=2)
