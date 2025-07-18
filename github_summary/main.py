import logging
import time

import schedule
import typer

from github_summary.actions import run_report
from github_summary.config import load_config
from github_summary.github_client import GitHubService

logger = logging.getLogger(__name__)

app = typer.Typer()
utils_app = typer.Typer()
app.add_typer(utils_app, name="utils")


@app.command()
def summarize(
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
    save: bool = typer.Option(False, "--save", help="Save the report to a JSON file."),
    save_markdown: bool = typer.Option(False, "--save-markdown", help="Save the summary to a Markdown file."),
    skip_summary: bool = typer.Option(False, "--skip-summary", help="Skip printing the summary."),
):
    """Summarize the recent progress in GitHub repositories."""
    run_report(config_path, save, save_markdown, skip_summary)


@app.command()
def schedule_run(
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
):
    """Run the summarization on a schedule."""
    config = load_config(config_path)
    if config.schedule and config.schedule.enabled:
        for run_time in config.schedule.run_at:
            schedule.every().day.at(run_time).do(run_report, config_path, False, False, False)
        while True:
            schedule.run_pending()
            time.sleep(60)


@utils_app.command("list-labels")
def list_labels(
    repo_name: str = typer.Argument(..., help="Repository name in 'owner/repo' format."),
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
):
    """List all labels for a given repository."""
    config = load_config(config_path)
    github_service = GitHubService(config.github.token)
    owner, repo = repo_name.split("/")
    labels = github_service.get_all_labels(owner, repo)
    for label in labels:
        print(label)


if __name__ == "__main__":
    app()
