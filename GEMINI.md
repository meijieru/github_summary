# GitHub Repository Summarizer

This is a command-line tool that fetches and summarizes activity from GitHub repositories. It can retrieve commits, issues, pull requests, and discussions, and then optionally use a Large Language Model (LLM) to generate a concise summary of the repository's recent developments.

## Key Features 🚀

- **Comprehensive Data Fetching:** Gathers detailed repository data, including commits, issues, pull requests, and discussions.
- **Advanced Filtering:** Allows for precise data selection using filters for time ranges, authors, titles, regular expressions, and more.
- **AI-Powered Summaries:** Integrates with LLMs to create intelligent and context-aware summaries of repository activity.
- **Efficient API Usage:** Primarily uses GitHub's GraphQL API for fast and efficient data retrieval.
- **Configurable System Prompt:** Customize the LLM's system prompt for tailored summaries.
- **RSS Feed:** Can generate an RSS feed.
- **Scheduled Runs:** Supports scheduling the summarization process to run automatically.

## Development Principles 🛠️

- **GraphQL-First API Usage:** We prioritize the [GitHub GraphQL API](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql) for its efficiency. It allows us to fetch precisely the data needed in a single request, reducing both over-fetching and the number of API calls.
- **Time Zone Management:**
  - **Standard:** Timestamps from the GitHub API are parsed from the ISO 8601 format.
  - **Internal:** All internal processing, logic, and storage must use UTC.
  - **Display:** All timestamps must be converted to the user's local time zone before being displayed in the UI.
- **Code Style:** We strictly adhere to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) to ensure a readable, consistent, and maintainable codebase.
- **Code Quality and Documentation:** We maintain a high-quality codebase and clear documentation through the following standards:
  - **In-Code:** All modules, classes, and functions must have comprehensive docstrings and complete type annotations.
  - **Usage Examples:** The `README.md` file must contain practical examples demonstrating how to use the program.
  - **Configuration:** A `config.toml.example` file must be provided to show all available configuration options.

## Project Management 📦

This project uses **uv** for fast and reliable dependency and virtual environment management, and **pyrefly** for type checking.

