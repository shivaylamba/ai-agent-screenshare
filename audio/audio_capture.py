"""Audio capture from microphone or browser."""
import asyncio
import pyaudio
import threading
from typing import Optional, Callable
from simple_logger import logger
from config import config


class AudioCapture:
    """Captures audio from microphone or browser."""

    def __init__(self, source: str = "microphone"):
        """
        Initialize audio capture.

        Args:
            source: Audio source ('microphone' or 'browser')
        """
        self.source = source
        self.audio = None
        self.stream = None
        self.is_capturing = False
        self.on_audio_chunk: Optional[Callable] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info(f"Audio capture initialized with source: {source}")

    async def start_capture(self, callback: Callable):
        """
        Start capturing audio.

        Args:
            callback: Function to call with audio chunks (bytes)
        """
        if self.is_capturing:
            logger.warning("Audio capture already running")
            return

        # Store reference to event loop
        self._event_loop = asyncio.get_event_loop()
        self.on_audio_chunk = callback

        if self.source == "microphone":
            await self._start_microphone_capture()
        elif self.source == "browser":
            await self._start_browser_capture()
        else:
            raise ValueError(f"Unknown audio source: {self.source}")

    async def _start_microphone_capture(self):
        """Start capturing from microphone."""
        try:
            self.audio = pyaudio.PyAudio()

            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=config.audio.channels,
                rate=config.audio.sample_rate,
                input=True,
                frames_per_buffer=config.audio.chunk_size,
                stream_callback=self._audio_callback
            )

            self.stream.start_stream()
            self.is_capturing = True
            logger.success("Microphone capture started")

        except Exception as e:
            logger.error(f"Error starting microphone capture: {e}")
            await self.stop_capture()
            raise

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream (runs in separate thread)."""
        if self.on_audio_chunk and self.is_capturing and self._event_loop:
            # Schedule callback in the main event loop
            # This is thread-safe when the loop is running
            try:
                if self._event_loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._process_chunk(in_data), 
                        self._event_loop
                    )
            except Exception as e:
                logger.error(f"Error scheduling audio chunk: {e}")
        return (None, pyaudio.paContinue)

    async def _process_chunk(self, chunk: bytes):
        """Process audio chunk."""
        if self.on_audio_chunk:
            if asyncio.iscoroutinefunction(self.on_audio_chunk):
                await self.on_audio_chunk(chunk)
            else:
                self.on_audio_chunk(chunk)

    async def _start_browser_capture(self):
        """Start capturing from browser (requires browser page)."""
        # This will be implemented when browser page is available
        logger.warning("Browser audio capture not yet implemented")
        raise NotImplementedError("Browser audio capture requires browser integration")

    async def stop_capture(self):
        """Stop capturing audio."""
        if not self.is_capturing:
            return

        self.is_capturing = False

        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error stopping stream: {e}")

        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating audio: {e}")

        self.stream = None
        self.audio = None
        logger.info("Audio capture stopped")

    def is_active(self) -> bool:
        """
        Check if capture is active.

        Returns:
            True if capturing
        """
        return self.is_capturing

