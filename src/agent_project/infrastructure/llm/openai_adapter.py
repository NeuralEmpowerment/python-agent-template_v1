"""OpenAI LLM adapter for agent interactions."""

from typing import Dict, List, Optional

from openai import AsyncOpenAI

from src.agent_project.config.settings import get_settings
from src.agent_project.infrastructure.logging import get_context_logger


class OpenAIAdapter:
    """
    OpenAI LLM adapter implementing the LLMProvider protocol.

    This adapter handles communication with OpenAI's API for generating
    agent responses. In development mode, it gracefully handles missing
    or invalid API keys.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        """Initialize the OpenAI adapter."""
        settings = get_settings()

        # Use provided API key or get from settings
        if api_key is None:
            api_key = settings.openai.api_key

        # Check if API key is valid (not the default placeholder)
        self.is_configured = bool(api_key and api_key != "your-api-key-here")

        if self.is_configured:
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            # In development mode, don't fail immediately - just log warning
            self.client = None

        self.logger = get_context_logger()

        if not self.is_configured:
            self.logger.warning(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable. "
                "Some features will not be available."
            )

    def _check_configuration(self) -> None:
        """Check if the adapter is properly configured."""
        if not self.is_configured:
            raise ValueError(
                "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable. "
                "Get your API key from: https://platform.openai.com/api-keys"
            )

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> str:
        """
        Generate a response using OpenAI's API.

        Args:
            messages: List of messages in OpenAI format
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated response text

        Raises:
            ValueError: If OpenAI API key is not configured
        """
        self._check_configuration()

        self.logger.info(f"Generating response with model: {model}")

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            content = response.choices[0].message.content or ""

            self.logger.info(
                f"Response generated successfully. "
                f"Tokens used: {response.usage.total_tokens if response.usage else 'unknown'}"
            )

            return content.strip()

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}", exc_info=True)
            raise

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ) -> None:
        """
        Generate a streaming response using OpenAI's API.

        Args:
            messages: List of messages in OpenAI format
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive

        Raises:
            ValueError: If OpenAI API key is not configured
        """
        self._check_configuration()

        self.logger.info(f"Starting streaming response with model: {model}")

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}", exc_info=True)
            raise

    async def health_check(self) -> bool:
        """Check if the OpenAI API is accessible."""
        if not self.is_configured:
            return False

        try:
            # Simple test call to verify connectivity
            await self.client.models.list()
            self.logger.info("OpenAI API health check passed")
            return True
        except Exception as e:
            self.logger.error(f"OpenAI API health check failed: {str(e)}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        # Common OpenAI models for reference
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
