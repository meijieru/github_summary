import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from github_summary.summary_cache import (
    add_summaries_to_cache,
    load_summaries,
    save_summaries,
)


@pytest.fixture(autouse=True)
def clean_cache():
    """Clean cache before and after each test."""
    cache_dir = Path("cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    yield
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


@pytest.fixture
def sample_summaries():
    """Sample summaries for testing."""
    base_time = datetime(2023, 1, 1, tzinfo=UTC)
    return [
        {
            "id": f"repo{i}-{(base_time + timedelta(days=i)).isoformat()}",
            "title": f"Summary for repo{i}",
            "content": f"Content {i}",
            "link": f"https://github.com/repo{i}",
            "timestamp": (base_time + timedelta(days=i)).isoformat(),
        }
        for i in range(3)
    ]


class TestSummaryCache:
    """Test summary cache functionality."""

    @pytest.mark.asyncio
    async def test_empty_cache(self):
        """Test loading from empty cache."""
        summaries = await load_summaries()
        assert summaries == []

    @pytest.mark.asyncio
    async def test_add_batch(self, sample_summaries):
        """Test adding summaries in batch."""
        result = await add_summaries_to_cache(sample_summaries)
        assert result == 3

        loaded = await load_summaries()
        assert len(loaded) == 3

    @pytest.mark.asyncio
    async def test_no_duplicates(self, sample_summaries):
        """Test duplicate prevention."""
        # Add once
        await add_summaries_to_cache(sample_summaries)

        # Add again
        result = await add_summaries_to_cache(sample_summaries)
        assert result == 0  # No new summaries

        loaded = await load_summaries()
        assert len(loaded) == 3

    @pytest.mark.asyncio
    async def test_sorting(self, sample_summaries):
        """Test summaries are sorted by timestamp."""
        await add_summaries_to_cache(sample_summaries)
        loaded = await load_summaries()

        timestamps = [s["timestamp"] for s in loaded]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_save_replaces(self, sample_summaries):
        """Test save_summaries replaces cache."""
        # Add some summaries
        await add_summaries_to_cache(sample_summaries[:2])
        assert len(await load_summaries()) == 2

        # Replace with different summaries
        await save_summaries(sample_summaries[1:])
        loaded = await load_summaries()
        assert len(loaded) == 2

        # Should not contain first summary
        ids = [s["id"] for s in loaded]
        assert sample_summaries[0]["id"] not in ids

    @pytest.mark.asyncio
    async def test_empty_batch(self):
        """Test adding empty batch."""
        result = await add_summaries_to_cache([])
        assert result == 0
        assert await load_summaries() == []
