from typing import Protocol
import json
import logging
import textwrap


logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    """A protocol defining the interface for an LLM client.

    Any class implementing this protocol must provide a `generate_summary` method.
    """

    def generate_summary(self, prompt: str) -> str: ...


class Summarizer:
    def __init__(self, llm_client: LLMClient, system_prompt: str):
        """Initializes the Summarizer with an LLM client and a system prompt.

        Args:
            llm_client: An instance of a class implementing the LLMClient protocol.
            system_prompt: The base system prompt to use for summarization.
        """
        logger.info("Initializing Summarizer.")
        self.llm_client = llm_client
        self.system_prompt = system_prompt

    def summarize(self, info) -> str:
        """Generates a summary of GitHub activity using the LLM client."""

        logger.info("Generating LLM prompt.")
        prompt = textwrap.dedent(f"""
        {self.system_prompt}

        ```json
        {json.dumps(info, indent=2)}
        ```
        """).strip()
        logger.debug("Generated prompt: %s", prompt)
        return self.llm_client.generate_summary(prompt)
