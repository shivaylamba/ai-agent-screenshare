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
        logger.info("Audio injector initialized")

    async def inject_audio(self, audio_data: bytes, local_playback: bool = True):
        """
        Inject audio into the Meet call.

        Args:
            audio_data: Audio data in bytes (MP3 or WAV)
            local_playback: Also play audio locally so user can hear
        """
        try:
            # Convert audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Choose injection function based on local playback preference
            js_function = "injectAudioToMeetWithLocalPlayback" if local_playback else "injectAudioToMeet"

            # Check if injection is ready
            is_ready = await self.page.evaluate("() => window._audioInjectorReady === true")
            
            if not is_ready:
                logger.warning("Audio injector not ready yet - Meet may not have initialized microphone")
                # Try to play locally at least
                await self._play_audio_locally(audio_base64)
                return

            # Inject the audio
            result = await self.page.evaluate(f"""
                async function(base64Audio) {{
                    if (typeof window.{js_function} === 'function') {{
                        return await window.{js_function}(base64Audio);
                    }} else {{
                        console.error('[AudioInjector] Function not found');
                        return {{ success: false, error: 'Function not initialized' }};
                    }}
                }}
            """, audio_base64)

            if result and result.get('success'):
                duration = result.get('duration', 0)
                logger.success(f"Audio injected successfully (duration: {duration:.2f}s)")
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                logger.warning(f"Audio injection may have failed: {error}")

        except Exception as e:
            logger.error(f"Error injecting audio: {e}")

    async def _play_audio_locally(self, audio_base64: str):
        """Fallback: play audio through browser's speakers."""
        try:
            await self.page.evaluate("""
                async function(base64Audio) {
                    try {
                        const ctx = new (window.AudioContext || window.webkitAudioContext)();
                        const binaryString = atob(base64Audio);
                        const bytes = new Uint8Array(binaryString.length);
                        for (let i = 0; i < binaryString.length; i++) {
                            bytes[i] = binaryString.charCodeAt(i);
                        }
                        const audioBuffer = await ctx.decodeAudioData(bytes.buffer.slice(0));
                        const source = ctx.createBufferSource();
                        source.buffer = audioBuffer;
                        source.connect(ctx.destination);
                        source.start(0);
                        console.log('[AudioInjector] Playing audio locally (fallback)');
                        return true;
                    } catch (e) {
                        console.error('[AudioInjector] Local playback error:', e);
                        return false;
                    }
                }
            """, audio_base64)
            logger.info("Audio played locally (fallback mode)")
        except Exception as e:
            logger.error(f"Error playing audio locally: {e}")

    async def check_status(self) -> dict:
        """Check if audio injection is properly set up."""
        try:
            status = await self.page.evaluate("""
                () => ({
                    ready: window._audioInjectorReady === true,
                    hasAudioContext: !!window.injectorAudioContext,
                    audioContextState: window.injectorAudioContext ? window.injectorAudioContext.state : 'none',
                    hasMixedStream: !!window.mixedStream,
                    hasOriginalMic: !!window.originalMicStream
                })
            """)
            return status
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            return {"ready": False, "error": str(e)}

    async def get_audio_devices(self) -> list:
        """Get list of available audio devices."""
        try:
            devices = await self.page.evaluate("""
                navigator.mediaDevices.enumerateDevices().then(devices =>
                    devices.filter(d => d.kind === 'audiooutput' || d.kind === 'audioinput')
                )
            """)
            return devices
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
            return []
