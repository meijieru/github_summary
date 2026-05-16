from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from github_summary.models import (
    Commit,
    Discussion,
    Issue,
    LLMConfig,
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
    """Test summarizer integration with new architecture."""
    # This test is now covered by test_app.py and test_cli.py
    # Removed old CLI testing that relied on deprecated functions
    pass


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
async def test_summarizer_prompt_uses_concise_high_signal_structure():
    """Ensure the generated prompt uses the revised high-signal structure."""
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_summary.return_value = "Generated summary"

    summarizer = Summarizer(
        llm_client=mock_llm_client,
        system_prompt=LLMConfig(base_url=None, api_key=None).system_prompt,
        audience="mixed",
    )

    repo_data = {
        "repo": "test/repo",
        "commits": [],
        "pull_requests": [],
        "issues": [],
        "discussions": [],
        "releases": [],
    }

    await summarizer.summarize(repo_data, None)

    system_prompt, prompt = mock_llm_client.generate_summary.call_args.args
    assert "high-signal GitHub activity summaries" in system_prompt
    assert "Balance user impact with brief technical context." in system_prompt
    assert "## TL;DR" in prompt
    assert "- 2-4 bullets only." in prompt
    assert "## Details" in prompt
    assert "Treat open pull requests as active developments only." in prompt
    assert "## Watchlist" in prompt
    assert prompt.index("## TL;DR") < prompt.index("## Details")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarizer_prompt_includes_language_and_last_run_context():
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_summary.return_value = "Generated summary"

    summarizer = Summarizer(
        llm_client=mock_llm_client,
        system_prompt=LLMConfig(base_url=None, api_key=None).system_prompt,
        audience="user",
        language="Chinese",
    )

    await summarizer.summarize({"repo": "test/repo"}, datetime(2025, 1, 1, tzinfo=UTC))

    system_prompt, prompt = mock_llm_client.generate_summary.call_args.args
    assert "Write the final summary in Chinese." in system_prompt
    assert "Optimize for practical user impact" in system_prompt
    assert "The previous successful run was at 2025-01-01 00:00:00 UTC." in prompt
