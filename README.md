# GitHub Repository Summarizer

A modern, async-first CLI tool and RSS server that fetches GitHub repository activity and generates AI-powered summaries using OpenAI and gidgethub.

## 🚀 Quick Start

1. **Install dependencies:**

   ```bash
   # Using uv (recommended)
   pip install uv && uv sync

   # Or using pip
   pip install -e .
   ```

2. **Configure:**

   ```bash
   cp examples/basic.toml config.toml
   # Edit config.toml with your GitHub token and LLM API key
   ```

3. **Run:**

   ```bash
   # Generate summaries
   ghsum run
   # Start RSS web server
   ghsum serve
   # Run scheduler daemon
   ghsum schedule
   ```

## 📋 Commands

### Generate Repository Summaries

```bash
# Process all repositories
ghsum run

# Process specific repository
ghsum run --repo owner/repo-name

# Save outputs
ghsum run --save-json --save-markdown

# Skip LLM summary generation (data collection only)
ghsum run --skip-summary
```

### RSS Web Server

```bash
# Start server on default port (8000)
ghsum serve

# Custom host and port
ghsum serve --host 0.0.0.0 --port 8080

# Development mode with auto-reload
ghsum serve --reload
```

### Scheduler Daemon

```bash
# Run scheduled jobs (blocking)
ghsum schedule
```

### Utilities

```bash
# Validate configuration
ghsum utils validate-config
```

## ⚙️ Configuration

### Basic Setup

```toml
# Optional. Defaults to:
#   $XDG_STATE_HOME/github-summary
# or:
#   ~/.local/state/github-summary
# run_dir = "~/.local/state/github-summary"
output_dir = "output"
cache_dir = "cache"
log_dir = "log"

[github]
token = "YOUR_GITHUB_TOKEN"

[[repositories]]
name = "owner/repo-name"

[llm]
api_key = "YOUR_LLM_API_KEY"
base_url = "https://api.openai.com/v1"  # Optional: custom OpenAI-compatible endpoint
model_name = "gpt-4o-mini"
language = "English"

[performance]
max_concurrent_repos = 4  # Maximum concurrent repository processing
max_concurrent_llm = 3    # Maximum concurrent LLM requests
```

By default, runtime files live under the XDG state directory: `$XDG_STATE_HOME/github-summary`, or `~/.local/state/github-summary` when `XDG_STATE_HOME` is not set. Relative `output_dir`, `cache_dir`, and `log_dir` values are resolved inside `run_dir`; absolute paths are used as-is. They can also be overridden from the CLI with `--output-dir`, `--cache-dir`, and `--log-dir`.

### RSS Configuration

```toml
[rss]
title = "My GitHub Activity"
link = "https://my-domain.com/rss.xml"
description = "Recent activity in my GitHub repositories"
filename = "rss.xml"
```

### Scheduling

```toml
[schedule]
cron = "0 9,17 * * *"       # Daily at 9 AM and 5 PM
timezone = "America/New_York"
```

**Common Cron Patterns:**

### Per-Repository Scheduling

```toml
[repositories.schedule]
cron = "0 12 * * 1"         # Every Monday at noon
timezone = "UTC"
```

### Release Tracking

Enable or disable release tracking for a repository:

```toml
[[repositories]]
name = "owner/repo-name"
include_releases = true

# Only fetch releases for this repository
[[repositories]]
name = "owner/another-repo"
release_only = true
```

### Filtering Releases

```toml
[filters.releases]
exclude_release_names_regex = "-alpha|-beta"
```

### Repository Grouping

Repositories with the same schedule are automatically grouped for efficient processing:

### Repository Grouping

Repositories with the same schedule are automatically grouped for efficient processing:

```toml
# These will be processed together in a single job
[[repositories]]
name = "owner/repo1"
[repositories.schedule]
cron = "0 9 * * *"

[[repositories]]
name = "owner/repo2"
[repositories.schedule]
cron = "0 9 * * *"
```

## 🌐 Web Interface

The RSS server provides:

- **RSS Feed**: Auto-generated from repository summaries
- **Static Files**: Access generated markdown and JSON reports
- **Health Check**: `/healthz` endpoint for monitoring
- **Background Jobs**: Automatic scheduled processing

```bash
# Start server
ghsum serve --port 8080

# Access feed
curl http://localhost:8080/rss.xml

# Health check
curl http://localhost:8080/healthz
```

## 🔧 Advanced Usage

### Environment Variables

```bash
# Override configuration
export GITHUB_TOKEN="your_token"
export OPENAI_API_KEY="your_key"
export GHSUM_CONCURRENT_REPOS="6"
export GHSUM_CONFIG_PATH="/path/to/config.toml"

# Run with overrides
ghsum run --max-concurrent 8
```

### Programming API

```python
from github_summary.app import GitHubSummaryApp

# Create application instance
app = GitHubSummaryApp("config/config.toml", skip_summary=False)

# Process all repositories
await app.run()

# Process specific repositories
await app.run(
    repo_names=["owner/repo1", "owner/repo2"],
    save_json=True,
    save_markdown=True,
    max_concurrent_repos=4
)
```

### Docker Deployment

Build the image:

```bash
docker build -t github-summary .
```

Run the RSS server:

```bash
docker run --rm \
  -p 8000:8000 \
  -v "$PWD/config/config.toml:/config/config.toml:ro" \
  -v github-summary-state:/data \
  github-summary
```

The container sets `XDG_STATE_HOME=/data`, so runtime files are stored under `/data/github-summary` by default. Mount `/data` or set `run_dir` in `config.toml` if you want a different persistent location.

Run the scheduler instead of the web server:

```bash
docker run --rm \
  -v "$PWD/config/config.toml:/config/config.toml:ro" \
  -v github-summary-state:/data \
  github-summary schedule
```

Run a one-off report:

```bash
docker run --rm \
  -v "$PWD/config/config.toml:/config/config.toml:ro" \
  -v github-summary-state:/data \
  github-summary run --skip-summary
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration

# Test new architecture
python test_new_architecture.py

# Validate configuration
ghsum utils validate-config
```

## 📊 Monitoring

### Logs

```bash
# Application logs
tail -f log/github_summary.log

# Structured logging with timestamps
[2025-01-13 10:00:00] INFO Processing repository: owner/repo
[2025-01-13 10:00:01] INFO Summary generated (1024 characters)
```

### Health Checks

```bash
# Web server health
curl http://localhost:8000/healthz

# Scheduler status (check logs)
ghsum schedule 2>&1 | grep "Scheduler"
```

### Performance Tuning

```toml
[performance]
max_concurrent_repos = 6     # Adjust based on GitHub API limits
max_concurrent_llm = 4       # Adjust based on LLM provider limits

fallback_lookback_days = 14  # Increase for more historical data
```

## ❓ Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**

   ```bash
   # Check your limits
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
   # Reduce concurrency
   ghsum run --max-concurrent 2
   ```

2. **LLM API Errors**

   ```bash
   # Test without LLM
   ghsum run --skip-summary
   # Check configuration
   ghsum utils validate-config
   ```

3. **Configuration Errors**

   ```bash
   # Validate syntax
   ghsum utils validate-config

   # Test with minimal config
   echo '[github]\ntoken="test"\n[[repositories]]\nname="owner/repo"' >test.toml
   ghsum run --config test.toml --skip-summary
   ```

### Debug Mode

```bash
# Enable debug logging
export GHSUM_LOG_LEVEL=DEBUG
ghsum run

# Or edit config.toml
log_level = "DEBUG"
```

## 🤝 Contributing

1. **Setup Development Environment**

   ```bash
   git clone https://github.com/your-username/github-summary.git
   cd github-summary || exit
   uv sync --dev
   ```

2. **Run Tests**

   ```bash
   pytest
   python test_new_architecture.py
   ```

3. **Code Style**
   ```bash
   ruff check .
   ruff format .
   ```

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [gidgethub](https://github.com/brettcannon/gidgethub) for async GitHub API client
- [FastAPI](https://fastapi.tiangolo.com/) for web framework
- [Typer](https://typer.tiangolo.com/) for CLI interface
- [APScheduler](https://apscheduler.readthedocs.io/) for scheduling
  github-summary web --reload --config custom.toml

# List repository labels

github-summary utils list-labels owner/repo

## ✨ Features

- **Async-first architecture**: Built with OpenAI and gidgethub for high performance
- **Multi-source data**: Commits, PRs, issues, discussions, and releases via GitHub GraphQL API
- **AI summaries**: OpenAI and compatible LLM integration with configurable concurrency
- **Flexible scheduling**: AsyncIOScheduler with cron-based scheduling and timezone support
- **RSS feeds**: Generate RSS feeds for summaries with markdown support
- **Advanced filtering**: Regex patterns, author filters, label filters, date ranges
- **Web service**: FastAPI-based service for RSS feeds and scheduled reports
- **Robust error handling**: Automatic retries with exponential backoff, rate limiting, and comprehensive logging
- **Per-repository tracking**: Individual last-run tracking and scheduling per repository
- **Modern async I/O**: Built on httpx for efficient HTTP operations

## 📁 Project Structure

```
├── config/ # Configuration files
├── github_summary/ # Main source code
├── tests/ # Test suite
├── docs/ # Detailed documentation
└── examples/ # Configuration examples
```

## 📚 Documentation

- **[API Documentation](docs/api_reference.md)** - GraphQL queries and data models
- **[Configuration Examples](examples/README.md)** - Example configurations for different use cases

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests:

   ```bash
   ruff check .          # Check for linting issues
   ruff check . --fix    # Auto-fix linting issues
   pyrefly check         # Type checking
   pytest                # Run tests
   pytest -m unit        # Run only unit tests (fast)
   pytest -m integration # Run integration tests
   ```

6. Submit a pull request

### Test Categories

- **Unit tests** (`@pytest.mark.unit`): Fast tests without external dependencies
- **Integration tests** (`@pytest.mark.integration`): Tests with mocked external services

For development guidelines and detailed testing information, see [Testing Guide](docs/testing_guide.md).

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
