# GitHub Repository Summarizer

GitHub Repository Summarizer is a powerful command-line tool designed to fetch and summarize activity from GitHub repositories. It can retrieve a wide range of data, including commits, issues, pull requests, and discussions, and then optionally leverage a Large Language Model (LLM) to generate concise and intelligent summaries of recent repository developments.

## 🚀 Key Features

- **Comprehensive Data Fetching:** Gathers detailed repository data, including commits, issues, pull requests, and discussions.
- **Advanced Filtering:** Allows for precise data selection using filters for time ranges, authors, titles, regular expressions, and more.
- **AI-Powered Summaries:** Integrates with LLMs to create intelligent and context-aware summaries of repository activity.
- **Efficient API Usage:** Primarily uses GitHub's GraphQL API for fast and efficient data retrieval.
- **Configurable System Prompt:** Customize the LLM's system prompt for tailored summaries.
- **RSS Feed:** Can generate an RSS feed.
- **Scheduled Runs:** Supports scheduling the summarization process to run automatically.

## ⚙️ Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/meijieru/github_summary.git
    cd github_summary || exit
    ```

2.  **Install `uv` (if you don't have it):**

    ```bash
    pip install uv
    ```

3.  **Install dependencies:**
    ```bash
    uv sync
    ```

## 📝 Configuration

The Gemini CLI uses a `config.toml` file for its settings. An example configuration is provided in `config/config.toml.example`.

1.  **Create your configuration file:**

    ```bash
    cp config/config.toml.example config/config.toml
    ```

2.  **Edit `config/config.toml`:**
    Open the `config/config.toml` file and replace the placeholder values with your actual GitHub token and LLM API key.

    ```toml
    [github]
    token = "YOUR_GITHUB_TOKEN"

    # Global filters that apply to all repositories unless overridden.
    [filters.commits]
    exclude_commit_messages_regex = "^(docs|test|build|chore|ci)"
    [filters.pull_requests]
    exclude_pull_request_titles_regex = "^(docs|test|build|chore|ci)"

    [[repositories]]
    name = "meijieru/github_summary"
    include_commits = true
    include_pull_requests = true
    include_issues = true
    include_discussions = true
    # filters.commits.exclude_commit_messages_regex = "^(fix|docs|test|build|chore|ci)"

    [llm]
    api_key = "YOUR_LLM_API_KEY"
    base_url = "YOUR_LLM_BASE_URL" # Optional, e.g., for local LLMs
    model_name = "gpt-4.1" # Or your preferred model
    system_prompt = "Please summarize the following GitHub repository activity:"
    language = "Simplified Chinese"
    ```

    - `YOUR_GITHUB_TOKEN`: A GitHub Personal Access Token with `repo` scope.
    - `YOUR_LLM_API_KEY`: Your API key for the chosen LLM service (e.g., OpenAI).
    - `YOUR_LLM_BASE_URL`: (Optional) The base URL for your LLM API, useful for self-hosted or local LLMs.
    - `model_name`: The specific model identifier for your LLM.
    - `system_prompt`: The initial instruction given to the LLM before providing the activity data.

    For more advanced filtering and customization options, see the data models in `github_summary/models.py`.

## 🚀 Usage

### Summarize Repository Activity

To generate a summary of repository activity based on your `config.toml`:

```bash
github-summary summarize -c config/config.toml
```

**Options:**

- `--config -c <path>`: Path to the configuration file (default: `config/config.toml`).
- `--save`: Save the generated report to a JSON file in the `output_dir` specified in `config.toml`.
- `--save-markdown`: Save the LLM-generated summary as a Markdown file.
- `--skip-summary`: Skip the LLM-based summary generation and only fetch data.

**Example:**

```bash
github-summary summarize -c config/config.toml --save
```

### List Repository Labels

To list all labels for a given repository:

```bash
github-summary utils list-labels <owner/repo_name> -c config/config.toml
```

### RSS Feed Generation

The CLI can generate an RSS feed of the summaries. This feature can be enabled and configured in the `config.toml` file under the `[rss]` section.

Example `config.toml` snippet for RSS:

```toml
[rss]
enabled = true
title = "GitHub Repository Summaries"
link = "http://localhost/rss.xml"
description = "Summaries of recent activity in GitHub repositories."
filename = "rss.xml"
```

### Scheduled Runs

The CLI supports scheduling the summarization process to run automatically at specified times. This is configured in the `config.toml` file under the `[schedule]` section.

Example `config.toml` snippet for scheduling:

```toml
[schedule]
enabled = true
run_at = ["06:00", "18:00"] # in HH:MM format (UTC)
```

### Web service mode (serving RSS and scheduling)

This project can run as a single-process web service that both serves the RSS output directory and schedules periodic report generation.

- Command: `github-summary web -c config/config.toml --host 0.0.0.0 --port 8000` (or `uv run github-summary web ...` if using uv)
- Server: Uvicorn (FastAPI app)
- Static files: Served from `output_dir` configured in `config.toml`
- Health check: `GET /healthz`
- Note: The service does not execute a report at startup; it only runs at the scheduled times. If you need an immediate report, run `github-summary summarize` once or enable a near-term schedule.

Example Docker run:

```bash
docker run --rm -p 8000:8000 \
docker run --rm -p 8000:8000 \
    -e GITHUB_TOKEN=xxxx \
    -e GHSUM_CONFIG_PATH=/app/config/config.toml \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/output:/app/output \
    yourimage:tag
```

Then access `http://localhost:8000/` for static files (e.g., the RSS file), and `http://localhost:8000/healthz` for health.

Developer tips:
- Hot reload locally: `github-summary web --reload`
- Import-style run still works: `uvicorn github_summary.web:web_app`

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## 📄 License

This project is licensed under the MIT License.
