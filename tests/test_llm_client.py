from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from github_summary.llm_client import AsyncLLMClient


class TestAsyncLLMClient:
    """Test cases for the async LLM client."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_simple(self):
        """Test text generation using generate_summary."""

        # Mock AsyncOpenAI
        with patch("github_summary.llm_client.AsyncOpenAI") as mock_openai:
            # Create async mock for the client method
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            # Mock the response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test summary"

            # Make the create method return the mock response
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            client = AsyncLLMClient(
                api_key="test_key",
                base_url="https://api.openai.com/v1",
                model_name="gpt-4",
            )

            result = await client.generate_summary("Test prompt")

            assert result == "Test summary"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_with_retries(self):
        """Test retry functionality on failure."""
        with patch("github_summary.llm_client.AsyncOpenAI") as mock_openai:
            # Create async mock for the client
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            # First call fails, second succeeds
            mock_success_response = MagicMock()
            mock_success_response.choices = [MagicMock()]
            mock_success_response.choices[0].message.content = "Success"

            mock_client.chat.completions.create = AsyncMock(
                side_effect=[
                    Exception("Network error"),
                    mock_success_response,
                ]
            )

            client = AsyncLLMClient(
                api_key="test_key",
                retries=2,
                retry_delay=1,  # Fast retry for testing
            )

            result = await client.generate_summary("Test prompt")

            assert result == "Success"
            assert mock_client.chat.completions.create.call_count == 2
