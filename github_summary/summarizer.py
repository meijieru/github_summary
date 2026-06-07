import json
import logging
from datetime import datetime
from typing import Any, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

AUDIENCE_GUIDANCE = {
    "user": (
        "Optimize for practical user impact: upgrades, new capabilities, compatibility risks, and visible behavior "
        "changes. Keep implementation details only when they explain user-facing consequences."
    ),
    "maintainer": (
        "Optimize for maintainers: module-level implications, migration work, operational risk, testing impact, and "
        "implementation-relevant context. Still explain why the change matters."
    ),
    "mixed": (
        "Balance user impact with concise technical context. Explain why a change matters without turning the summary "
        "into release-note prose or an implementation diary."
    ),
}


class AsyncLLMClient(Protocol):
    """A protocol defining the interface for an async LLM client."""

    async def generate_summary(self, system_prompt: str, prompt: str) -> str:
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
        audience: str = "mixed",
        language: str | None = None,
        timezone: str | None = None,
    ):
        """Initializes the Summarizer.

        Args:
            llm_client: An object that conforms to the AsyncLLMClient protocol.
            system_prompt: The base system prompt for the LLM.
            audience: The target audience perspective for the summary.
            language: The desired language for the summary (e.g., "en", "es").
            timezone: The timezone for displaying timestamps (e.g., "America/New_York").
        """
        logger.info("Initializing Summarizer.")
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.audience = audience
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

    def _build_system_prompt(self, audience: str | None = None) -> str:
        selected_audience = audience or self.audience
        prompt_lines = [
            self.system_prompt.strip(),
            AUDIENCE_GUIDANCE.get(selected_audience, AUDIENCE_GUIDANCE["mixed"]),
            (
                "Return GitHub-flavored Markdown only. Use normal Markdown lists and links; do not wrap the answer in "
                "a code block."
            ),
        ]
        if self.language:
            prompt_lines.append(
                f"Write the final summary in {self.language}. Do not translate common technical terms or abbreviations."
            )
        return "\n\n".join(prompt_lines)

    def _build_user_prompt(self, info: dict, last_run_time: datetime | None) -> str:
        prompt_lines = [
            "Summarize the repository activity in the JSON payload below.",
            "Use only facts supported by the input. If something is uncertain, omit it rather than infer.",
            "Keep the output concise and high-signal. Do not rewrite the entire release notes.",
            "Every referenced GitHub object must be a Markdown link using its html_url from the input.",
            "For pull requests, use the format [#123 Title](https://github.com/owner/repo/pull/123).",
            "Never mention a pull request number, title, or status without a hyperlink.",
            "Do not use Markdown tables; use bullets so the summary renders consistently in RSS readers.",
            "Treat releases, merged pull requests, closed issues, and already-landed commits as completed work.",
            "Treat open pull requests as active developments only. Never mix them into completed-work sections.",
            "If the same change appears in multiple input objects, mention it once using the most canonical source.",
            "Avoid marketing language, roadmap speculation, placeholder notes, or self-corrections.",
            "",
            "Output format",
            "## TL;DR",
            "- 2-4 bullets only.",
            "- Mention only the most important completed changes.",
            "- Each bullet should explain why the reader should care.",
            "- Do not mention open pull requests here.",
            "- Link each referenced commit, release, issue, or merged pull request.",
            "",
            "## Details",
            "- Cover at most 4 completed items.",
            "- Prioritize: releases, breaking changes, major user-facing features, critical fixes, major performance or architecture changes.",
            "- Expand only the most important items from TL;DR; do not restate everything.",
            "- Distinguish facts from implications. Keep implications modest and directly supported by the input.",
            "- Use linked GitHub object titles as anchors where possible.",
            "- If little happened, say so plainly.",
            "",
            "## Watchlist",
            "- Optional section.",
            "- Include at most 3 notable open pull requests.",
            "- For each item, give the linked pull request title and one short sentence on why it is worth watching.",
            "- Omit the section entirely if there are no clearly notable open pull requests in the input.",
            "",
            "Input JSON",
        ]
        if last_run_time:
            display_time = last_run_time.astimezone(self._tz) if self._tz else last_run_time
            prompt_lines.insert(
                1, f"The previous successful run was at {display_time.strftime('%Y-%m-%d %H:%M:%S %Z')}."
            )
        prompt_lines.extend(("```json", json.dumps(info, indent=2), "```"))
        return "\n".join(prompt_lines)

    async def summarize(self, info: dict, last_run_time: datetime | None, audience: str | None = None) -> str:
        """Generates a summary of GitHub activity.

        This method builds a prompt from the provided information, sends it to the
        LLM, and returns the cleaned-up summary.

        Args:
            info: A dictionary containing GitHub activity data (commits, PRs, etc.).
            last_run_time: The UTC datetime of the last run, used for context.
            audience: Optional per-repository audience override.

        Returns:
            A string containing the generated summary.
        """
        logger.info("Generating LLM prompt for %s", info.get("repo", "unknown"))

        # Convert timestamps if a valid timezone is set
        processed_info = self._convert_timestamps(info, self._tz) if self._tz else info

        system_prompt = self._build_system_prompt(audience)
        prompt = self._build_user_prompt(processed_info, last_run_time)
        logger.debug("Generated system prompt: %s", system_prompt)
        logger.debug("Generated user prompt: %s", prompt)
        summary = await self.llm_client.generate_summary(system_prompt, prompt)

        # Clean up the summary output
        if summary.startswith("```markdown"):
            summary = summary[len("```markdown") :].strip()
        if summary.endswith("```"):
            summary = summary[: -len("```")].strip()

        return summary
