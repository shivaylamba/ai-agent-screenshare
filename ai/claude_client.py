"""Claude API client with vision support."""
import base64
from typing import Optional, List, Dict
from anthropic import AsyncAnthropic
from simple_logger import logger
from config import config
from utils.performance import measure_time_async


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(self):
        """Initialize Claude client."""
        self.client = AsyncAnthropic(api_key=config.ai.anthropic_api_key)
        self.model = config.ai.model
        self.max_tokens = config.ai.max_tokens
        self.temperature = config.ai.temperature

        logger.info(f"Claude client initialized with model: {self.model}")

    @measure_time_async("claude_vision_analysis")
    async def analyze_screen(
        self,
        image_data: bytes,
        user_query: str,
        context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Analyze screen image with optional query.

        Args:
            image_data: Image data in bytes (JPEG)
            user_query: User's question or request
            context: Previous conversation context

        Returns:
            Dictionary with response text and annotations
        """
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            # Build messages
            messages = context or []

            # Add current message with image and query
            current_message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": self._build_vision_prompt(user_query)
                    }
                ]
            }

            messages.append(current_message)

            # Call Claude API
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=messages
            )

            # Extract response
            response_text = response.content[0].text if response.content else ""

            logger.info(f"Claude response ({len(response_text)} chars)")

            # Parse response for annotations
            result = self._parse_response(response_text)

            return result

        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            return {
                "text": "I'm having trouble analyzing the screen right now.",
                "annotations": []
            }

    def _build_vision_prompt(self, user_query: str) -> str:
        """Build prompt for vision analysis."""
        return f"""You are an AI assistant helping a user with their screen.
Analyze the screen image and respond to their query.

User query: {user_query}

Provide:
1. A helpful, conversational response
2. Visual guidance if relevant (describe where to click, what to look at)

Keep your response natural and concise. Focus on being helpful."""

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse Claude's response for text and annotations.

        Args:
            response_text: Raw response from Claude

        Returns:
            Dictionary with text and annotations
        """
        # For now, return simple structure
        # In production, you could parse structured JSON responses
        return {
            "text": response_text,
            "annotations": []  # Annotations would be parsed from structured response
        }

    async def chat(self, message: str, context: Optional[List[Dict]] = None) -> str:
        """
        Simple chat without vision.

        Args:
            message: User message
            context: Conversation context

        Returns:
            Claude's response text
        """
        try:
            messages = context or []
            messages.append({
                "role": "user",
                "content": message
            })

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=messages
            )

            return response.content[0].text if response.content else ""

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "I'm having trouble responding right now."
