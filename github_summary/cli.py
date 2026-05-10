"""
GitHub Summary CLI - Modern command line interface.
"""

import functools
import os

import typer
import uvicorn
from asyncer import syncify

from github_summary.app import GitHubSummaryApp, create_web_app
from github_summary.config import load_config

# Create the main CLI application
app = typer.Typer(name="ghsum", help="🚀 GitHub Repository Summary Tool", rich_markup_mode="rich", no_args_is_help=True)

# Create utils subcommand group
utils_app = typer.Typer(name="utils", help="🛠️ Utility commands")
app.add_typer(utils_app, name="utils")


@app.command("run")
@functools.partial(syncify, raise_sync_error=False)
async def run(
    repo: str | None = typer.Option(None, "--repo", "-r", help="Process specific repository (format: owner/repo)"),
    config: str = typer.Option("config/config.toml", "--config", "-c", help="Path to configuration file"),
    output_dir: str | None = typer.Option(None, "--output-dir", help="Override output directory"),
    cache_dir: str | None = typer.Option(None, "--cache-dir", help="Override cache directory"),
    log_dir: str | None = typer.Option(None, "--log-dir", help="Override log directory"),
    save_json: bool = typer.Option(False, "--save-json", help="Save detailed JSON reports"),
    save_markdown: bool = typer.Option(False, "--save-markdown", help="Save markdown summaries"),
    skip_summary: bool = typer.Option(False, "--skip-summary", help="Skip LLM summary generation"),
    max_concurrent: int = typer.Option(None, "--max-concurrent", help="Override max concurrent repositories"),
) -> None:
    """📊 Generate repository summaries."""

    app_instance = GitHubSummaryApp(
        config,
        skip_summary=skip_summary,
        output_dir=output_dir,
        cache_dir=cache_dir,
        log_dir=log_dir,
    )

    repo_names = [repo] if repo else None

    await app_instance.run(
        repo_names=repo_names,
        save_json=save_json,
        save_markdown=save_markdown,
        max_concurrent_repos=max_concurrent,
    )


@app.command("serve")
def serve(
    config: str = typer.Option("config/config.toml", "--config", "-c", help="Path to configuration file"),
    output_dir: str | None = typer.Option(None, "--output-dir", help="Override output directory"),
    cache_dir: str | None = typer.Option(None, "--cache-dir", help="Override cache directory"),
    log_dir: str | None = typer.Option(None, "--log-dir", help="Override log directory"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host interface"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (development only)"),
) -> None:
    """🌐 Start RSS web server."""

    if reload:
        # For development with auto-reload
        os.environ["GHSUM_CONFIG_PATH"] = config
        if output_dir is not None:
            os.environ["GHSUM_OUTPUT_DIR"] = output_dir
        if cache_dir is not None:
            os.environ["GHSUM_CACHE_DIR"] = cache_dir
        if log_dir is not None:
            os.environ["GHSUM_LOG_DIR"] = log_dir
        uvicorn.run("github_summary.app:create_web_app", host=host, port=port, reload=True, factory=True)
    else:
        # Production mode
        web_app = create_web_app(config, output_dir=output_dir, cache_dir=cache_dir, log_dir=log_dir)
        uvicorn.run(web_app, host=host, port=port, reload=False)


@app.command("schedule")
@functools.partial(syncify, raise_sync_error=False)
async def schedule(
    config: str = typer.Option("config/config.toml", "--config", "-c", help="Path to configuration file"),
    output_dir: str | None = typer.Option(None, "--output-dir", help="Override output directory"),
    cache_dir: str | None = typer.Option(None, "--cache-dir", help="Override cache directory"),
    log_dir: str | None = typer.Option(None, "--log-dir", help="Override log directory"),
) -> None:
    """⏰ Run scheduler daemon (blocking)."""

    from github_summary.scheduler import ReportScheduler

    scheduler = ReportScheduler(config, output_dir=output_dir, cache_dir=cache_dir, log_dir=log_dir)
    await scheduler.run_forever()


@utils_app.command("validate-config")
def validate_config(
    config: str = typer.Option("config/config.toml", "--config", "-c", help="Path to configuration file"),
) -> None:
    """✅ Validate configuration file."""

    try:
        config_obj = load_config(config)
        typer.echo(f"✅ Configuration file '{config}' is valid!")
        typer.echo(f"📊 Found {len(config_obj.repositories)} repositories configured")

        # Check for common issues
        if not config_obj.github.token and not os.environ.get("GITHUB_TOKEN"):
            typer.echo("⚠️  Warning: No GitHub token found in config or GITHUB_TOKEN environment variable")

        if config_obj.llm is None:
            typer.echo("ℹ️  Info: No LLM configuration found (summaries will be skipped)")

        # Show schedule information
        scheduled_repos = [repo for repo in config_obj.repositories if repo.schedule]
        if config_obj.schedule:
            typer.echo(f"⏰ Global schedule: {config_obj.schedule.cron}")
        if scheduled_repos:
            typer.echo(f"⏰ {len(scheduled_repos)} repositories have individual schedules")

    except (FileNotFoundError, ValueError) as e:
        typer.echo(f"❌ Configuration error: {e}", err=True)
        raise typer.Exit(1)


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
