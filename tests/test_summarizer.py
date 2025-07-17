from datetime import UTC, datetime
from unittest.mock import Mock, patch

from github_summary.config import Config
from github_summary.main import app as cli_app
from github_summary.models import (
    Commit,
    Discussion,
    GitHubConfig,
    Issue,
    PullRequest,
    RepoConfig,
)
from github_summary.summarizer import Summarizer


def test_summarizer():
    mock_llm_client = Mock()
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
    summary = summarizer.summarize(info, datetime.now(UTC))

    mock_llm_client.generate_summary.assert_called_once()
    assert summary == "Mocked LLM Summary"


def test_summarizer_output_json():
    mock_llm_client = Mock()
    summarizer_instance = Summarizer(llm_client=mock_llm_client, system_prompt="Test prompt")

    # Create a proper Config object
    test_repo_config = RepoConfig(name="test_owner/test_repo")
    mock_config = Config(
        repositories=[test_repo_config],
        output_dir="output",
        log_level="INFO",
        since_last_run=True,
        github=GitHubConfig(token="mock_token"),
    )

    mock_service = Mock()

    with (
        patch("github_summary.actions._get_services", return_value=(mock_config, mock_service, summarizer_instance)),
        patch("json.dump") as mock_json_dump,
        patch("github_summary.actions.set_last_run_time") as mock_set_last_run_time,
        patch.object(summarizer_instance, "summarize", return_value="Mocked LLM Summary") as mock_summarize_method,
    ):
        mock_service.get_commits.return_value = [
            Commit(
                sha="123",
                author="test_author",
                message="Test commit",
                date="2025-01-01",
                html_url="https://github.com/owner/repo/commit/123",
            )
        ]
        mock_service.get_pull_requests.return_value = [
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
        mock_service.get_issues.return_value = [
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
        mock_service.get_discussions.return_value = [
            Discussion(
                id="D_kwDOJ-L_c84AAQ",
                title="Test Discussion",
                body="Test Discussion body",
                author="test_author",
                created_at="2025-01-01",
                html_url="https://github.com/owner/repo/discussions/1",
            )
        ]

        # Call the full_report_cmd command
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(cli_app, ["summarize", "--config", "config.toml", "--save"])

        assert result.exit_code == 0
        mock_summarize_method.assert_called_once()

        # Assert that json.dump was called with the correct data
        expected_output_data = {
            "repo": "test_owner/test_repo",
            "commits": [
                Commit(
                    sha="123",
                    author="test_author",
                    message="Test commit",
                    date="2025-01-01",
                    html_url="https://github.com/owner/repo/commit/123",
                ).model_dump()
            ],
            "pull_requests": [
                PullRequest(
                    number=101,
                    title="Test PR",
                    body="Test PR body",
                    author="pr_author",
                    state="open",
                    created_at="2025-01-01",
                    merged_at=None,
                    html_url="https://github.com/owner/repo/pull/101",
                ).model_dump()
            ],
            "issues": [
                Issue(
                    number=1,
                    title="Test Issue",
                    body="Test Issue body",
                    author="test_author",
                    state="open",
                    created_at="2025-01-01",
                    html_url="https://github.com/owner/repo/issues/1",
                ).model_dump()
            ],
            "discussions": [
                Discussion(
                    id="D_kwDOJ-L_c84AAQ",
                    title="Test Discussion",
                    body="Test Discussion body",
                    author="test_author",
                    created_at="2025-01-01",
                    html_url="https://github.com/owner/repo/discussions/1",
                ).model_dump()
            ],
        }
        mock_json_dump.assert_called_once()
        # Check the first argument of json.dump (the data)
        assert mock_json_dump.call_args[0][0] == expected_output_data

        mock_set_last_run_time.assert_called_once_with("config.toml")
