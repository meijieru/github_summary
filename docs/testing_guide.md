# Testing

## Running Tests

```bash
pytest                                                # All tests
pytest -m unit                                        # unit tests (fast)
pytest -m integration                                 # integration tests (with mocks)
pytest tests/test_config.py::test_load_config_success # Specific test
```

## Code Quality & Linting

Before running tests, ensure your code passes linting and type checking:

```bash
ruff check .       # Check for linting issues (style, imports, etc.)
ruff check . --fix # Auto-fix linting issues where possible
pyrefly check      # Type checking and advanced static analysis
```

**Linting Tools:**

- **ruff**: Fast Python linter covering style, imports, and code quality
- **pyrefly**: Advanced type checker for catching type-related issues

Most linting issues can be automatically fixed with `ruff check . --fix`. For type errors from pyrefly, manual fixes are typically required.

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
