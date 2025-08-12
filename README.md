# GitHub Repository Summarizer

A CLI tool that fetches GitHub repository activity and generates AI-powered summaries.

## 🚀 Quick Start

1. **Install dependencies:**

   ```bash
   pip install uv
   uv sync
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
model_name = "gpt-4"
language = "English"
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

# List repository labels
github-summary utils list-labels owner/repo
```

## ✨ Features

- **Multi-source data**: Commits, PRs, issues, discussions
- **AI summaries**: LLM-powered intelligent summaries
- **Flexible scheduling**: Cron-based scheduling with timezone support
- **RSS feeds**: Generate RSS feeds for summaries
- **Advanced filtering**: Regex patterns, author filters, label filters
- **Web service**: Serve RSS feeds and schedule reports

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
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
