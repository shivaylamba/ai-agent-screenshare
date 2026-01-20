"""Speech-to-text using OpenAI Whisper API."""
import asyncio
import tempfile
import os
from typing import Optional
from openai import AsyncOpenAI
from simple_logger import logger
from config import config
from utils.performance import measure_time_async


class SpeechToText:
    """Convert speech audio to text using Whisper API."""

    def __init__(self):
        """Initialize Whisper STT client."""
        self.client = AsyncOpenAI(api_key=config.stt.openai_api_key)
        self.model = config.stt.model
        self.language = config.stt.language

        logger.info(f"Speech-to-text initialized with model: {self.model}")

    @measure_time_async("stt_transcribe")
    async def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio data in bytes (WAV format)
            language: Language code (e.g., 'en', 'es'), None for auto-detect

        Returns:
            Transcribed text
        """
        try:
            language = language or self.language

            # Whisper API requires a file, so create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            try:
                # Transcribe using Whisper API
                with open(temp_path, 'rb') as audio_file:
                    transcript = await self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=language,
                        response_format="text"
                    )

                # Extract text from response
                if isinstance(transcript, str):
                    text = transcript
                else:
                    text = transcript.text if hasattr(transcript, 'text') else str(transcript)

                text = text.strip()

                if text:
                    logger.info(f"Transcribed: '{text}'")
                else:
                    logger.debug("Empty transcription result")

                return text

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    async def transcribe_stream(self, audio_chunks: list[bytes]) -> str:
        """
        Transcribe multiple audio chunks as a stream.

        Args:
            audio_chunks: List of audio chunks in bytes

        Returns:
            Combined transcribed text
        """
        # Combine chunks into single audio data
        combined_audio = b''.join(audio_chunks)

        if not combined_audio:
            return ""

        return await self.transcribe(combined_audio)

    def is_valid_transcription(self, text: str) -> bool:
        """
        Check if transcription result is valid.

        Args:
            text: Transcribed text

        Returns:
            True if valid, False otherwise
        """
        if not text:
            return False

        # Filter out common Whisper artifacts
        artifacts = ['[BLANK_AUDIO]', '[MUSIC]', '[NOISE]', '(static)', '...']
        text_lower = text.lower()

        for artifact in artifacts:
            if artifact.lower() in text_lower:
                return False

        # Check minimum length
        if len(text.strip()) < 2:
            return False

        return True
