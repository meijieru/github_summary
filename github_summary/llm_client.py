from openai import OpenAI
import logging
from github_summary.summarizer import LLMClient

logger = logging.getLogger(__name__)


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self, api_key: str | None, base_url: str | None = None, model_name: str = "gpt-3.5-turbo"):
        """Initializes the OpenAICompatibleLLMClient.

        Args:
            api_key: The API key for the OpenAI-compatible service.
            base_url: Optional. The base URL for the API. Defaults to OpenAI's base URL.
            model_name: The name of the model to use for summarization. Defaults to "gpt-3.5-turbo".
        """
        logger.info("Initializing OpenAICompatibleLLMClient with model: %s", model_name)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def generate_summary(self, prompt: str) -> str:
        """Generates a summary using the LLM.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The generated summary string.
        """
        logger.debug("Sending prompt to LLM: %s", prompt)
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=self.model_name,
        )
        summary = chat_completion.choices[0].message.content
        logger.debug("Received summary from LLM.")
        return summary or ""
