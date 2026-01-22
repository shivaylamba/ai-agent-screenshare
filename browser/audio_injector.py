"""Audio injection into Google Meet calls."""
import asyncio
import base64
from typing import Optional
from playwright.async_api import Page
from simple_logger import logger


class AudioInjector:
    """Injects audio into Google Meet via browser automation."""

    def __init__(self, page: Page):
        """
        Initialize audio injector.

        Args:
            page: Playwright page object
        """
        self.page = page
        self._audio_context_initialized = False

        logger.info("Audio injector initialized")

    async def initialize_audio_context(self):
        """Initialize Web Audio API context in the browser."""
        if self._audio_context_initialized:
            return

        try:
            # Inject JavaScript directly into the page (since page is already loaded)
            # This ensures the function is available immediately
            await self.page.evaluate("""
                // Only initialize if not already initialized
                if (!window.customAudioContext) {
                    // Create audio context
                    window.customAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                    window.customAudioQueue = [];
                    window.isPlayingCustomAudio = false;

                    // Function to play audio from base64
                    window.playCustomAudio = async function(base64Audio) {
                        try {
                            // Decode base64 to array buffer
                            const binaryString = atob(base64Audio);
                            const bytes = new Uint8Array(binaryString.length);
                            for (let i = 0; i < binaryString.length; i++) {
                                bytes[i] = binaryString.charCodeAt(i);
                            }

                            // Decode audio data
                            const audioBuffer = await window.customAudioContext.decodeAudioData(bytes.buffer);

                            // Create source
                            const source = window.customAudioContext.createBufferSource();
                            source.buffer = audioBuffer;
                            source.connect(window.customAudioContext.destination);

                            // Play
                            source.start(0);

                            return true;
                        } catch (error) {
                            console.error('Error playing custom audio:', error);
                            return false;
                        }
                    };

                    console.log('Custom audio context initialized');
                }
            """)

            self._audio_context_initialized = True
            logger.success("Audio context initialized in browser")

        except Exception as e:
            logger.error(f"Error initializing audio context: {e}")

    async def inject_audio(self, audio_data: bytes):
        """
        Inject audio into the Meet call.

        Args:
            audio_data: Audio data in bytes (MP3 or WAV)
        """
        try:
            # Ensure audio context is initialized
            await self.initialize_audio_context()

            # Convert audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Use a more robust injection method that handles large strings
            # We'll pass the base64 as a separate argument to avoid f-string issues
            result = await self.page.evaluate("""
                async function(base64Audio) {
                    // Re-initialize if needed (safety check)
                    if (!window.customAudioContext) {
                        window.customAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                    }
                    
                    if (!window.playCustomAudio) {
                        window.playCustomAudio = async function(base64Audio) {
                            try {
                                // Decode base64 to array buffer
                                const binaryString = atob(base64Audio);
                                const bytes = new Uint8Array(binaryString.length);
                                for (let i = 0; i < binaryString.length; i++) {
                                    bytes[i] = binaryString.charCodeAt(i);
                                }

                                // Decode audio data (supports MP3, WAV, etc.)
                                const audioBuffer = await window.customAudioContext.decodeAudioData(bytes.buffer);

                                // Create source
                                const source = window.customAudioContext.createBufferSource();
                                source.buffer = audioBuffer;
                                source.connect(window.customAudioContext.destination);

                                // Play
                                source.start(0);

                                return true;
                            } catch (error) {
                                console.error('Error playing custom audio:', error);
                                return false;
                            }
                        };
                    }

                    // Call the function
                    return await window.playCustomAudio(base64Audio);
                }
            """, audio_base64)

            if result:
                logger.success("Audio injected successfully")
            else:
                logger.warning("Audio injection may have failed")

        except Exception as e:
            logger.error(f"Error injecting audio: {e}")

    async def set_audio_output_device(self, device_id: Optional[str] = None):
        """
        Set audio output device (if supported).

        Args:
            device_id: Audio device ID, None for default
        """
        try:
            # This is browser-dependent and may not work in all cases
            if device_id:
                await self.page.evaluate(f"""
                    navigator.mediaDevices.getUserMedia({{audio: {{deviceId: '{device_id}'}} }})
                """)
                logger.info(f"Audio output device set to: {device_id}")

        except Exception as e:
            logger.debug(f"Could not set audio output device: {e}")

    async def get_audio_devices(self) -> list:
        """
        Get list of available audio devices.

        Returns:
            List of audio device information
        """
        try:
            devices = await self.page.evaluate("""
                navigator.mediaDevices.enumerateDevices().then(devices =>
                    devices.filter(d => d.kind === 'audiooutput')
                )
            """)
            return devices
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
            return []
