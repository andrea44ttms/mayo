"""Tests for core webhook handler functions in api/index.py."""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_repo(full_name="owner/repo"):
    repo = MagicMock()
    repo.full_name = full_name
    return repo


def make_mock_issue(number=1, title="Test issue", body="Do something", state="open"):
    issue = MagicMock()
    issue.number = number
    issue.title = title
    issue.body = body
    issue.state = state
    issue.pull_request = None
    return issue


def make_mock_pr(number=2, title="Test PR", body="Fix something", state="open"):
    pr = MagicMock()
    pr.number = number
    pr.title = title
    pr.body = body
    pr.state = state
    return pr


# ---------------------------------------------------------------------------
# co_author_msg
# ---------------------------------------------------------------------------

class TestCoAuthorMsg:
    def test_returns_string(self):
        from api.index import co_author_msg
        result = co_author_msg("testuser")
        assert isinstance(result, str)

    def test_contains_username(self):
        from api.index import co_author_msg
        result = co_author_msg("octocat")
        assert "octocat" in result

    def test_format(self):
        from api.index import co_author_msg
        result = co_author_msg("octocat")
        # Should follow the Git co-author trailer convention
        assert "Co-authored-by:" in result


# ---------------------------------------------------------------------------
# verify_signature
# ---------------------------------------------------------------------------

class TestVerifySignature:
    def test_valid_signature(self):
        import hmac
        import hashlib
        from api.index import verify_signature

        secret = "mysecret"
        payload = b'{"action": "opened"}'
        sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        with patch("api.index.WEBHOOK_SECRET", secret):
            assert verify_signature(payload, sig) is True

    def test_invalid_signature(self):
        from api.index import verify_signature

        payload = b'{"action": "opened"}'
        bad_sig = "sha256=" + "0" * 64

        with patch("api.index.WEBHOOK_SECRET", "mysecret"):
            assert verify_signature(payload, bad_sig) is False

    def test_missing_signature(self):
        from api.index import verify_signature

        payload = b'{"action": "opened"}'

        with patch("api.index.WEBHOOK_SECRET", "mysecret"):
            assert verify_signature(payload, None) is False

    def test_malformed_signature(self):
        from api.index import verify_signature

        payload = b'{"action": "opened"}'

        with patch("api.index.WEBHOOK_SECRET", "mysecret"):
            # A signature without the expected "sha256=" prefix should be rejected
            assert verify_signature(payload, "deadbeef") is False
