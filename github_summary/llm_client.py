import asyncio
import logging

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionUserMessageParam
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class AsyncLLMClient:
    """Async LLM client using AsyncOpenAI for concurrent API calls."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model_name: str = "gpt-4",
        retries: int = 3,
        retry_delay: int = 1,
        max_concurrent: int = 3,
    ):
        """Initialize the AsyncOpenAI-based LLM client.

        Args:
            api_key: The API key for authentication.
            base_url: The base URL for the API. If None, uses OpenAI's default.
            model_name: The name of the model to use.
            retries: Number of retry attempts for failed requests.
            retry_delay: Base delay between retries in seconds.
            max_concurrent: Maximum number of concurrent requests.
        """
        self.model_name = model_name
        self.retries = retries
        self.retry_delay = retry_delay
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Create AsyncOpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=0,  # We handle retries ourselves
            timeout=120.0,
        )

    async def generate_summary(self, prompt: str) -> str:
        """Generate a summary from a prompt.

        Args:
            prompt: The full prompt including system instructions and data.

        Returns:
            The generated summary.
        """
        # Use semaphore to limit concurrent LLM requests
        async with self.semaphore:
            return await self._generate_summary_internal(prompt)

    async def _generate_summary_internal(self, prompt: str) -> str:
        """Internal method to generate summary with retry logic."""
        # The prompt already contains everything including system instructions
        messages: list[ChatCompletionUserMessageParam] = [{"role": "user", "content": prompt}]

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.retries),
            wait=wait_exponential(multiplier=self.retry_delay, min=self.retry_delay, max=60),
        ):
            with attempt:
                logger.debug("Making LLM API request with model %s", self.model_name)

                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                )

                if not response.choices:
                    raise ValueError("No choices in LLM response")

                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Empty content in LLM response")

                return content
        raise Exception("Failed to generate summary after multiple retries.")
