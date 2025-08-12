# Project Structure

## Directory Structure

```
├── docs/                     # Documentation
├── examples/                 # Configuration examples
├── github_summary/           # Main source code
├── tests/                    # Test suite
├── config/                   # Configuration files
└── output/                   # Generated files (runtime)
```

## Key Components

### Source Code (`github_summary/`)

| Module                | Purpose                              |
| --------------------- | ------------------------------------ |
| `main.py`             | CLI entry point using Typer          |
| `actions.py`          | Core report generation logic         |
| `github_client.py`    | GitHub GraphQL API client            |
| `llm_client.py`       | LLM integration (OpenAI-compatible)  |
| `summarizer.py`       | AI-powered summary generation        |
| `scheduler.py`        | Cron-based task scheduling           |
| `rss.py`              | RSS feed creation and management     |
| `web.py`              | FastAPI web service                  |
| `config.py`           | Configuration loading and validation |
| `models.py`           | Pydantic data models                 |
| `queries.py`          | GitHub GraphQL query definitions     |
| `last_run_manager.py` | Execution time tracking              |

### Configuration

- `examples/` - Configuration templates for different use cases

### Documentation

- `README.md` - Quick start and overview
- `docs/SETUP.md` - Installation and setup guide
- `docs/CONFIGURATION.md` - Complete configuration reference
- `docs/API.md` - Technical API documentation
- `GEMINI.md` - AI assistant development context

## File Conventions

### Generated Files (Runtime)

- `output/rss.xml` - RSS feed file
- `output/*_summary.json` - Raw data reports
- `output/*_summary.md` - AI-generated summaries
- `log/github_summary.log` - Application logs
- `log/last_run_times.json` - Execution tracking

### Development Files

- `pyproject.toml` - Project dependencies and metadata
- `uv.lock` - Dependency lock file
- `tests/` - Test suite with pytest
- `.gitignore` - Git ignore patterns
- `Dockerfile` - Container configuration

This structure provides clear separation of concerns and makes the project easy to navigate and maintain.

