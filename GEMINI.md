# GitHub Repository Summarizer

Gemini CLI is a command-line tool that fetches and summarizes activity from GitHub repositories. It can retrieve commits, issues, pull requests, and discussions, and then optionally use a Large Language Model (LLM) to generate a concise summary of the repository's recent developments.

## Key Features 🚀

- **Comprehensive Data Fetching:** Gathers a wide range of repository data, including commits, issues, pull requests, and discussions.
- **Advanced Filtering:** Allows for precise data selection using filters for time ranges, titles, regular expressions, and more.
- **AI-Powered Summaries:** Leverages the power of LLMs to create intelligent and context-aware summaries.
- **Efficient API Usage:** Primarily uses GitHub's GraphQL API for fast and efficient queries.

## Development Principles 🛠️

- **Prioritize GraphQL API:** We prefer using the [GitHub GraphQL API](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql) for its efficiency and ability to fetch precisely the data needed in a single request.
- **Code Style:** The project adheres to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) to ensure code is readable, consistent, and maintainable.
- **Code Quality:** We maintain high standards for code quality through comprehensive docstrings and complete type annotations.

## Project Management 📦

This project uses **uv** for fast and reliable dependency and virtual environment management, and **pyrefly** for type checking.
