# GitHub Repository Summarizer

> **Note:** This file serves as a context reference for AI development assistants. We use AI assistants internally for development assistance, and this file helps better understand our project context, coding style, and development principles.

## Project Overview

A CLI tool that fetches GitHub repository activity and generates AI-powered summaries using GraphQL API and LLM integration. Features include RSS feed generation, web interface, scheduling, and advanced filtering capabilities.

This section provides essential context for AI development assistants:

**Core Principles:**

- **GraphQL-First:** Prioritize GitHub GraphQL API for efficiency
- **Time Zone Management:** UTC for internal processing, local time for display
- **Code Style:** Strict adherence to Google Python Style Guide
- **Documentation:** Complete docstrings and type annotations for all code

**Development Requirements:**

- Update relevant documentation when making changes
- Maintain consistency with existing codebase patterns
- Use UTC for all internal timestamp processing
- Prefer GraphQL API over REST when possible
- **Code Quality:** All code must pass `ruff check` and `pyrefly check` before submission

## Related Documentation

For comprehensive project information, refer to:

- **[README.md](./README.md)** - Main project documentation and quick start
- **[docs/SETUP.md](docs/SETUP.md)** - Installation and setup instructions
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - Configuration options and examples
- **[docs/API.md](docs/API.md)** - API documentation and integration details
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Codebase structure overview
- **[docs/testing_guide.md](docs/testing_guide.md)** - Testing guidelines and pytest usage
