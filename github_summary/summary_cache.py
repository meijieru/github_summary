import asyncio
import functools
import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

# Define the cache file path directly within the cache directory
CACHE_FILE_PATH = Path("cache/summary_cache.json")
MAX_CACHE_ENTRIES = 100  # Configurable: max number of entries to keep


async def _ensure_cache_dir_exists():
    """Ensures the cache directory exists."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, functools.partial(CACHE_FILE_PATH.parent.mkdir, parents=True, exist_ok=True))


async def load_summaries() -> List[Dict]:
    """Loads summaries from the cache file."""
    loop = asyncio.get_running_loop()
    if not await loop.run_in_executor(None, CACHE_FILE_PATH.exists):
        return []
    try:

        def _read_file():
            with open(CACHE_FILE_PATH, "r") as f:
                return json.load(f)

        return await loop.run_in_executor(None, _read_file)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Could not decode summary cache. Starting with empty data: %s", e)
        return []


async def save_summaries(summaries: List[Dict]):
    """Saves summaries to the cache file."""
    await _ensure_cache_dir_exists()
    loop = asyncio.get_running_loop()
    try:
        # Sort by timestamp before saving to keep the file tidy
        sorted_summaries = sorted(summaries, key=lambda x: x["timestamp"], reverse=True)

        def _write_file():
            with open(CACHE_FILE_PATH, "w") as f:
                json.dump(sorted_summaries, f, indent=2)

        await loop.run_in_executor(None, _write_file)
    except IOError as e:
        logger.error("Failed to save summary cache: %s", e)


async def add_summary_to_cache(new_summary: Dict):
    """Adds a new summary to the cache, ensuring no duplicates and pruning old entries."""
    summaries = await load_summaries()

    # Prevent duplicates by checking the unique ID
    summary_ids = {s["id"] for s in summaries}
    if new_summary["id"] in summary_ids:
        logger.info("Summary with ID %s already in cache. Skipping.", new_summary["id"])
        return

    summaries.append(new_summary)

    # Sort by date and prune the cache
    sorted_summaries = sorted(summaries, key=lambda x: x["timestamp"], reverse=True)
    pruned_summaries = sorted_summaries[:MAX_CACHE_ENTRIES]

    await save_summaries(pruned_summaries)
    logger.info("Added new summary for %s to cache.", new_summary["title"])
