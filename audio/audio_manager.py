"""Main audio manager coordinating all audio operations."""
import asyncio
import wave
import io
from typing import Optional, Callable
from simple_logger import logger
from config import config
from audio.vad_detector import VADDetector
from audio.speech_to_text import SpeechToText
from audio.text_to_speech import TextToSpeech


class AudioManager:
    """Manages audio input, output, and processing."""

    def __init__(self):
        """Initialize audio manager."""
        self.vad = VADDetector()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()

        self.is_listening = False
        self.audio_buffer = []
        self.silence_counter = 0
        self.silence_threshold = int(config.audio.silence_duration * config.audio.sample_rate / config.audio.chunk_size)

        self.on_transcription_callback: Optional[Callable] = None
        self.on_audio_generated_callback: Optional[Callable] = None

        # Processing state
        self._processing_buffer = False
        self._last_transcription: Optional[str] = None
        self._last_transcription_time = 0.0
        self._cooldown_period = 3.0  # Seconds to wait before processing same transcription again
        self._is_speaking = False  # Track when TTS is playing

        logger.info("Audio manager initialized")

    async def process_audio_chunk(self, audio_chunk: bytes):
        """
        Process incoming audio chunk.

        Args:
            audio_chunk: Audio data in bytes
        """
        try:
            # Skip processing if we're currently speaking (prevent feedback loop)
            if self._is_speaking:
                return

            # Skip if already processing buffer
            if self._processing_buffer:
                return

            # Check for voice activity
            has_speech = self.vad.is_speech(audio_chunk)

            if has_speech:
                # Add to buffer
                self.audio_buffer.append(audio_chunk)
                self.silence_counter = 0
                self.is_listening = True
            elif self.is_listening:
                # Increment silence counter
                self.silence_counter += 1

                # If silence threshold reached, process buffered audio
                if self.silence_counter >= self.silence_threshold:
                    await self._process_buffered_audio()

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")

    async def _process_buffered_audio(self):
        """Process accumulated audio buffer."""
        if not self.audio_buffer:
            return

        # Prevent concurrent processing
        if self._processing_buffer:
            logger.debug("Already processing audio buffer, skipping")
            return

        self._processing_buffer = True

        try:
            import time
            current_time = time.time()

            logger.info(f"Processing {len(self.audio_buffer)} audio chunks")

            # Reset buffer immediately to prevent duplicate processing
            buffer_copy = self.audio_buffer.copy()
            self.audio_buffer = []
            self.is_listening = False
            self.silence_counter = 0

            # Convert chunks to WAV format
            wav_data = self._chunks_to_wav(buffer_copy)

            # Transcribe
            text = await self.stt.transcribe(wav_data)

            # Validate transcription
            if self.stt.is_valid_transcription(text):
                # Check for duplicate transcription (same text within cooldown period)
                if (text == self._last_transcription and 
                    current_time - self._last_transcription_time < self._cooldown_period):
                    logger.debug(f"Skipping duplicate transcription: '{text}' (within cooldown)")
                    return

                # Update last transcription
                self._last_transcription = text
                self._last_transcription_time = current_time

                logger.success(f"User said: '{text}'")

                # Call callback if set
                if self.on_transcription_callback:
                    if asyncio.iscoroutinefunction(self.on_transcription_callback):
                        await self.on_transcription_callback(text)
                    else:
                        self.on_transcription_callback(text)

        except Exception as e:
            logger.error(f"Error processing buffered audio: {e}")
        finally:
            self._processing_buffer = False

    def _chunks_to_wav(self, chunks: list[bytes]) -> bytes:
        """
        Convert audio chunks to WAV format.

        Args:
            chunks: List of audio chunks

        Returns:
            WAV audio data in bytes
        """
        # Combine all chunks
        audio_data = b''.join(chunks)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(config.audio.channels)
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(config.audio.sample_rate)
            wav_file.writeframes(audio_data)

        return wav_buffer.getvalue()

    async def synthesize_and_play(self, text: str):
        """
        Synthesize text to speech and trigger playback.

        Args:
            text: Text to convert to speech
        """
        try:
            # Mark as speaking to prevent feedback loop
            self._is_speaking = True

            logger.info(f"Synthesizing: '{text[:50]}...'")

            # Generate speech
            audio_data = await self.tts.synthesize(text)

            if audio_data and self.on_audio_generated_callback:
                # Trigger callback to play audio
                if asyncio.iscoroutinefunction(self.on_audio_generated_callback):
                    await self.on_audio_generated_callback(audio_data)
                else:
                    self.on_audio_generated_callback(audio_data)

            # Estimate speaking duration (rough estimate: ~150 words per minute)
            import time
            word_count = len(text.split())
            estimated_duration = (word_count / 150.0) * 60.0  # seconds
            # Add buffer time
            await asyncio.sleep(min(estimated_duration + 1.0, 10.0))

        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
        finally:
            # Unmute after speaking is done
            self._is_speaking = False
            logger.debug("Finished speaking, audio capture re-enabled")

    def set_transcription_callback(self, callback: Callable):
        """
        Set callback for when text is transcribed.

        Args:
            callback: Function to call with transcribed text
        """
        self.on_transcription_callback = callback
        logger.info("Transcription callback set")

    def set_audio_generated_callback(self, callback: Callable):
        """
        Set callback for when audio is generated.

        Args:
            callback: Function to call with generated audio bytes
        """
        self.on_audio_generated_callback = callback
        logger.info("Audio generated callback set")

    def clear_buffer(self):
        """Clear the audio buffer."""
        self.audio_buffer = []
        self.is_listening = False
        self.silence_counter = 0
        logger.debug("Audio buffer cleared")

    def get_buffer_info(self) -> dict:
        """
        Get information about current audio buffer.

        Returns:
            Dictionary with buffer information
        """
        return {
            'chunk_count': len(self.audio_buffer),
            'is_listening': self.is_listening,
            'silence_counter': self.silence_counter,
            'buffer_size_bytes': sum(len(chunk) for chunk in self.audio_buffer)
        }
