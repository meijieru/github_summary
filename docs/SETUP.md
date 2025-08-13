# Setup Guide

## Installation

### Prerequisites

### System Requirements

The async-first architecture has minimal system requirements:

- **Memory**: ~50MB base + ~10MB per concurrent repository
- **CPU**: Async I/O is CPU-efficient, works well on modest hardware
- **Network**: Good network connectivity for GitHub and LLM APIs
- **Python**: 3.11+ required for modern async features

### Step 1: Clone Repository

```bash
git clone https://github.com/meijieru/github_summary.git
cd github_summary || exit
```

### Step 2: Install Dependencies

```bash
# Using uv (recommended for fast dependency management)
uv sync

# Or using pip
pip install -e .
```

### Dependencies Overview

Key dependencies for the async architecture:

- **`gidgethub`**: Production-ready GitHub API client with automatic rate limiting
- **`openai`**: Official AsyncOpenAI client for LLM integration
- **`apscheduler`**: AsyncIOScheduler for cron-based scheduling
- **`asyncio`**: Native Python async runtime (Python 3.11+)
- **`pydantic`**: Type-safe configuration and data validation
- **`fastapi`**: Async web framework for the web service

### Step 3: Configuration

```bash
cp examples/basic.toml config/config.toml
```

Edit `config/config.toml`:

```toml
[github]
token = "ghp_your_github_token_here"

[[repositories]]
name = "owner/repository-name"

[llm]
base_url = "https://api.openai.com/v1"  # or OpenRouter, etc.
api_key = "your_api_key_here"
model_name = "gpt-4"
max_concurrent = 3  # Configurable concurrent LLM requests
language = "English"
```

## GitHub Token Setup

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select these scopes:
   - `repo` (Full control of private repositories)
   - `public_repo` (Access public repositories)
4. Copy the token to your config file

## LLM API Setup

### OpenAI

```toml
[llm]
base_url = "https://api.openai.com/v1"
api_key = "sk-your-openai-key"
model_name = "gpt-4"
```

### OpenRouter

```toml
[llm]
base_url = "https://openrouter.ai/api/v1"
api_key = "sk-or-v1-your-key"
model_name = "anthropic/claude-3-sonnet"
```

### Local LLM (Ollama)

```toml
[llm]
base_url = "http://localhost:11434/v1"
api_key = "fake-key"  # Can be anything for local
model_name = "llama2"
```

## Verification

Test your setup:

```bash
github-summary summarize --skip-summary
```

This should fetch repository data without generating summaries.
