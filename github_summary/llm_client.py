from openai import OpenAI
from github_summary.summarizer import LLMClient


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self, api_key: str, base_url: str | None = None, model_name: str = "gpt-3.5-turbo"):
        """Initializes the OpenAICompatibleLLMClient.

        Args:
            api_key: The API key for the OpenAI-compatible service.
            base_url: Optional. The base URL for the API. Defaults to OpenAI's base URL.
            model_name: The name of the model to use for summarization. Defaults to "gpt-3.5-turbo".
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def generate_summary(self, prompt: str) -> str:
        """Generates a summary using the LLM.

        Args:
            prompt: The prompt to send to the LLM.

        Returns:
            The generated summary string.
        """
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=self.model_name,
        )
        return chat_completion.choices[0].message.content
