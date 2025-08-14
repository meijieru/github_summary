# API Reference

## Core Application

### GitHubSummaryApp

The main application class that handles all GitHub repository processing.

#### Constructor

```python
from github_summary.app import GitHubSummaryApp

app = GitHubSummaryApp(
    config_path: str,
    skip_summary: bool = False
)
```

**Parameters:**

- `config_path`: Path to the TOML configuration file
- `skip_summary`: If True, skips LLM summary generation (data collection only)

#### Methods

##### `run()`

Process repositories and generate summaries.

```python
await app.run(
    repo_names: list[str] | None = None,
    save_json: bool = False,
    save_markdown: bool = False,
    max_concurrent_repos: int | None = None,
) -> None
```

**Parameters:**

- `repo_names`: List of repository names to process. If None, processes all configured repositories
- `save_json`: Whether to save detailed JSON reports
- `save_markdown`: Whether to save markdown summaries
- `max_concurrent_repos`: Maximum concurrent repository operations (overrides config)

**Example:**

```python
# Process all repositories
await app.run()

# Process specific repositories with outputs
await app.run(
    repo_names=["owner/repo1", "owner/repo2"],
    save_json=True,
    save_markdown=True,
    max_concurrent_repos=4
)
```

#### Context Manager Usage

The app can be used as an async context manager for proper resource cleanup:

```python
async with GitHubSummaryApp(config_path) as app:
    await app.run()
# Resources are automatically cleaned up
```

#### Properties

##### `config`

Access the loaded configuration:

```python
config = app.config
print(f"Processing {len(config.repositories)} repositories")
```

## Web Application

### create_web_app()

Create a FastAPI application for the RSS server.

```python
from github_summary.app import create_web_app

web_app = create_web_app(config_path: str = "config/config.toml") -> FastAPI
```

**Parameters:**

- `config_path`: Path to the configuration file

**Returns:**

- Configured FastAPI application instance

**Example:**

```python
import uvicorn
from github_summary.app import create_web_app

app = create_web_app("my_config.toml")
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Endpoints

The web application provides these endpoints:

#### `GET /`

Root endpoint with service information.

**Response:**

```json
{
	"service": "GitHub Summary RSS Server",
	"endpoints": {
		"health": "/healthz",
		"rss": "/rss.xml",
		"static": "/*"
	}
}
```

#### `GET /healthz`

Health check endpoint.

**Response:**

```json
{
	"status": "ok",
	"service": "github-summary-rss"
}
```

#### `GET /rss.xml`

RSS feed (served as static file).

#### `GET /*`

Static files from the output directory (generated summaries).

## Scheduler

### ReportScheduler

Handles scheduled execution of repository processing.

```python
from github_summary.scheduler import ReportScheduler

scheduler = ReportScheduler(config_path: str)
```

#### Methods

##### `start()`

Start the scheduler.

```python
await scheduler.start()
```

##### `stop()`

Stop the scheduler.

```python
await scheduler.stop()
```

##### `run_forever()`

Run scheduler indefinitely (for CLI usage).

```python
await scheduler.run_forever()
```

**Example:**

```python
scheduler = ReportScheduler("config/config.toml")
try:
    await scheduler.run_forever()
except KeyboardInterrupt:
    print("Scheduler stopped by user")
```

## CLI Functions

All CLI commands are available programmatically:

### run()

```python
from github_summary.cli import run
from asyncio import run as arun

arun(run(
    repo="owner/repo",
    config="config/config.toml",
    save_json=True,
    save_markdown=False,
    skip_summary=False,
    max_concurrent=None
))
```

### serve()

```python
from github_summary.cli import serve

serve(
    config="config/config.toml",
    host="0.0.0.0",
    port=8000,
    reload=False
)
```

### schedule()

```python
from github_summary.cli import schedule
from asyncio import run as arun

arun(schedule(config="config/config.toml"))
```

## Configuration Model

### Config

Main configuration class based on Pydantic.

```python
from github_summary.models import Config
from github_summary.config import load_config

config = load_config("config/config.toml")
```

#### Properties

- `github: GitHubConfig` - GitHub API configuration
- `repositories: list[RepoConfig]` - Repository configurations
- `llm: LLMConfig | None` - LLM service configuration
- `rss: RssConfig | None` - RSS feed configuration
- `schedule: ScheduleConfig | None` - Global schedule configuration
- `performance: PerformanceConfig` - Performance settings
- `output_dir: str` - Output directory for generated files
- `log_level: str` - Logging level
- `since_last_run: bool` - Use last run time for incremental updates
- `fallback_lookback_days: int` - Days to look back when no last run time
- `timezone: str` - Default timezone

### RepoConfig

Repository-specific configuration.

#### Properties

- `name: str` - Repository name (owner/repo)
- `filters: FilterConfig` - Repository-specific filters
- `include_commits: bool` - Include commits in processing
- `include_pull_requests: bool` - Include pull requests
- `include_issues: bool` - Include issues
- `include_discussions: bool` - Include discussions
- `schedule: ScheduleConfig | None` - Repository-specific schedule

### LLMConfig

LLM service configuration.

#### Properties

- `base_url: str | None` - API base URL
- `api_key: str | None` - API key
- `model_name: str` - Model name
- `language: str | None` - Summary language
- `retries: int` - Number of retries
- `retry_delay: int` - Delay between retries
- `system_prompt: str` - System prompt for the LLM

### Performance Configuration

#### Environment Variables

These environment variables can override configuration:

- `GITHUB_TOKEN` - GitHub API token
- `OPENAI_API_KEY` - OpenAI API key
- `GHSUM_CONCURRENT_REPOS` - Max concurrent repositories
- `GHSUM_CONFIG_PATH` - Configuration file path

#### Concurrency Control

```python
# Application automatically uses semaphores to limit concurrency
semaphore = asyncio.Semaphore(max_concurrent_repos)

async def process_with_semaphore(repo):
    async with semaphore:
        return await process_repository(repo)
```

## Error Handling

### Exception Types

The application handles these common exceptions:

- `FileNotFoundError` - Configuration file not found
- `ValueError` - Invalid configuration values
- `typer.Exit` - CLI exit conditions
- `aiohttp.ClientError` - HTTP client errors
- `Exception` - General exceptions (logged and handled gracefully)

### Error Recovery

```python
try:
    app = GitHubSummaryApp(config_path)
    await app.run()
except typer.Exit as e:
    print(f"Application error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Application continues processing other repositories
```

## Best Practices

### Resource Management

Always use async context managers:

```python
# ✅ Good
async with GitHubSummaryApp(config_path) as app:
    await app.run()

# ❌ Bad - may leak resources
app = GitHubSummaryApp(config_path)
await app.run()
```

### Configuration Validation

Validate configuration before deployment:

```python
from github_summary.config import load_config

try:
    config = load_config("config/config.toml")
    print("✅ Configuration valid")
except (FileNotFoundError, ValueError) as e:
    print(f"❌ Configuration error: {e}")
```

### Concurrent Processing

Use appropriate concurrency limits:

```python
# For GitHub API (respect rate limits)
max_concurrent_repos = 4

# For LLM APIs (based on provider limits)
max_concurrent_llm = 3

# Override at runtime
await app.run(max_concurrent_repos=6)
```

### Logging

Configure appropriate log levels:

```python
# Development
log_level = "DEBUG"

# Production
log_level = "INFO"

# Monitor only errors
log_level = "ERROR"
```

