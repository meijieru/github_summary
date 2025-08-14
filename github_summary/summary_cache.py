import asyncio
import functools
import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

CACHE_FILE_PATH = Path("cache/summary_cache.json")
DEFAULT_MAX_ENTRIES = 100


class SummaryCache:
    """Simple summary cache with batch operations."""

    def __init__(self, cache_file: Path = CACHE_FILE_PATH, max_entries: int = DEFAULT_MAX_ENTRIES):
        self.cache_file = cache_file
        self.max_entries = max_entries

    async def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, functools.partial(self.cache_file.parent.mkdir, parents=True, exist_ok=True))

    async def load_all(self) -> List[Dict]:
        """Load all summaries from cache."""
        loop = asyncio.get_running_loop()

        if not await loop.run_in_executor(None, self.cache_file.exists):
            return []

        try:

            def _read():
                with open(self.cache_file, "r") as f:
                    return json.load(f)

            return await loop.run_in_executor(None, _read)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Could not load cache, starting fresh: %s", e)
            return []

    async def save_all(self, summaries: List[Dict]):
        """Save all summaries to cache."""
        await self._ensure_cache_dir()
        loop = asyncio.get_running_loop()

        # Sort by timestamp (newest first) and limit
        sorted_summaries = sorted(summaries, key=lambda x: x["timestamp"], reverse=True)
        limited_summaries = sorted_summaries[: self.max_entries]

        def _write():
            with open(self.cache_file, "w") as f:
                json.dump(limited_summaries, f, indent=2)

        await loop.run_in_executor(None, _write)
        logger.debug("Saved %d summaries to cache", len(limited_summaries))

    async def add_batch(self, new_summaries: List[Dict]) -> int:
        """Add multiple summaries, avoiding duplicates."""
        if not new_summaries:
            return 0

        # Load existing
        existing = await self.load_all()
        existing_ids = {s["id"] for s in existing}

        # Filter duplicates
        unique_new = []
        for summary in new_summaries:
            if summary["id"] not in existing_ids:
                unique_new.append(summary)
                existing_ids.add(summary["id"])

        if not unique_new:
            logger.debug("No new summaries to add (all duplicates)")
            return 0

        # Combine and save
        all_summaries = existing + unique_new
        await self.save_all(all_summaries)

        logger.info("Added %d new summaries to cache", len(unique_new))
        return len(unique_new)


# Global instance
_cache = SummaryCache()


async def load_summaries() -> List[Dict]:
    """Load all summaries."""
    return await _cache.load_all()


async def add_summaries_to_cache(summaries: List[Dict]) -> int:
    """Add multiple summaries to cache."""
    return await _cache.add_batch(summaries)


async def save_summaries(summaries: List[Dict]):
    """Replace cache with new summaries."""
    await _cache.save_all(summaries)
