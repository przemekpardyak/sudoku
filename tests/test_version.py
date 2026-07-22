"""
Tests for the /api/version endpoint and app version display.
"""
import unittest
from app import app


class TestVersionAPI(unittest.TestCase):
    """Tests for the /api/version endpoint."""

    def setUp(self):
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    def test_version_endpoint_returns_200(self):
        """Should return 200 with version info."""
        res = self.client.get('/api/version')
        self.assertEqual(res.status_code, 200)

    def test_version_returns_version_field(self):
        """Should include a 'version' field in the response."""
        res = self.client.get('/api/version')
        data = res.get_json()
        self.assertIn('version', data)
        self.assertIsInstance(data['version'], str)
        self.assertGreater(len(data['version']), 0)

    def test_version_returns_git_commit(self):
        """Should include 'git_commit' field."""
        res = self.client.get('/api/version')
        data = res.get_json()
        self.assertIn('git_commit', data)

    def test_version_returns_deployed_at(self):
        """Should include 'deployed_at' timestamp."""
        res = self.client.get('/api/version')
        data = res.get_json()
        self.assertIn('deployed_at', data)

    def test_version_format_is_semver(self):
        """Version should follow semantic versioning (e.g., 1.0.0)."""
        res = self.client.get('/api/version')
        data = res.get_json()
        version = data['version']
        parts = version.split('.')
        self.assertGreaterEqual(len(parts), 2,
                                f"Version '{version}' should have at least major.minor")

    def test_git_commit_is_valid_format(self):
        """Git commit should be a 7+ char hex string or 'unknown'."""
        import re
        res = self.client.get('/api/version')
        data = res.get_json()
        git_commit = data['git_commit']
        self.assertTrue(
            re.match(r'^[0-9a-f]{7,}$', git_commit) or git_commit == 'unknown',
            f"Git commit '{git_commit}' should be a hex hash or 'unknown'"
        )

    def test_deployed_at_is_string(self):
        """deployed_at should be a string (may be empty if env var not set)."""
        res = self.client.get('/api/version')
        data = res.get_json()
        self.assertIsInstance(data['deployed_at'], str)

    def test_index_page_contains_version(self):
        """The rendered index page should contain the app version string."""
        from app import APP_VERSION
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(APP_VERSION, res.data.decode('utf-8'),
                      f"Index page should contain version '{APP_VERSION}'")


if __name__ == '__main__':
    unittest.main(verbosity=2)
