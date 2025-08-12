# Configuration Reference

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

**Environment Variables:**

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`

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

Global scheduling configuration. Include this section to enable automatic runs.

| Field      | Type   | Default     | Description     |
| ---------- | ------ | ----------- | --------------- |
| `cron`     | string | `0 6 * * *` | Cron expression |
| `timezone` | string | System      | Timezone name   |

**To disable scheduling:** Simply omit the `[schedule]` section entirely.

**Common Cron Patterns:**

- `"0 6 * * *"` - Daily at 6 AM
- `"0 9,17 * * *"` - Daily at 9 AM and 5 PM
- `"0 9 * * 1"` - Every Monday at 9 AM
- `"0 9-17 * * 1-5"` - Hourly during business hours, weekdays only
- `"*/15 * * * *"` - Every 15 minutes

### Global Settings

| Field                    | Type    | Default  | Description         |
| ------------------------ | ------- | -------- | ------------------- |
| `log_level`              | string  | `INFO`   | Logging level       |
| `output_dir`             | string  | `output` | Output directory    |
| `since_last_run`         | boolean | `true`   | Track last run time |
| `fallback_lookback_days` | integer | 7        | Fallback time range |
| `timezone`               | string  | System   | Default timezone    |

## Example Configurations

> 💡 **Tip**: Copy configurations from the [`examples/`](../examples/) directory for ready-to-use templates.
