from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from github_summary.github_client import GitHubService
from github_summary.models import (
    FilterConfig,
    ReleaseFilterConfig,
    RepoConfig,
)


@pytest.fixture
async def github_service():
    """Create GitHub service with retry disabled for tests."""
    return GitHubService(token="test_token")


@pytest.fixture
def sample_release_response():
    """Sample GitHub API response for releases"""
    return {
        "data": {
            "repository": {
                "releases": {
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                    "nodes": [
                        {
                            "id": "1",
                            "name": "v1.0.0",
                            "tagName": "v1.0.0",
                            "description": "Initial release",
                            "publishedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                            "url": "https://github.com/owner/repo/releases/tag/v1.0.0",
                            "author": {"login": "test_author"},
                        }
                    ],
                }
            }
        }
    }


@pytest.fixture
def sample_repo_config():
    """Create a sample repository configuration"""
    return RepoConfig(name="owner/repo", include_releases=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_service_releases(sample_release_response, github_service, sample_repo_config):
    """Test fetching releases from GitHub API"""
    with patch("gidgethub.httpx.GitHubAPI.graphql") as mock_graphql:
        mock_graphql.return_value = sample_release_response["data"]

        filters = FilterConfig()
        async with github_service as service:
            releases = await service.get_releases(
                sample_repo_config, filters, since=datetime.now(UTC) - timedelta(days=7)
            )

        assert len(releases) == 1
        assert releases[0].author == "test_author"
        assert releases[0].name == "v1.0.0"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_service_releases_exclude_regex(github_service):
    """Test release filtering with regex exclusion."""
    response_data = {
        "repository": {
            "releases": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": [
                    {
                        "id": "1",
                        "name": "v1.0.0",
                        "tagName": "v1.0.0",
                        "description": "Initial release",
                        "publishedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "url": "https://github.com/owner/repo/releases/tag/v1.0.0",
                        "author": {"login": "test_author"},
                    },
                    {
                        "id": "2",
                        "name": "v1.1.0-alpha",
                        "tagName": "v1.1.0-alpha",
                        "description": "Alpha release",
                        "publishedAt": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                        "url": "https://github.com/owner/repo/releases/tag/v1.1.0-alpha",
                        "author": {"login": "test_author"},
                    },
                ],
            }
        }
    }

    with patch("gidgethub.httpx.GitHubAPI.graphql") as mock_graphql:
        mock_graphql.return_value = response_data

        filters = FilterConfig(releases=ReleaseFilterConfig(exclude_release_names_regex="alpha"))
        repo_config = RepoConfig(name="owner/repo", include_releases=True)

        async with github_service as service:
            releases = await service.get_releases(repo_config, filters, since=datetime.now(UTC) - timedelta(days=7))

        assert len(releases) == 1
        assert releases[0].name == "v1.0.0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_github_service_releases_disabled(github_service):
    """Test that releases are not fetched when disabled."""
    repo = RepoConfig(name="owner/repo", include_releases=False)
    filters = FilterConfig()
    async with github_service as service:
        releases = await service.get_releases(repo, filters, since=datetime.now(UTC) - timedelta(days=7))
    assert len(releases) == 0
