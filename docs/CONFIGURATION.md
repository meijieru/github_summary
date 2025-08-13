# Configuration Reference

### Per-Repository Scheduling

You can also configure individual schedules for specific repositories:

```toml
[[repositories]]
name = "owner/repo1"
schedule = { cron = "0 9 * * *", timezone = "UTC" }

[[repositories]]
name = "owner/repo2"
schedule = { cron = "0 17 * * 5", timezone = "America/New_York" }
```

## Quick Start Examples

See the [`examples/`](../examples/) directory for ready-to-use configurations:

- **`basic.toml`** - Simple getting started configuration
- **`minimal.toml`** - Basic template for customization
- **`scheduling.toml`** - Comprehensive scheduling examples
- **`advanced.toml`** - Full-featured configuration

## Configuration Sections

### GitHub API (`[github]`)

| Field   | Type   | Required | Description                  |
| ------- | ------ | -------- | ---------------------------- |
| `token` | string | Yes      | GitHub Personal Access Token |

**Environment Variable:** `GITHUB_TOKEN`

### Performance Settings (`[performance]`)

Configuration for concurrency and performance tuning.

| Field                  | Type    | Default | Description                          |
| ---------------------- | ------- | ------- | ------------------------------------ |
| `max_concurrent_repos` | integer | 4       | Max concurrent repository processing |
| `max_concurrent_llm`   | integer | 3       | Max concurrent LLM API requests      |

**Environment Variables:**

- `GHSUM_CONCURRENT_REPOS`: Overrides `max_concurrent_repos`

### Global Filters (`[filters]`)

Applied to all repositories unless overridden by repository-specific filters.

#### Commits (`[filters.commits]`)

| Field                           | Type   | Description                      |
| ------------------------------- | ------ | -------------------------------- |
| `author`                        | string | Filter by commit author          |
| `exclude_commit_messages_regex` | string | Regex to exclude commit messages |

#### Pull Requests (`[filters.pull_requests]`)

| Field                               | Type   | Description                |
| ----------------------------------- | ------ | -------------------------- |
| `author`                            | string | Filter by PR author        |
| `state`                             | string | `OPEN`, `CLOSED`, `MERGED` |
| `labels`                            | array  | Required labels            |
| `exclude_pull_request_titles_regex` | string | Regex to exclude PR titles |
| `since_filter_type`                 | string | `updated` or `created`     |

#### Issues (`[filters.issues]`)

| Field                        | Type   | Description                   |
| ---------------------------- | ------ | ----------------------------- |
| `author`                     | string | Filter by issue author        |
| `labels`                     | array  | Required labels               |
| `assignee`                   | string | Filter by assignee            |
| `milestone`                  | string | Filter by milestone           |
| `exclude_issue_titles_regex` | string | Regex to exclude issue titles |

#### Discussions (`[filters.discussions]`)

| Field                             | Type   | Description                        |
| --------------------------------- | ------ | ---------------------------------- |
| `author`                          | string | Filter by discussion author        |
| `exclude_discussion_titles_regex` | string | Regex to exclude discussion titles |

### Repositories (`[[repositories]]`)

| Field                   | Type    | Default  | Description                       |
| ----------------------- | ------- | -------- | --------------------------------- |
| `name`                  | string  | Required | Repository in `owner/repo` format |
| `include_commits`       | boolean | `true`   | Include commit data               |
| `include_pull_requests` | boolean | `true`   | Include PR data                   |
| `include_issues`        | boolean | `true`   | Include issue data                |
| `include_discussions`   | boolean | `true`   | Include discussion data           |
| `filters`               | object  | {}       | Repository-specific filters       |
| `schedule`              | object  | null     | Repository-specific schedule      |

### LLM Configuration (`[llm]`)

| Field           | Type    | Default   | Description                     |
| --------------- | ------- | --------- | ------------------------------- |
| `base_url`      | string  | OpenAI    | API base URL                    |
| `api_key`       | string  | Required  | LLM API key                     |
| `model_name`    | string  | `gpt-4.1` | Model identifier                |
| `language`      | string  | null      | Summary language                |
| `retries`       | integer | 3         | Retry attempts                  |
| `retry_delay`   | integer | 1         | Delay between retries (seconds) |
| `system_prompt` | string  | Default   | Custom system prompt            |

### LLM Client Features

- **AsyncOpenAI Integration**: Native async client with proper connection pooling
- **Configurable Concurrency**: Control concurrent LLM API requests with `max_concurrent`
- **Automatic Retries**: Exponential backoff for failed requests
- **OpenAI Compatible**: Works with OpenAI API and compatible endpoints (Anthropic, local models, etc.)
- **Type Safety**: Full type hints and error handling

**Environment Variables:**

### RSS Configuration (`[rss]`)

RSS feed generation. Include this section to enable RSS output.

| Field         | Type   | Default   | Description          |
| ------------- | ------ | --------- | -------------------- |
| `title`       | string | Default   | RSS feed title       |
| `link`        | string | Required  | RSS feed URL         |
| `description` | string | Default   | RSS feed description |
| `filename`    | string | `rss.xml` | Output filename      |

**To disable RSS:** Simply omit the `[rss]` section entirely.

### Scheduling (`[schedule]`)

Global scheduling configuration using AsyncIOScheduler. Include this section to enable automatic runs.

| Field      | Type   | Default     | Description     |
| ---------- | ------ | ----------- | --------------- |
| `cron`     | string | `0 6 * * *` | Cron expression |
| `timezone` | string | System      | Timezone name   |

### Scheduler Features

- **AsyncIOScheduler**: Native async scheduling without blocking the event loop
- **Per-Repository Scheduling**: Each repository can have its own schedule
- **Timezone Support**: Full timezone support using system timezone data
- **Graceful Shutdown**: Proper cleanup of running async jobs
- **Error Handling**: Failed jobs don't affect other scheduled jobs

**To disable scheduling:** Simply omit the `[schedule]` section entirely.

**Common Cron Patterns:**

### Global Settings

| Field                    | Type    | Default  | Description         |
| ------------------------ | ------- | -------- | ------------------- |
| `log_level`              | string  | `INFO`   | Logging level       |
| `output_dir`             | string  | `output` | Output directory    |
| `since_last_run`         | boolean | `true`   | Track last run time |
| `fallback_lookback_days` | integer | 7        | Fallback time range |
| `timezone`               | string  | System   | Default timezone    |

### Performance Configuration

The application supports several configuration options and environment variables for performance tuning:

#### Concurrency Control

The tool uses a two-tier concurrency system:

1. **Repository Concurrency**: How many repositories to process simultaneously
2. **LLM Concurrency**: How many LLM API requests can run concurrently

These work as **independent limits**, not multiplicative factors.

| Environment Variable     | Default | Description                          |
| ------------------------ | ------- | ------------------------------------ |
| `GHSUM_CONCURRENT_REPOS` | 4       | Max concurrent repository processing |
| `GHSUM_CONFIG_PATH`      | -       | Override config file path            |

#### Configuration Priority

Concurrency settings are applied in this order (highest to lowest priority):

1. CLI argument (`--max-concurrent-repos`)
2. Environment variable (`GHSUM_CONCURRENT_REPOS`)
3. Configuration file (`performance.max_concurrent_repos`)
4. Default value (4)

### Async Architecture Benefits

The async-first design provides several performance advantages:

- **Concurrent Repository Processing**: Process multiple repositories simultaneously
- **Non-blocking I/O**: All file operations use async I/O to prevent blocking
- **Configurable Concurrency**: Control both repository and LLM request concurrency
- **Efficient API Usage**: Gidgethub provides optimal GitHub API interaction
- **Memory Efficient**: Async operations reduce memory usage compared to threading

### Tuning Guidelines

- **LLM Concurrency**: Start with 3 concurrent requests, adjust based on API limits
- **Independent Controls**: Repository and LLM concurrency work as separate throttles
- **Total LLM Load**: Actual concurrent LLM requests = min(active_repos, llm.max_concurrent)

For detailed concurrency tuning guidance, see [docs/CONCURRENCY.md](./CONCURRENCY.md).

## Example Configurations

> 💡 **Tip**: Copy configurations from the [`examples/`](../examples/) directory for ready-to-use templates.
