import functools
import logging
import os

import typer
import uvicorn
from asyncer import syncify

from github_summary.actions import run_report
from github_summary.config import load_config
from github_summary.github_client import GitHubService
from github_summary.scheduler import ReportScheduler
from github_summary.web import build_web_app

logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=True)
utils_app = typer.Typer()
app.add_typer(utils_app, name="utils")


@app.command()
@functools.partial(syncify, raise_sync_error=False)
async def summarize(
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
    save: bool = typer.Option(False, "--save", help="Save the report to a JSON file."),
    save_markdown: bool = typer.Option(False, "--save-markdown", help="Save the summary to a Markdown file."),
    skip_summary: bool = typer.Option(False, "--skip-summary", help="Skip printing the summary."),
    repo: str = typer.Option(None, "--repo", help="Run only for a specific repository (format: owner/repo)."),
) -> None:
    """Summarize the recent progress in GitHub repositories."""
    await run_report(config_path, save, save_markdown, skip_summary, repo)


@app.command("schedule-run")
@functools.partial(syncify, raise_sync_error=False)
async def schedule_run(
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
) -> None:
    """Run the summarization on a schedule (blocking)."""
    scheduler = ReportScheduler(config_path)
    await scheduler.run_forever()


@app.command("web")
def web(
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
    host: str = typer.Option("0.0.0.0", "--host", help="Host interface."),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind."),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev only)."),
) -> None:
    """Run the web server."""
    if reload:
        # uvicorn reload requires import path + factory
        os.environ["GHSUM_CONFIG_PATH"] = config_path
        uvicorn.run("github_summary.web:create_app", host=host, port=port, reload=True, factory=True)
    else:
        uvicorn.run(build_web_app(config_path), host=host, port=port, reload=False)


@utils_app.command("list-labels")
@functools.partial(syncify, raise_sync_error=False)
async def list_labels(
    repo_name: str = typer.Argument(..., help="Repository name in 'owner/repo' format."),
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
) -> None:
    """List all labels for a given repository."""
    config = load_config(config_path)
    token = config.github.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        logging.error("GitHub token is required. Set it in the config file or as an environment variable.")
        raise typer.Exit(1)

    owner, repo = repo_name.split("/")

    async with GitHubService(token) as gh_service:
        labels = await gh_service.get_all_labels(owner, repo)
        print("\n".join(labels))


def main() -> None:
    """CLI entry point to run the Typer application."""
    app()
