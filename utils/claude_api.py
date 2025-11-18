"""
Claude API Wrapper

Handles all interactions with the Anthropic Claude API including:
- Client initialization
- Request formatting
- Error handling and retries
- Response parsing
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Wrapper for Claude API interactions with error handling and retry logic.
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            config: Configuration dictionary with model parameters
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.config = config or {}
        logger.info("Claude API client initialized")

    def call_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Call Claude API with retry logic.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation (0.0 for deterministic)
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed response from Claude

        Raises:
            Exception: If all retries fail
        """
        model = self.config.get("model", "claude-sonnet-4-20250514")

        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Claude API (attempt {attempt + 1}/{max_retries})")

                messages = [{"role": "user", "content": prompt}]

                kwargs = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                }

                if system_prompt:
                    kwargs["system"] = system_prompt

                response = self.client.messages.create(**kwargs)

                # Extract text content from response
                content = response.content[0].text if response.content else ""

                logger.info(f"API call successful (tokens: {response.usage.input_tokens} in, "
                           f"{response.usage.output_tokens} out)")

                return {
                    "content": content,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                }

            except Exception as e:
                logger.error(f"API call failed (attempt {attempt + 1}): {str(e)}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 5
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    raise

        raise Exception("Failed to call Claude API after all retries")

    def validate_json_response(self, content: str) -> Dict:
        """
        Parse and validate JSON response from Claude.

        Args:
            content: Response content string

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If JSON is invalid
        """
        import json

        try:
            # Try to parse the entire content as JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
                return json.loads(json_str)
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                json_str = content[start:end].strip()
                return json.loads(json_str)
            else:
                raise ValueError("Could not parse JSON from response")
