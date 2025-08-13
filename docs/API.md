# API Documentation

- **GitHub Integration**: Gidgethub client for GraphQL API access with automatic rate limiting
- **LLM Integration**: AsyncOpenAI client with configurable concurrency and retries
- **Scheduling**: AsyncIOScheduler for native async cron scheduling
- **Concurrency**: Asyncio semaphores for controlled concurrent processing
- **State Management**: Async file operations with proper locking

## GitHub GraphQL Integration

### Client Features

- **Gidgethub**: Production-ready GitHub API client
- **Automatic Rate Limiting**: Built-in rate limit handling and backoff
- **Retries**: Automatic retry logic with exponential backoff
- **Pagination**: Efficient GraphQL pagination handling

### Query Examples

The tool uses optimized GraphQL queries for each data type:

## Async Architecture Details

### Concurrency Control

```python
# Repository processing with semaphores
semaphore = asyncio.Semaphore(max_concurrent)

async def process_with_semaphore(repo):
    async with semaphore:
        return await process_repository(...)

# Process all repositories concurrently
tasks = [process_with_semaphore(repo) for repo in repositories]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Error Handling

```python
# Retry logic with exponential backoff
async for attempt in AsyncRetrying(
    stop=stop_after_attempt(retries),
    wait=wait_exponential(multiplier=retry_delay, min=retry_delay, max=60),
):
    with attempt:
        response = await self.client.chat.completions.create(...)
```

### State Management

```python
# Async file operations with locking
async with _async_lock:
    data = await _read_last_run_times()
    # Update data
    await _write_last_run_times(data)
```

## Architecture Overview

This tool uses a modern async-first architecture:

```graphql
# Commits Query (GET_COMMITS_QUERY)
query ($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $cursor) {
            pageInfo {
              endCursor
              hasNextPage
            }
            nodes {
              oid
              messageHeadline
              url
              author {
                name
                date
              }
            }
          }
        }
      }
    }
  }
}
```

## LLM Integration

### AsyncOpenAI Client

```python
class AsyncLLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model_name: str = "gpt-4",
        retries: int = 3,
        retry_delay: int = 1,
        max_concurrent: int = 3,  # Configurable concurrency
    ):
```

### Features

- **Async Operations**: Non-blocking LLM API calls
- **Configurable Concurrency**: Control concurrent request limits
- **Automatic Retries**: Exponential backoff for failed requests
- **OpenAI Compatible**: Works with OpenAI and compatible endpoints
- **Type Safety**: Full type hints with proper error handling

### System Prompt Structure

The LLM receives a comprehensive system prompt that includes:

1. **Role Definition**: AI assistant specialized in technical changelogs
2. **Output Format**: Two-part summary structure
3. **Analysis Priorities**: Features, bug fixes, breaking changes, etc.
4. **Input Data Description**: Explanation of the JSON structure

### Input Data Format

```json
{
  "repo": "owner/repo-name",
  "commits": [...],
  "pull_requests": [...],
  "issues": [...],
  "discussions": [...]
}
```

### Response Processing

- **Automatic markdown cleanup**: Removes code fences from LLM responses
- **Timezone conversion**: Converts timestamps to configured timezone using zoneinfo
- **Language-specific formatting**: Supports multiple output languages
- **Async processing**: Non-blocking summary generation with concurrent LLM calls

## Web Service API

### Endpoints

#### Health Check

```
GET /healthz
```

Response:

```json
{ "status": "ok" }
```

#### Static Files

```
GET /{path:path}
```

Serves files from the configured `output_dir`, including:

- RSS feeds (`rss.xml`)
- Generated reports (`*.json`, `*.md`)
- Any other output files

### Deployment

#### Docker Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install uv && uv sync

CMD ["github-summary", "web", "--host", "0.0.0.0", "--port", "8000"]
```

#### Environment Variables

- `GITHUB_TOKEN`: GitHub Personal Access Token
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_BASE_URL`: Custom OpenAI base URL
- `GHSUM_CONFIG_PATH`: Path to configuration file

## Rate Limiting

### GitHub API Limits

- **GraphQL**: 5,000 points per hour (handled automatically by gidgethub)
- **Query Cost**: Each query consumes points based on complexity
- **Pagination**: 100 items per page to optimize point usage
- **Automatic Handling**: gidgethub provides built-in rate limit management

### Best Practices

1. Use appropriate `since` timestamps to limit data
2. Gidgethub handles exponential backoff automatically
3. Monitor API usage in logs (rate limit info logged automatically)
4. Optional caching support via gidgethub (disabled by default for simplicity)
5. Configure `max_concurrent` for repository processing to control load

## Error Handling

### Common Errors

- **Invalid GitHub Token**: Check token permissions and scopes
- **Repository Not Found**: Verify repository name format (owner/repo)
- **API Rate Limit**: Handled automatically by gidgethub with backoff
- **LLM API Errors**: AsyncOpenAI client retries with exponential backoff
- **Invalid Cron Expression**: Validated by APScheduler
- **Async Errors**: Proper exception handling with asyncio.gather

### Logging

All components use structured logging with appropriate levels:

- `DEBUG`: Detailed execution information
- `INFO`: Normal operation messages
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors requiring attention

## Extension Points

### Custom LLM Clients

Implement the `AsyncLLMClient` protocol:

```python
class CustomAsyncLLMClient:
    async def generate_summary(self, prompt: str) -> str:
        # Your async implementation
        return "Generated summary"
```

### Async Patterns

When extending the system, follow these async patterns:

```python
# Use async context managers
async with GitHubService(token) as gh_service:
    commits = await gh_service.get_commits(...)

# Use semaphores for concurrency control
semaphore = asyncio.Semaphore(max_concurrent)
async with semaphore:
    result = await some_operation()

# Handle exceptions in concurrent operations
results = await asyncio.gather(*tasks, return_exceptions=True)
for result in results:
    if isinstance(result, Exception):
        logger.error("Operation failed: %s", result)
```

### Custom Filters

Extend filter configurations in `models.py`:

```python
class CustomFilterConfig(BaseModel):
    custom_field: str | None = None
    # Add validation logic
```

### Additional Data Sources

Add new GraphQL queries in `queries.py` and corresponding async service methods in `github_client.py`:

```python
# In queries.py
GET_CUSTOM_DATA_QUERY = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    customField {
      # Your GraphQL query
    }
  }
}
"""

# In github_client.py
async def get_custom_data(self, repo: RepoConfig, filters: FilterConfig, since: datetime) -> list[CustomModel]:
    """Fetch custom data using async GraphQL client."""
    if not repo.include_custom_data:
        return []

    # Use _paginate_graphql for automatic pagination
    custom_data = await self._paginate_graphql(
        GET_CUSTOM_DATA_QUERY,
        variables,
        lambda data: data["repository"]["customField"],
    )

    # Convert to domain models
    return [CustomModel(**item) for item in custom_data]
```
