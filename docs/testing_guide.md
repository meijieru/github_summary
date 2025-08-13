# Testing

## Running Tests

```bash
pytest                                                # All tests
pytest -m unit                                        # unit tests (fast)
pytest -m integration                                 # integration tests (with mocks)
pytest tests/test_config.py::test_load_config_success # Specific test
```

## Test Structure

- **`test_config.py`** - Configuration loading and validation (3 tests)
- **`test_github_client.py`** - GitHub GraphQL API client (19 tests)
- **`test_cron_schedule.py`** - APScheduler integration (9 tests)
- **`test_rss.py`** - RSS feed generation (4 tests)
- **`test_summarizer.py`** - LLM integration (2 tests)

## Writing Tests

Use `@pytest.mark.unit` for fast tests, `@pytest.mark.integration` for tests with `@patch`:

```python
@pytest.mark.unit
def test_schedule_config_validation():
    schedule = ScheduleConfig(cron="0 9 * * *")
    assert schedule.cron == "0 9 * * *"

@pytest.mark.integration
@patch("github_summary.scheduler.load_config")
def test_scheduler_registers_jobs(mock_load_config):
    # Test with mocked dependencies
```

Fixtures are defined per-file (see `test_github_client.py` for GitHub API fixtures).

