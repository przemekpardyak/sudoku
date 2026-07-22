#!/usr/bin/env python3
"""
Setup verification test: ensures the Cloud Run proxy is running and the app is accessible.

Usage:
    PROJECT_ID=ppardyak-new-project PORT=8080 venv/bin/python3 tests/test_proxy_setup.py

This test:
1. Checks if a proxy is running on the specified port
2. If not, starts one via gcloud run services proxy
3. Verifies the app responds with HTTP 200
4. Verifies /api/version returns valid JSON
5. Verifies /api/new-game creates a game
"""
import json
import os
import subprocess
import sys
import time
import unittest
import urllib.request
import urllib.error

PROJECT_ID = os.environ.get("PROJECT_ID", "ppardyak-new-project")
PORT = int(os.environ.get("PORT", "8080"))
REGION = os.environ.get("REGION", "us-central1")
BASE_URL = f"http://localhost:{PORT}"


def is_port_listening(port: int) -> bool:
    """Check if something is listening on the given port."""
    import socket
    try:
        with socket.create_connection(("localhost", port), timeout=2):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def start_proxy(project_id: str, port: int, region: str) -> subprocess.Popen:
    """Start gcloud run services proxy as a background process."""
    print(f"  Starting proxy: gcloud run services proxy sudoku --region={region} --project={project_id} --port={port}")
    proc = subprocess.Popen(
        ["gcloud", "run", "services", "proxy", "sudoku",
         f"--region={region}", f"--project={project_id}", f"--port={port}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    # Wait for proxy to start
    for _ in range(10):
        time.sleep(1)
        if is_port_listening(port):
            print(f"  Proxy is listening on port {port}")
            return proc
    print(f"  ERROR: Proxy did not start on port {port} within 10s")
    return proc


def ensure_proxy() -> subprocess.Popen | None:
    """Ensure a proxy is running. Start one if not."""
    if is_port_listening(PORT):
        print(f"  Proxy already running on port {PORT}")
        return None
    print(f"  No proxy on port {PORT}, starting one...")
    return start_proxy(PROJECT_ID, PORT, REGION)


def http_get(path: str) -> tuple[int, dict | str]:
    """Make an HTTP GET request to the proxy. Returns (status_code, body)."""
    url = f"{BASE_URL}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body
    except urllib.error.URLError as e:
        return 0, str(e)


class TestProxySetup(unittest.TestCase):
    """Verify the proxy setup is working end-to-end."""

    @classmethod
    def setUpClass(cls):
        """Ensure proxy is running before tests."""
        print(f"\n=== Setup Verification for {PROJECT_ID} on port {PORT} ===")
        cls.proxy_proc = ensure_proxy()
        # Give it a moment to fully initialize
        time.sleep(1)

    def test_01_proxy_is_listening(self):
        """Proxy should be listening on the configured port."""
        self.assertTrue(is_port_listening(PORT),
                        f"Nothing listening on port {PORT}")

    def test_02_root_returns_200(self):
        """Root URL should return HTTP 200."""
        status, _ = http_get("/")
        self.assertEqual(status, 200, f"GET / returned {status}")

    def test_03_version_endpoint(self):
        """/api/version should return version info."""
        status, data = http_get("/api/version")
        self.assertEqual(status, 200)
        self.assertIn("version", data)
        self.assertIn("git_commit", data)

    def test_04_new_game_works(self):
        """/api/new-game should create a game."""
        status, data = http_get("/api/new-game")
        self.assertEqual(status, 200)
        self.assertIn("puzzle", data, f"new-game response missing 'puzzle': {data}")
        self.assertIn("solution", data, f"new-game response missing 'solution': {data}")

    def test_05_login_works(self):
        """Login as testuser should succeed."""
        import urllib.request
        url = f"{BASE_URL}/api/login"
        body = json.dumps({"username": "testuser", "password": "password"}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                self.assertIn("user_id", data, f"Login should return user_id: {data}")
                self.assertEqual(data.get("username"), "testuser", f"Login should return username: {data}")
        except urllib.error.HTTPError as e:
            self.fail(f"Login returned {e.code}: {e.read().decode()}")

    @classmethod
    def tearDownClass(cls):
        """Leave proxy running for manual testing."""
        if cls.proxy_proc:
            print(f"\n  Proxy started by test is left running on port {PORT} for manual testing.")
            print(f"  To stop it: kill {cls.proxy_proc.pid}")


if __name__ == "__main__":
    print(f"Project: {PROJECT_ID}")
    print(f"Port: {PORT}")
    print(f"Region: {REGION}")
    print(f"URL: {BASE_URL}")
    print()
    unittest.main(verbosity=2)
