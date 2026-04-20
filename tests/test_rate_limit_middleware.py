"""Tests for rate_limit_middleware.py"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from utils.rate_limit_middleware import rate_limited


def make_mock_issue(number=1, repo_full_name="owner/repo"):
    issue = MagicMock()
    issue.number = number
    repo = MagicMock()
    repo.full_name = repo_full_name
    issue.repository = repo
    return issue


def make_mock_gh():
    gh = MagicMock()
    gh.get_repo = MagicMock()
    return gh


class TestRateLimitedDecorator:
    def test_allows_call_within_limit(self):
        """Function should be called normally when under rate limit."""
        mock_fn = MagicMock(return_value="ok")
        issue = make_mock_issue()
        gh = make_mock_gh()

        decorated = rate_limited(max_calls=5, window=60)(mock_fn)
        result = decorated(issue, gh)

        mock_fn.assert_called_once_with(issue, gh)
        assert result == "ok"

    def test_blocks_call_over_limit(self):
        """Function should not be called when rate limit is exceeded."""
        mock_fn = MagicMock(return_value="ok")
        issue = make_mock_issue(number=42, repo_full_name="org/blocked-repo")
        gh = make_mock_gh()

        decorated = rate_limited(max_calls=2, window=60)(mock_fn)

        # Exhaust the limit
        decorated(issue, gh)
        decorated(issue, gh)

        mock_fn.reset_mock()

        # This call should be blocked
        with patch("utils.rate_limit_middleware.post_comment") as mock_post:
            result = decorated(issue, gh)
            mock_post.assert_called_once()
            mock_fn.assert_not_called()
            assert result is None

    def test_different_repos_are_isolated(self):
        """Rate limits should be tracked per repo independently."""
        mock_fn = MagicMock(return_value="ok")
        issue_a = make_mock_issue(number=1, repo_full_name="org/repo-a")
        issue_b = make_mock_issue(number=1, repo_full_name="org/repo-b")
        gh = make_mock_gh()

        decorated = rate_limited(max_calls=1, window=60)(mock_fn)

        decorated(issue_a, gh)
        mock_fn.reset_mock()

        # repo-b should not be affected by repo-a's limit
        result = decorated(issue_b, gh)
        mock_fn.assert_called_once_with(issue_b, gh)
        assert result == "ok"

    def test_post_comment_called_with_issue_info(self):
        """When blocked, post_comment should receive issue and a message string."""
        mock_fn = MagicMock()
        issue = make_mock_issue(number=7, repo_full_name="test/repo")
        gh = make_mock_gh()

        decorated = rate_limited(max_calls=1, window=60)(mock_fn)
        decorated(issue, gh)  # consume limit

        with patch("utils.rate_limit_middleware.post_comment") as mock_post:
            decorated(issue, gh)
            args = mock_post.call_args[0]
            assert args[0] is issue
            assert isinstance(args[1], str)
            assert len(args[1]) > 0

    def test_allows_single_call_at_limit_boundary(self):
        """The Nth call (exactly at max_calls) should still be allowed."""
        mock_fn = MagicMock(return_value="ok")
        issue = make_mock_issue(number=3, repo_full_name="org/boundary-repo")
        gh = make_mock_gh()

        decorated = rate_limited(max_calls=3, window=60)(mock_fn)

        # First two calls
        decorated(issue, gh)
        decorated(issue, gh)
        mock_fn.reset_mock()

        # Third call should still be allowed (exactly at the limit)
        result = decorated(issue, gh)
        mock_fn.assert_called_once_with(issue, gh)
        assert result == "ok"
