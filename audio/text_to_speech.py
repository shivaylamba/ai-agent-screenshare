"""Text-to-speech using ElevenLabs API."""
import asyncio
from typing import Optional
from elevenlabs import generate, set_api_key, voices
from simple_logger import logger
from config import config
from utils.performance import measure_time_async


class TextToSpeech:
    """Convert text to speech using ElevenLabs API."""

    def __init__(self):
        """Initialize ElevenLabs TTS client."""
        set_api_key(config.tts.elevenlabs_api_key)
        self.voice_id = config.tts.voice_id
        self.model = config.tts.model
        self._cache = {}  # Simple response cache

        logger.info(f"Text-to-speech initialized with voice: {self.voice_id}")

    @measure_time_async("tts_synthesize")
    async def synthesize(self, text: str, use_cache: bool = True) -> bytes:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert to speech
            use_cache: Whether to use cached responses for common phrases

        Returns:
            Audio data in bytes (MP3 format)
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for TTS")
                return b''

            # Check cache for common responses
            if use_cache and text in self._cache:
                logger.debug(f"Using cached TTS for: '{text[:30]}...'")
                return self._cache[text]

            logger.info(f"Synthesizing speech: '{text[:50]}...'")

            # Generate speech (run in thread pool since it's blocking)
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(
                None,
                lambda: generate(
                    text=text,
                    voice=self.voice_id,
                    model=self.model
                )
            )

            # Cache short, common responses
            if use_cache and len(text) < 100:
                self._cache[text] = audio

            logger.debug(f"Speech synthesized: {len(audio)} bytes")
            return audio

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b''

    async def synthesize_ssml(self, ssml: str) -> bytes:
        """
        Convert SSML markup to speech (if supported).

        Args:
            ssml: SSML markup string

        Returns:
            Audio data in bytes
        """
        # ElevenLabs doesn't directly support SSML, but we can parse it
        # For now, just extract text and synthesize
        import re
        text = re.sub('<[^<]+?>', '', ssml)  # Remove tags
        return await self.synthesize(text)

    def clear_cache(self):
        """Clear the TTS response cache."""
        self._cache.clear()
        logger.info("TTS cache cleared")

    def get_cache_size(self) -> int:
        """
        Get number of cached responses.

        Returns:
            Number of cached items
        """
        return len(self._cache)

    async def list_available_voices(self) -> list:
        """
        Get list of available voices.

        Returns:
            List of voice dictionaries
        """
        try:
            loop = asyncio.get_event_loop()
            voice_list = await loop.run_in_executor(None, voices)
            return voice_list
        except Exception as e:
            logger.error(f"Error listing voices: {e}")
            return []

    def preload_common_phrases(self):
        """Preload common phrases into cache."""
        common_phrases = [
            "I can help you with that.",
            "Let me analyze that for you.",
            "I see. Let me check.",
            "Here's what I found.",
            "That looks correct.",
            "Let me guide you through this.",
            "Click here.",
            "Go to this location.",
            "I'm analyzing your screen now.",
        ]

        async def _preload():
            for phrase in common_phrases:
                await self.synthesize(phrase, use_cache=True)
            logger.info(f"Preloaded {len(common_phrases)} common phrases")

        asyncio.create_task(_preload())
