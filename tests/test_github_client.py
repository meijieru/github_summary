from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from github_summary.github_client import GitHubService
from github_summary.models import (
    CommitFilterConfig,
    FilterConfig,
    RepoConfig,
)


@pytest.fixture
async def github_service():
    """Create GitHub service with retry disabled for tests."""
    return GitHubService(token="test_token")


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_service_commits(sample_commit_response, github_service, sample_repo_config):
    """Test fetching commits from GitHub API"""
    with patch("gidgethub.httpx.GitHubAPI.graphql") as mock_graphql:
        mock_graphql.return_value = sample_commit_response["data"]

        filters = FilterConfig()
        async with github_service as service:
            commits = await service.get_commits(
                sample_repo_config, filters, since=datetime.now(UTC) - timedelta(days=7)
            )

        assert len(commits) == 1
        assert commits[0].author == "test_author"
        assert commits[0].message == "feat: initial commit"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_service_commits_exclude_regex(github_service):
    """Test commit filtering with regex exclusion."""
    response_data = {
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

    with patch("gidgethub.httpx.GitHubAPI.graphql") as mock_graphql:
        mock_graphql.return_value = response_data

        filters = FilterConfig(commits=CommitFilterConfig(exclude_commit_messages_regex="vim-patch"))
        repo_config = RepoConfig(name="owner/repo", include_commits=True)

        async with github_service as service:
            commits = await service.get_commits(repo_config, filters, since=datetime.now(UTC) - timedelta(days=7))

        assert len(commits) == 1
        assert commits[0].message == "feat: new feature"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_github_service_commits_disabled(github_service):
    """Test that commits are not fetched when disabled."""
    repo = RepoConfig(name="owner/repo", include_commits=False)
    filters = FilterConfig()
    async with github_service as service:
        commits = await service.get_commits(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(commits) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager functionality."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        with patch("gidgethub.httpx.GitHubAPI"):
            service = GitHubService("test_token")

            async with service as gh_service:
                assert gh_service.session is not None
                assert gh_service.gh_client is not None

            # Verify cleanup was called
            mock_client.aclose.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limit_access():
    """Test rate limit information access."""
    with patch("httpx.AsyncClient") as mock_client_class, patch("gidgethub.httpx.GitHubAPI") as mock_github_api:
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_rate_limit = MagicMock()
        mock_rate_limit.remaining = 4000
        mock_rate_limit.limit = 5000

        mock_api_instance = MagicMock()
        mock_api_instance.rate_limit = mock_rate_limit
        mock_github_api.return_value = mock_api_instance

        service = GitHubService("test_token")

        async with service as gh_service:
            gh_service.gh_client = mock_api_instance
            if gh_service.rate_limit:
                assert gh_service.rate_limit.remaining == 4000
                assert gh_service.rate_limit.limit == 5000
