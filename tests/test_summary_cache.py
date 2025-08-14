import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from github_summary.summary_cache import (
    CACHE_FILE_PATH,
    MAX_CACHE_ENTRIES,
    _ensure_cache_dir_exists,
    add_summary_to_cache,
    load_summaries,
    save_summaries,
)


@pytest.fixture(autouse=True)
def setup_and_teardown_cache_dir():
    """Ensures a clean cache directory for each test."""
    cache_dir_for_tests = Path("cache")
    if cache_dir_for_tests.exists():
        shutil.rmtree(cache_dir_for_tests)
    cache_dir_for_tests.mkdir(parents=True, exist_ok=True)

    yield

    if cache_dir_for_tests.exists():
        shutil.rmtree(cache_dir_for_tests)


@pytest.fixture
def sample_summary():
    """Return a sample summary dictionary."""
    return {
        "id": "test/repo-2025-08-13T12:00:00Z",
        "title": "Summary for test/repo",
        "content": "This is a test summary.",
        "link": "https://github.com/test/repo",
        "timestamp": datetime.now(UTC).isoformat(),
    }


class TestSummaryCache:
    """Test cases for the summary cache functionality."""

    @pytest.mark.asyncio
    async def test_load_summaries_no_file(self):
        """Test loading summaries when the cache file doesn't exist."""
        summaries = await load_summaries()
        assert summaries == []

    @pytest.mark.asyncio
    async def test_load_summaries_corrupted_file(self):
        """Test loading summaries from a corrupted JSON file."""
        await _ensure_cache_dir_exists()
        with open(CACHE_FILE_PATH, "w") as f:
            f.write("this is not json")

        summaries = await load_summaries()
        assert summaries == []

    @pytest.mark.asyncio
    async def test_save_and_load_summaries(self, sample_summary):
        """Test saving and then loading summaries."""
        summaries_to_save = [sample_summary]
        await save_summaries(summaries_to_save)

        loaded_summaries = await load_summaries()
        assert len(loaded_summaries) == 1
        assert loaded_summaries[0]["id"] == sample_summary["id"]

    @pytest.mark.asyncio
    async def test_add_summary_to_cache(self, sample_summary):
        """Test adding a single summary to the cache."""
        await add_summary_to_cache(sample_summary)

        summaries = await load_summaries()
        assert len(summaries) == 1
        assert summaries[0]["id"] == sample_summary["id"]

    @pytest.mark.asyncio
    async def test_add_summary_deduplication(self, sample_summary):
        """Test that adding a summary with a duplicate ID is skipped."""
        await add_summary_to_cache(sample_summary)
        await add_summary_to_cache(sample_summary)

        summaries = await load_summaries()
        assert len(summaries) == 1

    @pytest.mark.asyncio
    async def test_cache_pruning(self):
        """Test that the cache is pruned to MAX_CACHE_ENTRIES."""
        for i in range(MAX_CACHE_ENTRIES + 5):
            summary = {
                "id": f"id_{i}",
                "title": "Title",
                "content": "Content",
                "link": "link",
                "timestamp": (datetime.now(UTC) - timedelta(days=i)).isoformat(),
            }
            await add_summary_to_cache(summary)

        summaries = await load_summaries()
        assert len(summaries) == MAX_CACHE_ENTRIES

    @pytest.mark.asyncio
    async def test_cache_sorting(self):
        """Test that the cache is sorted by timestamp."""
        summaries_to_add = []
        for i in range(5):
            summaries_to_add.append(
                {
                    "id": f"id_{i}",
                    "title": "Title",
                    "content": "Content",
                    "link": "link",
                    "timestamp": (datetime.now(UTC) - timedelta(minutes=i)).isoformat(),
                }
            )

        for summary in reversed(summaries_to_add):
            await add_summary_to_cache(summary)

        loaded_summaries = await load_summaries()

        assert loaded_summaries[0]["id"] == "id_0"
        assert loaded_summaries[-1]["id"] == "id_4"
