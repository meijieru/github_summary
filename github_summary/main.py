import typer

from github_summary.actions import run_report
from github_summary.github_client import GitHubService
from github_summary.config import load_config

app = typer.Typer()
utils_app = typer.Typer()
app.add_typer(utils_app, name="utils")


@app.command()
def summarize(
    config_path: str = typer.Option("config/config.toml", "--config", "-c", help="Path to the configuration file."),
    since_days: int | None = typer.Option(
        None, "--since-days", help="Number of days to look back for data. If not set, uses default from config."
    ),
    author: str | None = typer.Option(None, "--author", help="Filter by author."),
    save: bool = typer.Option(False, "--save", help="Save the report to a JSON file."),
    skip_summary: bool = typer.Option(False, "--skip-summary", help="Skip printing the summary."),
):
    """Summarize the recent progress in GitHub repositories."""
    run_report(config_path, since_days, author, save, skip_summary)


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


def main():
    app()


if __name__ == "__main__":
    main()
