"""Shared state management."""
import asyncio
from typing import Optional, Any, Dict
import numpy as np
from simple_logger import logger
from overlay.macos_overlay import Annotation


class StateManager:
    """Manages shared application state."""

    def __init__(self):
        """Initialize state manager."""
        self._lock = asyncio.Lock()

        # Screen state
        self.current_screen: Optional[np.ndarray] = None
        self.screen_changed: bool = False

        # Audio state
        self.last_transcription: Optional[str] = None
        self.is_speaking: bool = False

        # AI state
        self.last_ai_response: Optional[str] = None
        self.processing_query: bool = False

        # Overlay state
        self.active_annotations: list[Annotation] = []

        # Meeting state
        self.is_in_meeting: bool = False
        self.screen_share_active: bool = False

        logger.info("State manager initialized")

    async def update_screen(self, screen: np.ndarray):
        """
        Update current screen.

        Args:
            screen: Screen frame data
        """
        async with self._lock:
            self.current_screen = screen
            self.screen_changed = True

    async def get_current_screen(self) -> Optional[np.ndarray]:
        """
        Get current screen.

        Returns:
            Current screen frame or None
        """
        async with self._lock:
            return self.current_screen

    async def mark_screen_processed(self):
        """Mark current screen as processed."""
        async with self._lock:
            self.screen_changed = False

    async def update_transcription(self, text: str):
        """
        Update last transcription.

        Args:
            text: Transcribed text
        """
        async with self._lock:
            self.last_transcription = text

    async def get_last_transcription(self) -> Optional[str]:
        """
        Get last transcription.

        Returns:
            Last transcribed text or None
        """
        async with self._lock:
            return self.last_transcription

    async def set_speaking(self, speaking: bool):
        """
        Set speaking state.

        Args:
            speaking: Whether AI is currently speaking
        """
        async with self._lock:
            self.is_speaking = speaking

    async def is_ai_speaking(self) -> bool:
        """
        Check if AI is speaking.

        Returns:
            True if speaking
        """
        async with self._lock:
            return self.is_speaking

    async def set_processing(self, processing: bool):
        """
        Set processing state.

        Args:
            processing: Whether AI is processing a query
        """
        async with self._lock:
            self.processing_query = processing

    async def is_processing(self) -> bool:
        """
        Check if processing.

        Returns:
            True if processing
        """
        async with self._lock:
            return self.processing_query

    async def update_ai_response(self, response: str):
        """
        Update AI response.

        Args:
            response: AI response text
        """
        async with self._lock:
            self.last_ai_response = response

    async def set_meeting_state(self, in_meeting: bool, screen_share: bool = False):
        """
        Update meeting state.

        Args:
            in_meeting: Whether in meeting
            screen_share: Whether screen share is active
        """
        async with self._lock:
            self.is_in_meeting = in_meeting
            self.screen_share_active = screen_share

    async def get_state_summary(self) -> Dict[str, Any]:
        """
        Get summary of current state.

        Returns:
            Dictionary with state information
        """
        async with self._lock:
            return {
                'has_screen': self.current_screen is not None,
                'screen_changed': self.screen_changed,
                'last_transcription': self.last_transcription,
                'is_speaking': self.is_speaking,
                'processing_query': self.processing_query,
                'last_ai_response': self.last_ai_response[:50] + '...' if self.last_ai_response else None,
                'in_meeting': self.is_in_meeting,
                'screen_share_active': self.screen_share_active,
                'active_annotations': len(self.active_annotations)
            }
