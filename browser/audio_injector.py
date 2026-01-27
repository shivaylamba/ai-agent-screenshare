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

            logger.info(f"Injecting audio ({len(audio_data)} bytes)")

            # Use the simplified injection function that handles both local and Meet playback
            result = await self.page.evaluate("""
                async function(base64Audio) {
                    if (typeof window.injectAudioToMeetWithLocalPlayback === 'function') {
                        const result = await window.injectAudioToMeetWithLocalPlayback(base64Audio);
                        console.log('[AudioInjector] Injection result:', result);
                        return result;
                    } else {
                        console.error('[AudioInjector] injectAudioToMeetWithLocalPlayback function not found');
                        return { success: false, error: 'Function not initialized' };
                    }
                }
            """, audio_base64)

            if result and result.get('success'):
                local_ok = result.get('localPlayback', False)
                meet_ok = result.get('meetInjection', False)
                logger.success(f"Audio injection completed - Local: {local_ok}, Meet: {meet_ok}")

                if not meet_ok:
                    logger.warning("Audio injected locally but NOT into Meet call - check Meet microphone permissions")
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                logger.error(f"Audio injection failed: {error}")

                # Fallback to local playback
                logger.info("Attempting fallback local playback...")
                await self._play_audio_locally(audio_base64)

        except Exception as e:
            logger.error(f"Error injecting audio: {e}")
            # Try fallback local playback
            try:
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                await self._play_audio_locally(audio_base64)
            except Exception as fallback_e:
                logger.error(f"Fallback local playback also failed: {fallback_e}")

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
                () => {
                    const status = {
                        hasInjectionFunction: typeof window.injectAudioToMeetWithLocalPlayback === 'function',
                        activeConnections: window._audioInjectorActiveConnections ? window._audioInjectorActiveConnections.size : 0,
                        userMediaStreams: window._userMediaStreams ? window._userMediaStreams.size : 0,
                        audioContext: !!window._injectorAudioContext,
                        audioContextState: window._injectorAudioContext ? window._injectorAudioContext.state : 'none'
                    };

                    // Check for active audio tracks
                    let audioTracks = 0;
                    if (window._audioInjectorActiveConnections) {
                        for (const pc of window._audioInjectorActiveConnections) {
                            try {
                                const senders = pc.getSenders();
                                for (const sender of senders) {
                                    if (sender.track && sender.track.kind === 'audio') {
                                        audioTracks++;
                                    }
                                }
                            } catch (e) {}
                        }
                    }
                    status.audioTracks = audioTracks;

                    // Check for any MediaStreams in window
                    let mediaStreams = 0;
                    for (const key in window) {
                        try {
                            const obj = window[key];
                            if (obj instanceof MediaStream && obj.getAudioTracks().length > 0) {
                                mediaStreams++;
                            }
                        } catch (e) {}
                    }
                    status.mediaStreams = mediaStreams;

                    return status;
                }
            """)

            logger.info(f"Audio injector status: {status}")

            # Provide helpful advice based on status
            if not status.get('hasInjectionFunction'):
                logger.warning("Audio injection JavaScript not loaded properly")
            if status.get('activeConnections', 0) == 0:
                logger.warning("No active WebRTC connections found - has Meet started the call?")
            if status.get('audioTracks', 0) == 0:
                logger.warning("No audio tracks found - microphone may not be active in Meet")

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

    async def test_audio_injection(self):
        """Test audio injection with a simple beep sound."""
        try:
            logger.info("Testing audio injection with beep sound...")

            # Create a simple beep sound (1kHz tone for 0.5 seconds)
            import wave
            import struct
            import io

            # Generate beep audio
            sample_rate = 44100
            duration = 0.5
            frequency = 1000
            num_samples = int(sample_rate * duration)

            # Generate sine wave
            audio_data = b''
            for i in range(num_samples):
                sample = int(32767 * 0.5 * (1 + (i / num_samples) ** 2) * (i / num_samples) * 0.3)  # Simple envelope
                audio_data += struct.pack('<h', sample)

            # Create WAV file
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)

            wav_data = wav_buffer.getvalue()

            # Test injection
            await self.inject_audio(wav_data)
            logger.success("Audio injection test completed")

        except Exception as e:
            logger.error(f"Error testing audio injection: {e}")
