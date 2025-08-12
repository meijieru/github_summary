# API Documentation

## GitHub GraphQL Queries

This tool primarily uses GitHub's GraphQL API for efficient data retrieval.

## LLM Integration

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

- Automatic markdown cleanup (removes code fences)
- Timezone conversion for timestamps
- Language-specific formatting

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

- **GraphQL**: 5,000 points per hour
- **Query Cost**: Each query consumes points based on complexity
- **Pagination**: 100 items per page to optimize point usage

### Best Practices

1. Use appropriate `since` timestamps to limit data
2. Implement exponential backoff for rate limit hits
3. Monitor API usage in logs
4. Consider caching for frequently accessed data

## Error Handling

### Common Errors

- **Invalid GitHub Token**: Check token permissions
- **Repository Not Found**: Verify repository name format
- **API Rate Limit**: Implement retry logic
- **LLM API Errors**: Check API key and model availability
- **Invalid Cron Expression**: Use validation tools

### Logging

All components use structured logging with appropriate levels:

- `DEBUG`: Detailed execution information
- `INFO`: Normal operation messages
- `WARNING`: Non-critical issues
- `ERROR`: Critical errors requiring attention

## Extension Points

### Custom LLM Clients

Implement the `LLMClient` protocol:

```python
class CustomLLMClient:
    def generate_summary(self, prompt: str) -> str:
        # Your implementation
        pass
```

### Custom Filters

Extend filter configurations in `models.py`:

```python
class CustomFilterConfig(BaseModel):
    custom_field: str | None = None
    # Add validation logic
```

### Additional Data Sources

Add new GraphQL queries in `queries.py` and corresponding service methods in `github_client.py`.
