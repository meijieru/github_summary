from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from github_summary.github_client import GitHubService
from github_summary.models import (
    CommitFilterConfig,
    FilterConfig,
    RepoConfig,
)


@pytest.fixture
def github_service():
    """Create GitHub service with retry disabled for tests."""
    return GitHubService(token="test_token", enable_retry=False)


@pytest.fixture
def sample_commit_response():
    """Sample GitHub API response for commits"""
    return {
        "data": {
            "repository": {
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {
                                    "oid": "12345",
                                    "messageHeadline": "feat: initial commit",
                                    "author": {
                                        "name": "test_author",
                                        "date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                                    },
                                    "url": "https://github.com/owner/repo/commit/12345",
                                }
                            ],
                        }
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_repo_config():
    """Create a sample repository configuration"""
    return RepoConfig(name="owner/repo", include_commits=True)


@pytest.mark.unit
def test_github_service_commits(sample_commit_response, github_service, sample_repo_config):
    """Test fetching commits from GitHub API"""
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.json.return_value = sample_commit_response
        mock_post.return_value.raise_for_status.return_value = None

        filters = FilterConfig()
        commits = github_service.get_commits(sample_repo_config, filters, since=datetime.now(UTC) - timedelta(days=7))

        assert len(commits) == 1
        assert commits[0].author == "test_author"
        assert commits[0].message == "feat: initial commit"


@pytest.mark.unit
def test_github_service_commits_exclude_regex():
    """Test commit filtering with regex exclusion."""
    github_service = GitHubService(token="test_token", enable_retry=False)

    response_data = {
        "data": {
            "repository": {
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {
                                    "oid": "1",
                                    "messageHeadline": "feat: new feature",
                                    "author": {
                                        "name": "test_author",
                                        "date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                                    },
                                    "url": "https://github.com/owner/repo/commit/1",
                                },
                                {
                                    "oid": "2",
                                    "messageHeadline": "vim-patch: some patch",
                                    "author": {
                                        "name": "test_author",
                                        "date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                                    },
                                    "url": "https://github.com/owner/repo/commit/2",
                                },
                            ],
                        }
                    }
                }
            }
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.json.return_value = response_data
        mock_post.return_value.raise_for_status.return_value = None

        filters = FilterConfig(commits=CommitFilterConfig(exclude_commit_messages_regex="vim-patch"))
        repo_config = RepoConfig(name="owner/repo", include_commits=True)

        commits = github_service.get_commits(repo_config, filters, since=datetime.now(UTC) - timedelta(days=7))

        assert len(commits) == 1
        assert commits[0].message == "feat: new feature"


@pytest.mark.unit
def test_github_service_commits_disabled():
    """Test that commits are not fetched when disabled."""
    service = GitHubService(token="test_token", enable_retry=False)
    repo = RepoConfig(name="owner/repo", include_commits=False)
    filters = FilterConfig()
    commits = service.get_commits(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(commits) == 0


@pytest.mark.unit
def test_retry_disabled_for_tests():
    """Test that retry is properly disabled for test instances."""
    service = GitHubService(token="test_token", enable_retry=False)
    assert service.client.enable_retry is False


@pytest.mark.unit
def test_retry_enabled_by_default():
    """Test that retry is enabled by default."""
    service = GitHubService(token="test_token")
    assert service.client.enable_retry is True
