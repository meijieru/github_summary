# Setup Guide

## Installation

### Prerequisites

- Python 3.11+
- Git
- GitHub Personal Access Token
- LLM API Key (OpenAI, OpenRouter, etc.)

### Step 1: Clone Repository

```bash
git clone https://github.com/meijieru/github_summary.git
cd github_summary || exit
```

### Step 2: Install Dependencies

```bash
# Using uv (recommended)
pip install uv
uv sync

# Or using pip
pip install -e .
```

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
