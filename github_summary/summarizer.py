import json
import logging
from datetime import datetime
from typing import Any, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """{system_prompt}

```json
{info}
```"""


class AsyncLLMClient(Protocol):
    """A protocol defining the interface for an async LLM client."""

    async def generate_summary(self, prompt: str) -> str:
        """Generates a summary for the given prompt."""
        ...


class Summarizer:
    """Handles the generation of summaries from repository data using an LLM.

    This class orchestrates the process of building a detailed prompt,
    including system instructions, language preferences, and repository activity data.
    It then uses an LLM client to generate a summary and cleans up the output.
    """

    def __init__(
        self,
        llm_client: AsyncLLMClient,
        system_prompt: str,
        language: str | None = None,
        timezone: str | None = None,
    ):
        """Initializes the Summarizer.

        Args:
            llm_client: An object that conforms to the AsyncLLMClient protocol.
            system_prompt: The base system prompt for the LLM.
            language: The desired language for the summary (e.g., "en", "es").
            timezone: The timezone for displaying timestamps (e.g., "America/New_York").
        """
        logger.info("Initializing Summarizer.")
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.language = language
        self.timezone_str = timezone
        self._tz = self._get_timezone()

    def _get_timezone(self) -> ZoneInfo | None:
        """Parses the timezone string and returns a ZoneInfo object.

        Returns:
            A ZoneInfo object if the timezone string is valid, otherwise None.
        """
        if not self.timezone_str:
            return None
        try:
            return ZoneInfo(self.timezone_str)
        except ZoneInfoNotFoundError:
            logger.warning(
                "Invalid timezone '%s' specified. Timestamps will remain in UTC.",
                self.timezone_str,
            )
            return None

    @staticmethod
    def _convert_timestamps(data: Any, tz: ZoneInfo) -> Any:
        """Recursively converts ISO 8601 timestamp strings in a dictionary to a given timezone.

        Args:
            data: The dictionary, list, or value to process.
            tz: The timezone to convert timestamps to.

        Returns:
            The processed data with converted timestamps.
        """
        if isinstance(data, dict):
            return {key: Summarizer._convert_timestamps(value, tz) for key, value in data.items()}
        if isinstance(data, list):
            return [Summarizer._convert_timestamps(item, tz) for item in data]
        if isinstance(data, str):
            try:
                dt = datetime.fromisoformat(data.replace("Z", "+00:00"))
                return dt.astimezone(tz).isoformat()
            except (ValueError, TypeError):
                return data
        return data

    async def summarize(self, info: dict, last_run_time: datetime | None) -> str:
        """Generates a summary of GitHub activity.

        This method builds a prompt from the provided information, sends it to the
        LLM, and returns the cleaned-up summary.

        Args:
            info: A dictionary containing GitHub activity data (commits, PRs, etc.).
            last_run_time: The UTC datetime of the last run, used for context.

        Returns:
            A string containing the generated summary.
        """
        logger.info("Generating LLM prompt for %s", info.get("repo", "unknown"))

        # Convert timestamps if a valid timezone is set
        processed_info = self._convert_timestamps(info, self._tz) if self._tz else info

        # Build the system prompt
        prompt_lines = [self.system_prompt]
        if self.language:
            prompt_lines.append(
                f"Please provide the summary in {self.language}. "
                "Do not translate common technical terms or abbreviations."
            )

        if last_run_time:
            display_time = last_run_time.astimezone(self._tz) if self._tz else last_run_time
            prompt_lines.append(f"The last run was at {display_time.strftime('%Y-%m-%d %H:%M:%S %Z')}.")

        system_prompt = "\n".join(prompt_lines)

        # Create the full prompt and generate the summary
        prompt = PROMPT_TEMPLATE.format(
            system_prompt=system_prompt,
            info=json.dumps(processed_info, indent=2),
        )
        logger.debug("Generated prompt: %s", prompt)
        summary = await self.llm_client.generate_summary(prompt)

        # Clean up the summary output
        if summary.startswith("```markdown"):
            summary = summary[len("```markdown") :].strip()
        if summary.endswith("```"):
            summary = summary[: -len("```")].strip()

        return summary
