# GitHub Repository Summarizer

GitHub Repository Summarizer is a powerful command-line tool designed to fetch and summarize activity from GitHub repositories. It can retrieve a wide range of data, including commits, issues, pull requests, and discussions, and then optionally leverage a Large Language Model (LLM) to generate concise and intelligent summaries of recent repository developments.

## 🚀 Key Features

- **Comprehensive Data Fetching:** Gathers detailed repository data, including commits, issues, pull requests, and discussions.
- **Advanced Filtering:** Allows for precise data selection using filters for time ranges, authors, titles, regular expressions, and more.
- **AI-Powered Summaries:** Integrates with LLMs to create intelligent and context-aware summaries of repository activity.
- **Efficient API Usage:** Primarily uses GitHub's GraphQL API for fast and efficient data retrieval.
- **Configurable System Prompt:** Customize the LLM's system prompt for tailored summaries.

## 🛠️ Development Principles

- **Prioritize GraphQL API:** We prefer using the [GitHub GraphQL API](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql) for its efficiency and ability to fetch precisely the data needed in a single request.
- **Code Style:** The project adheres to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) to ensure code is readable, consistent, and maintainable.
- **Code Quality:** We maintain high standards for code quality through comprehensive docstrings and complete type annotations.

## 📦 Project Management

This project uses **uv** for fast and reliable dependency and virtual environment management.

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
python -m github_summary summarize
```

**Options:**

- `--config -c <path>`: Specify a different path to the configuration file (default: `config/config.toml`).
- `--since-days <int>`: Override the number of days to look back for activity (e.g., `--since-days 14`).
- `--author <name>`: Filter activity by a specific author.
- `--save`: Save the generated report to a JSON file in the `output_dir` specified in `config.toml`.
- `--skip-summary`: Skip the LLM-based summary generation and only fetch data.

**Example:**

```bash
python -m github_summary summarize --since-days 7 --save
```

### List Repository Labels

To list all labels for a given repository:

```bash
python -m github_summary utils list-labels <owner/repo_name>
```

**Example:**

```bash
python -m github_summary utils list-labels meijieru/github_summary
```

## 🤝 Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## 📄 License

This project is licensed under the MIT License.
