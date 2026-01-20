"""Voice Activity Detection for filtering audio input."""
import webrtcvad
from simple_logger import logger
from config import config


class VADDetector:
    """Detect voice activity in audio streams."""

    def __init__(self, aggressiveness: int = None):
        """
        Initialize VAD detector.

        Args:
            aggressiveness: VAD aggressiveness level (0-3)
                           0 = least aggressive (more false positives)
                           3 = most aggressive (more false negatives)
        """
        self.aggressiveness = aggressiveness or config.audio.vad_aggressiveness
        self.vad = webrtcvad.Vad(self.aggressiveness)
        self.sample_rate = config.audio.sample_rate

        logger.info(f"VAD initialized with aggressiveness: {self.aggressiveness}")

    def is_speech(self, audio_chunk: bytes, sample_rate: int = None) -> bool:
        """
        Detect if audio chunk contains speech.

        Args:
            audio_chunk: Audio data in bytes (must be 10, 20, or 30 ms)
            sample_rate: Sample rate in Hz (8000, 16000, 32000, or 48000)

        Returns:
            True if speech detected, False otherwise
        """
        try:
            sample_rate = sample_rate or self.sample_rate

            # Ensure sample rate is valid
            if sample_rate not in [8000, 16000, 32000, 48000]:
                logger.warning(f"Invalid sample rate {sample_rate}, using 16000")
                sample_rate = 16000

            # Check if audio chunk length is valid (10, 20, or 30 ms)
            frame_duration_ms = len(audio_chunk) / (sample_rate * 2 / 1000)
            if frame_duration_ms not in [10, 20, 30]:
                logger.debug(f"Invalid frame duration: {frame_duration_ms}ms")
                return False

            return self.vad.is_speech(audio_chunk, sample_rate)

        except Exception as e:
            logger.debug(f"VAD error: {e}")
            return False

    def process_audio_stream(self, audio_chunks: list, sample_rate: int = None) -> bool:
        """
        Process multiple audio chunks and determine if speech is present.

        Args:
            audio_chunks: List of audio chunks
            sample_rate: Sample rate in Hz

        Returns:
            True if majority of chunks contain speech
        """
        if not audio_chunks:
            return False

        speech_count = 0
        for chunk in audio_chunks:
            if self.is_speech(chunk, sample_rate):
                speech_count += 1

        # Return True if more than 30% of chunks contain speech
        threshold = len(audio_chunks) * 0.3
        return speech_count > threshold

    def update_aggressiveness(self, level: int):
        """
        Update VAD aggressiveness level.

        Args:
            level: New aggressiveness level (0-3)
        """
        if 0 <= level <= 3:
            self.aggressiveness = level
            self.vad.set_mode(level)
            logger.info(f"VAD aggressiveness updated to: {level}")
        else:
            logger.warning(f"Invalid aggressiveness level: {level}")
