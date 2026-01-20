"""Conversation context management."""
from collections import deque
from typing import List, Dict, Optional
from simple_logger import logger
from config import config


class ContextManager:
    """Manages conversation context and history."""

    def __init__(self):
        """Initialize context manager."""
        self.messages: deque = deque(maxlen=config.ai.max_context_messages)
        self.screen_history: deque = deque(maxlen=config.ai.max_context_frames)

        logger.info(f"Context manager initialized (max messages: {config.ai.max_context_messages})")

    def add_user_message(self, text: str, screen_data: Optional[bytes] = None):
        """
        Add user message to context.

        Args:
            text: User's message text
            screen_data: Optional screen image data
        """
        message = {
            "role": "user",
            "content": text
        }

        self.messages.append(message)

        if screen_data:
            self.screen_history.append(screen_data)

        logger.debug(f"Added user message: '{text[:50]}...'")

    def add_assistant_message(self, text: str):
        """
        Add assistant message to context.

        Args:
            text: Assistant's response text
        """
        message = {
            "role": "assistant",
            "content": text
        }

        self.messages.append(message)
        logger.debug(f"Added assistant message: '{text[:50]}...'")

    def get_context(self) -> List[Dict]:
        """
        Get current conversation context.

        Returns:
            List of messages in context
        """
        return list(self.messages)

    def get_recent_screens(self, count: int = 3) -> List[bytes]:
        """
        Get recent screen images.

        Args:
            count: Number of recent screens to retrieve

        Returns:
            List of screen image data
        """
        return list(self.screen_history)[-count:]

    def clear_context(self):
        """Clear all context."""
        self.messages.clear()
        self.screen_history.clear()
        logger.info("Context cleared")

    def get_context_stats(self) -> Dict:
        """
        Get statistics about current context.

        Returns:
            Dictionary with context statistics
        """
        return {
            'message_count': len(self.messages),
            'screen_count': len(self.screen_history),
            'max_messages': self.messages.maxlen,
            'max_screens': self.screen_history.maxlen
        }
