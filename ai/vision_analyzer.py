"""Vision analysis for screen content."""
from typing import Optional, Dict
import numpy as np
from simple_logger import logger
from ai.claude_client import ClaudeClient
from capture.screen_capturer import ScreenCapturer


class VisionAnalyzer:
    """Analyzes screen content using Claude vision."""

    def __init__(self):
        """Initialize vision analyzer."""
        self.claude = ClaudeClient()
        self.last_analysis = None

        logger.info("Vision analyzer initialized")

    async def analyze_frame(
        self,
        frame: np.ndarray,
        query: str,
        context: Optional[list] = None
    ) -> Dict:
        """
        Analyze a screen frame.

        Args:
            frame: Frame data as numpy array
            query: User's question or request
            context: Conversation context

        Returns:
            Analysis result with text and annotations
        """
        try:
            # Convert frame to JPEG
            capturer = ScreenCapturer()
            image_bytes = capturer.frame_to_jpeg(frame)

            # Analyze with Claude
            result = await self.claude.analyze_screen(
                image_data=image_bytes,
                user_query=query,
                context=context
            )

            self.last_analysis = result
            return result

        except Exception as e:
            logger.error(f"Error analyzing frame: {e}")
            return {
                "text": "I couldn't analyze that screen.",
                "annotations": []
            }

    def get_last_analysis(self) -> Optional[Dict]:
        """
        Get the last analysis result.

        Returns:
            Last analysis result or None
        """
        return self.last_analysis
