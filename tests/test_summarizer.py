from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from github_summary.main import app as cli_app
from github_summary.models import (
    Commit,
    Discussion,
    Issue,
    PullRequest,
)
from github_summary.summarizer import Summarizer


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarizer():
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_summary.return_value = "Mocked LLM Summary"
    summarizer = Summarizer(llm_client=mock_llm_client, system_prompt="Test prompt")
    commits = [
        Commit(
            sha="123",
            author="test_author",
            message="Test commit",
            date="2025-01-01",
            html_url="https://github.com/owner/repo/commit/123",
        )
    ]
    pull_requests = [
        PullRequest(
            number=101,
            title="Test PR",
            body="Test PR body",
            author="pr_author",
            state="open",
            created_at="2025-01-01",
            merged_at=None,
            html_url="https://github.com/owner/repo/pull/101",
        )
    ]
    issues = [
        Issue(
            number=1,
            title="Test Issue",
            body="Test Issue body",
            author="test_author",
            state="open",
            created_at="2025-01-01",
            html_url="https://github.com/owner/repo/issues/1",
        )
    ]
    discussions = [
        Discussion(
            id="D_kwDOJ-L_c84AAQ",
            title="Test Discussion",
            body="Test Discussion body",
            author="test_author",
            created_at="2025-01-01",
            html_url="https://github.com/owner/repo/discussions/1",
        )
    ]

    info = {
        "repo": "test_owner/test_repo",
        "commits": [c.model_dump() for c in commits],
        "pull_requests": [pr.model_dump() for pr in pull_requests],
        "issues": [i.model_dump() for i in issues],
        "discussions": [d.model_dump() for d in discussions],
    }
    summary = await summarizer.summarize(info, datetime.now(UTC))

    mock_llm_client.generate_summary.assert_called_once()
    assert summary == "Mocked LLM Summary"


@pytest.mark.integration
def test_summarizer_output_json():
    runner = CliRunner()
    with patch("github_summary.main.run_report") as mock_run_report:
        mock_run_report.return_value = None
        result = runner.invoke(cli_app, ["summarize", "--config", "config.toml", "--save"], catch_exceptions=False)
        assert result.exit_code == 0
        mock_run_report.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_with_data():
    """Test summarization with repository data."""
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_summary.return_value = "Generated summary"

    summarizer = Summarizer(
        llm_client=mock_llm_client,
        system_prompt="Test system prompt",
    )

    repo_data = {
        "repo": "test/repo",
        "commits": [{"sha": "abc123"}],
        "pull_requests": [],
        "issues": [],
        "discussions": [],
    }

    since = datetime.now(UTC) - timedelta(days=1)
    result = await summarizer.summarize(repo_data, since)

    assert result == "Generated summary"
    mock_llm_client.generate_summary.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_no_data():
    """Test summarization with no repository data."""
    mock_llm_client = AsyncMock()

    summarizer = Summarizer(
        llm_client=mock_llm_client,
        system_prompt="Test system prompt",
    )

    repo_data = {
        "repo": "test/repo",
        "commits": [],
        "pull_requests": [],
        "issues": [],
        "discussions": [],
    }

    since = datetime.now(UTC) - timedelta(days=1)
    result = await summarizer.summarize(repo_data, since)

    assert result == "No new updates."
    mock_llm_client.generate_summary.assert_not_called()
