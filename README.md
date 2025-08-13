# GitHub Repository Summarizer

A modern, async-first CLI tool that fetches GitHub repository activity and generates AI-powered summaries using OpenAI and gidgethub.

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
   github-summary summarize
   ```

## ⚙️ Configuration

### Basic Setup

```toml
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

### Scheduling

```toml
[schedule]
cron = "0 9,17 * * *"       # Daily at 9 AM and 5 PM
timezone = "America/New_York"
```

**Common Cron Patterns:**

- `"0 6 * * *"` - Daily at 6 AM
- `"0 9 * * 1"` - Every Monday at 9 AM
- `"0 9-17 * * 1-5"` - Hourly during business hours
- `"0 17 * * 5"` - Every Friday at 5 PM

## 📋 Commands

```bash
# Generate summary
github-summary summarize

# Save to files
github-summary summarize --save --save-markdown

# Run specific repository
github-summary summarize --repo owner/repo

# Start scheduler
github-summary schedule-run

# Web service (serves RSS + scheduling)
github-summary web --port 8000

# Web service with custom config
github-summary web --config /path/to/config.toml --port 8000

# Web service with auto-reload (development)
github-summary web --reload --config custom.toml

# List repository labels
github-summary utils list-labels owner/repo
```

## ✨ Features

- **Async-first architecture**: Built with OpenAI and gidgethub for high performance
- **Multi-source data**: Commits, PRs, issues, discussions via GitHub GraphQL API
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
├── config/                 # Configuration files
├── github_summary/         # Main source code
├── tests/                  # Test suite
├── docs/                   # Detailed documentation
└── examples/               # Configuration examples
```

## 📚 Documentation

- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Configuration Reference](docs/CONFIGURATION.md)** - All configuration options
- **[API Documentation](docs/API.md)** - GraphQL queries and data models
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
