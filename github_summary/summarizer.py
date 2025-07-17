import json
import logging
from datetime import datetime
from typing import Protocol

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """{system_prompt}

```json
{info}
```"""


class LLMClient(Protocol):
    """A protocol defining the interface for an LLM client.

    Any class implementing this protocol must provide a `generate_summary` method.
    """

    def generate_summary(self, prompt: str) -> str: ...


class Summarizer:
    def __init__(self, llm_client: LLMClient, system_prompt: str, language: str | None = None):
        """Initializes the Summarizer with an LLM client and a system prompt.

        Args:
            llm_client: An instance of a class implementing the LLMClient protocol.
            system_prompt: The base system prompt to use for summarization.
            language: The language for the summary.
        """
        logger.info("Initializing Summarizer.")
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.language = language

    def summarize(self, info: dict, last_run_time: datetime | None) -> str:
        """Generates a summary of GitHub activity using the LLM client."""

        logger.info("Generating LLM prompt.")
        system_prompt = self.system_prompt
        if self.language:
            system_prompt += f"\nPlease provide the summary in {self.language}. Do not translate common technical terms or abbreviations."

        if last_run_time:
            system_prompt += f"\n\nThe last run was at {last_run_time.strftime('%Y-%m-%d %H:%M:%S UTC')}."

        prompt = PROMPT_TEMPLATE.format(system_prompt=system_prompt, info=json.dumps(info, indent=2))
        logger.debug("Generated prompt: %s", prompt)
        return self.llm_client.generate_summary(prompt)
