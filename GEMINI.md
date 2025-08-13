# GitHub Repository Summarizer

## Development Guidelines

### Code Quality Standards

Before submitting any code changes:

```bash
# Linting and formatting
ruff check .          # Check for issues
ruff check . --fix    # Auto-fix where possible

# Type checking
pyrefly check         # Advanced type analysis

# Testing
pytest -m unit        # Fast unit tests
pytest -m integration # Integration tests with mocks
pytest                # Full test suite
```

### Async Programming Guidelines

- **Always use async/await**: All I/O operations should be async
- **Proper context management**: Use `async with` for resources
- **Concurrency control**: Use semaphores to limit concurrent operations
- **Error handling**: Implement proper exception handling for async operations
- **Testing async code**: Use `pytest-asyncio` and proper async test patterns

### Common Patterns

```python
# Async context manager pattern
async with GitHubService(token) as gh_service:
    data = await gh_service.fetch_repository_data(owner, repo)

# Concurrent processing with semaphore
semaphore = asyncio.Semaphore(max_concurrent)
async with semaphore:
    result = await process_repository(repo)

# Proper error handling with retries
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def api_call():
    # Implementation with automatic retry
```

### File Naming Conventions

- **Source files**: Use descriptive names reflecting purpose (`github_client.py`, `llm_client.py`)
- **Test files**: Prefix with `test_` and match source file names (`test_github_client.py`)
- **Configuration**: Use `.toml` format with clear section naming
- **Output files**: Include repository name and timestamp for clarity

This document is regularly updated to reflect the evolving codebase and development practices.
> **Note:** This file serves as a context reference for AI development assistants. We use AI assistants internally for development assistance, and this file helps better understand our project context, coding style, and development principles.

## Project Overview

A modern, async-first CLI tool that fetches GitHub repository activity and generates AI-powered summaries using GraphQL API and LLM integration. The tool emphasizes high performance through asyncio concurrency, robust error handling, and modular design.
### Key Features

- **Async-first architecture**: Built on asyncio with concurrent repository processing
- **GitHub GraphQL API**: Efficient data fetching with gidgethub client
- **LLM integration**: OpenAI and compatible APIs with configurable concurrency
- **Flexible scheduling**: APScheduler for cron-based automation with per-repository support
- **Web service**: FastAPI-based REST API and RSS feed server
- **Advanced filtering**: Regex patterns, author filters, label filters, date ranges
- **State management**: Per-repository last-run tracking with async file operations
- **Modern HTTP**: httpx-based async HTTP client replacing requests

This section provides essential context for AI development assistants:

**Core Principles:**

- **Async-First:** All I/O operations use asyncio for non-blocking performance
- **GraphQL-First:** Prioritize GitHub GraphQL API for efficiency over REST
- **Concurrent by Design:** Configurable concurrency for both repositories and LLM requests
- **Time Zone Management:** UTC for internal processing, local time for display
- **Type Safety:** Comprehensive Pydantic models and type annotations
- **Error Resilience:** Automatic retries with exponential backoff and graceful degradation
- **Code Style:** Strict adherence to Python best practices
  - ruff for linting and formatting
  - pyrefly for advanced type checking
  - pytest with async support for testing
- **Documentation:** Complete docstrings and type annotations for all code

**Development Requirements:**

- **Python 3.11+**: Required for modern async features and performance
- **Dependency Management**: Use uv for fast dependency resolution and virtual environments
- Update relevant documentation when making changes
- Maintain consistency with existing codebase patterns
- Use UTC for all internal timestamp processing
- Prefer GraphQL API over REST when possible
- **Code Quality:** All code must pass `ruff check .` and `pyrefly check` before submission
- **Testing**: Use pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
## Technology Stack

### Core Dependencies

- **asyncio**: Native Python async runtime (Python 3.11+)
- **gidgethub**: Production-ready GitHub API client with rate limiting
- **openai**: Official OpenAI client with async support
- **httpx**: Modern async HTTP client (replaces requests)
- **pydantic**: Type-safe configuration and data validation
- **typer**: CLI framework with rich output support
- **apscheduler**: AsyncIOScheduler for cron-based scheduling

### Web & API

- **fastapi**: Async web framework for REST API
- **uvicorn**: ASGI server with auto-reload support
- **feedgen**: RSS feed generation
- **markdown-it-py**: Markdown processing

### Development Tools

- **pytest**: Testing framework with async support
- **ruff**: Fast Python linter and formatter
- **pyrefly**: Advanced type checker
- **uv**: Fast dependency management

### Recent Improvements

- **Migration to httpx**: Replaced requests with async httpx for better performance
- **Per-repository tracking**: Individual last-run times and scheduling
- **Enhanced error handling**: Tenacity for retry logic with exponential backoff
- **Improved scheduling**: APScheduler with timezone support and per-repo schedules
- **Better modularity**: Cleaner separation of concerns in codebase
- **Comprehensive testing**: Full pytest suite with unit and integration tests

## Related Documentation

For comprehensive project information, refer to:

- **[README.md](./README.md)** - Main project documentation and quick start guide
- **[docs/SETUP.md](docs/SETUP.md)** - Detailed installation and setup instructions
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Complete configuration reference and examples
- **[docs/API.md](docs/API.md)** - API documentation and GraphQL schema details
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Architecture overview and codebase structure
- **[docs/testing_guide.md](docs/testing_guide.md)** - Testing guidelines and pytest best practices
- **[examples/README.md](examples/README.md)** - Configuration examples for different use cases
