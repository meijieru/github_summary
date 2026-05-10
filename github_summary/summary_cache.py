import json
import logging
import os
import tempfile
from pathlib import Path

from github_summary.paths import get_default_cache_dir

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = get_default_cache_dir()
CACHE_FILE_PATH = DEFAULT_CACHE_DIR / "summary_cache.json"
DEFAULT_MAX_ENTRIES = 100


class SummaryCache:
    """Simple summary cache with batch operations."""

    def __init__(self, cache_file: Path = CACHE_FILE_PATH, max_entries: int = DEFAULT_MAX_ENTRIES):
        self.cache_file = cache_file
        self.max_entries = max_entries

    async def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    async def load_all(self) -> list[dict]:
        """Load all summaries from cache."""
        if not self.cache_file.exists():
            return []

        try:

            def _read_file():
                with open(self.cache_file, "r") as f:
                    return json.load(f)

            return _read_file()
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Could not load cache, starting fresh: %s", e)
            return []

    async def save_all(self, summaries: list[dict]) -> None:
        """Save all summaries to cache."""
        await self._ensure_cache_dir()

        # Sort by timestamp (newest first) and limit
        sorted_summaries = sorted(summaries, key=lambda x: x["timestamp"], reverse=True)
        limited_summaries = sorted_summaries[: self.max_entries]

        def _write_file():
            with tempfile.NamedTemporaryFile("w", dir=self.cache_file.parent, delete=False) as f:
                json.dump(limited_summaries, f, indent=2)
                temp_file = Path(f.name)
            os.replace(temp_file, self.cache_file)

        _write_file()
        logger.debug("Saved %d summaries to cache", len(limited_summaries))

    async def add_batch(self, new_summaries: list[dict]) -> int:
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


# Default global instance, used when no cache directory is supplied.
_cache = SummaryCache()


def _get_cache(cache_dir: str | os.PathLike[str] | None = None) -> SummaryCache:
    """Return the default cache or a cache rooted at cache_dir."""
    if cache_dir is None:
        return _cache
    return SummaryCache(cache_file=Path(cache_dir) / "summary_cache.json")


async def load_summaries(cache_dir: str | os.PathLike[str] | None = None) -> list[dict]:
    """Load all summaries."""
    return await _get_cache(cache_dir).load_all()


async def add_summaries_to_cache(summaries: list[dict], cache_dir: str | os.PathLike[str] | None = None) -> int:
    """Add multiple summaries to cache."""
    return await _get_cache(cache_dir).add_batch(summaries)


async def save_summaries(summaries: list[dict], cache_dir: str | os.PathLike[str] | None = None) -> None:
    """Replace cache with new summaries."""
    await _get_cache(cache_dir).save_all(summaries)
