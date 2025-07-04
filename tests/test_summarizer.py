from unittest.mock import Mock, patch
from github_summary.models import Commit, Discussion, Issue, PullRequest
from github_summary.summarizer import Summarizer
from github_summary.main import app as cli_app


def test_summarizer():
    mock_llm_client = Mock()
    mock_llm_client.generate_summary.return_value = "Mocked LLM Summary"
    summarizer = Summarizer(llm_client=mock_llm_client)
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
            author="test_author",
            created_at="2025-01-01",
            html_url="https://github.com/owner/repo/discussions/1",
        )
    ]

    summary = summarizer.summarize(commits, pull_requests, issues, discussions)

    mock_llm_client.generate_summary.assert_called_once()
    assert summary == "Mocked LLM Summary"


def test_summarizer_output_json():
    mock_llm_client = Mock()
    mock_summarizer = Mock()
    mock_summarizer.summarize.return_value = "Mocked LLM Summary"

    # Mock GitHubService methods to return dummy data
    mock_config = Mock()
    mock_config.repositories = [Mock()]
    mock_config.repositories[0].name = "test_owner/test_repo"
    mock_service = Mock()

    with (
        patch("github_summary.actions._get_services", return_value=(mock_config, mock_service, mock_summarizer)),
        patch("github_summary.actions.console.print") as mock_console_print,
        patch("json.dump") as mock_json_dump,
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
        mock_summarizer.summarize.assert_called_once()  # full_report_cmd calls summarizer

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
                    author="test_author",
                    created_at="2025-01-01",
                    html_url="https://github.com/owner/repo/discussions/1",
                ).model_dump()
            ],
        }
        mock_json_dump.assert_called_once()
        # Check the first argument of json.dump (the data)
        assert mock_json_dump.call_args[0][0] == expected_output_data

        # Assert that console.print was called with the summary
        mock_console_print.assert_any_call("Mocked LLM Summary")
