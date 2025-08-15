from unittest.mock import patch

import pytest

from github_summary.summary_cache import SummaryCache


@pytest.fixture(autouse=True)
def isolate_last_run_cache(tmp_path):
    """Fixture to patch the last run times cache file path."""
    temp_file = tmp_path / "last_run_times.json"
    with patch("github_summary.last_run_manager.LAST_RUN_TIMES_FILE", temp_file):
        yield


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path):
    """Clean cache before and after each test."""
    # Create isolated cache for each test to avoid touching real cache
    test_cache_dir = tmp_path / "test_cache"
    test_cache_file = test_cache_dir / "summary_cache.json"
    test_cache_instance = SummaryCache(cache_file=test_cache_file)

    with patch("github_summary.summary_cache._cache", test_cache_instance):
        yield
