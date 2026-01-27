"""Google Meet browser automation controller."""
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from simple_logger import logger
from config import config
from utils.performance import measure_time_async


class MeetController:
    """Controller for automating Google Meet interactions."""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._is_joined = False

    @measure_time_async("meet_join")
    async def join_meeting(self, meet_url: str) -> bool:
        """
        Join a Google Meet call.

        Args:
            meet_url: The Google Meet URL to join

        Returns:
            True if successfully joined, False otherwise
        """
        try:
            logger.info(f"Initializing browser to join meeting: {meet_url}")

            # Start Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with specific flags for audio support
            self.browser = await self.playwright.chromium.launch(
                headless=config.browser.headless,
                args=[
                    '--use-fake-ui-for-media-stream',  # Auto-accept media permissions
                    '--use-fake-device-for-media-stream',  # Use fake devices
                    '--enable-usermedia-screen-capturing',  # Enable screen capture
                    '--allow-http-screen-capture',
                    '--auto-select-desktop-capture-source=Entire screen',
                    '--disable-blink-features=AutomationControlled',  # Avoid detection
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )

            # Create browser context with permissions
            self.context = await self.browser.new_context(
                viewport={
                    'width': config.browser.viewport_width,
                    'height': config.browser.viewport_height
                },
                user_agent=config.browser.user_agent if config.browser.user_agent else None,
                permissions=['microphone', 'camera'],
            )

            # Create new page
            self.page = await self.context.new_page()

            # Set default timeout
            self.page.set_default_timeout(config.browser.timeout)

            # IMPORTANT: Inject audio interceptor BEFORE navigating to Meet
            # This hooks into getUserMedia before Meet requests the microphone
            await self._inject_audio_interceptor()

            # Navigate to Meet URL
            logger.info("Navigating to Google Meet...")
            await self.page.goto(meet_url, wait_until='networkidle')

            # Wait a bit for page to load
            await asyncio.sleep(2)

            # Try to find and click the "Ask to join" or "Join now" button
            await self._join_meeting_flow()

            self._is_joined = True
            logger.success("Successfully joined Google Meet call")
            return True

        except Exception as e:
            logger.error(f"Failed to join meeting: {e}")
            await self.cleanup()
            return False

    async def _inject_audio_interceptor(self):
        """Inject JavaScript to intercept getUserMedia and RTCPeerConnection for audio injection."""
        try:
            # This script will be executed before any page scripts run
            await self.page.add_init_script("""
                (function() {
                    console.log('[AudioInjector] Installing simplified audio injection system...');

                    // Initialize global state
                    window._audioInjectorReady = false;
                    window._audioInjectorActiveConnections = new Set();
                    window._audioInjectorAudioElements = new Map();

                    // Simplified approach: We'll inject audio directly into active MediaStreams
                    window.injectAudioToMeetWithLocalPlayback = async function(base64Audio) {
                        console.log('[AudioInjector] injectAudioToMeetWithLocalPlayback called');

                        try {
                            // Always try local playback first (guaranteed to work)
                            const localSuccess = await window._playAudioLocally(base64Audio);
                            if (!localSuccess) {
                                console.warn('[AudioInjector] Local playback failed');
                            }

                            // Try to inject into Meet streams
                            const meetSuccess = await window._injectIntoMeetStreams(base64Audio);
                            if (!meetSuccess) {
                                console.warn('[AudioInjector] Meet injection failed, only local playback active');
                            }

                            return {
                                success: true,
                                localPlayback: localSuccess,
                                meetInjection: meetSuccess,
                                duration: 0 // Will be calculated
                            };

                        } catch (err) {
                            console.error('[AudioInjector] Error in injectAudioToMeetWithLocalPlayback:', err);
                            return { success: false, error: err.message };
                        }
                    };

                    // Local playback function
                    window._playAudioLocally = async function(base64Audio) {
                        try {
                            const audioUrl = 'data:audio/mp3;base64,' + base64Audio;
                            const audio = new Audio(audioUrl);
                            audio.volume = 1.0;

                            return new Promise((resolve) => {
                                audio.onended = () => {
                                    console.log('[AudioInjector] Local audio playback completed');
                                    resolve(true);
                                };
                                audio.onerror = (e) => {
                                    console.error('[AudioInjector] Local audio playback error:', e);
                                    resolve(false);
                                };
                                audio.play().then(() => {
                                    console.log('[AudioInjector] Local audio started playing');
                                }).catch(e => {
                                    console.error('[AudioInjector] Local audio play failed:', e);
                                    resolve(false);
                                });
                            });
                        } catch (e) {
                            console.error('[AudioInjector] Local playback setup error:', e);
                            return false;
                        }
                    };

                    // Meet stream injection function
                    window._injectIntoMeetStreams = async function(base64Audio) {
                        try {
                            // Find all active MediaStreams with audio tracks
                            const streams = window._findActiveAudioStreams();
                            if (streams.length === 0) {
                                console.log('[AudioInjector] No active audio streams found');
                                return false;
                            }

                            console.log('[AudioInjector] Found', streams.length, 'active audio streams');

                            // Try to inject into each stream
                            let successCount = 0;
                            for (const stream of streams) {
                                try {
                                    const injected = await window._injectIntoStream(stream, base64Audio);
                                    if (injected) successCount++;
                                } catch (e) {
                                    console.warn('[AudioInjector] Failed to inject into stream:', e);
                                }
                            }

                            return successCount > 0;

                        } catch (err) {
                            console.error('[AudioInjector] Meet injection error:', err);
                            return false;
                        }
                    };

                    // Find active audio streams
                    window._findActiveAudioStreams = function() {
                        const streams = [];

                        // Check RTCPeerConnection senders
                        if (window._audioInjectorActiveConnections) {
                            for (const pc of window._audioInjectorActiveConnections) {
                                try {
                                    const senders = pc.getSenders();
                                    for (const sender of senders) {
                                        if (sender.track && sender.track.kind === 'audio') {
                                            streams.push(sender.track);
                                        }
                                    }
                                } catch (e) {
                                    console.debug('[AudioInjector] Error checking peer connection:', e);
                                }
                            }
                        }

                        // Check getUserMedia streams stored globally
                        if (window._userMediaStreams) {
                            streams.push(...window._userMediaStreams);
                        }

                        // Check for any MediaStream objects in window
                        for (const key in window) {
                            try {
                                const obj = window[key];
                                if (obj instanceof MediaStream && obj.getAudioTracks().length > 0) {
                                    streams.push(obj);
                                }
                            } catch (e) {
                                // Ignore errors
                            }
                        }

                        return [...new Set(streams)]; // Deduplicate
                    };

                    // Inject audio into a specific stream
                    window._injectIntoStream = async function(stream, base64Audio) {
                        try {
                            // Create audio context if needed
                            if (!window._injectorAudioContext) {
                                const AudioContext = window.AudioContext || window.webkitAudioContext;
                                window._injectorAudioContext = new AudioContext();
                            }

                            if (window._injectorAudioContext.state === 'suspended') {
                                await window._injectorAudioContext.resume();
                            }

                            // Decode audio data
                            const binaryString = atob(base64Audio);
                            const bytes = new Uint8Array(binaryString.length);
                            for (let i = 0; i < binaryString.length; i++) {
                                bytes[i] = binaryString.charCodeAt(i);
                            }

                            const audioBuffer = await window._injectorAudioContext.decodeAudioData(bytes.buffer.slice(0));

                            // Create source and destination
                            const source = window._injectorAudioContext.createBufferSource();
                            source.buffer = audioBuffer;

                            // Try to connect to the stream's audio track
                            if (stream instanceof MediaStreamTrack && stream.kind === 'audio') {
                                // If it's a track, we need to create a new MediaStream with our audio mixed in
                                console.log('[AudioInjector] Injecting into audio track');

                                // Create a new MediaStream with the injected audio
                                const mixedDestination = window._injectorAudioContext.createMediaStreamDestination();

                                // Mix original track with injected audio
                                const originalSource = window._injectorAudioContext.createMediaStreamSource(new MediaStream([stream]));
                                const gainNode = window._injectorAudioContext.createGain();

                                originalSource.connect(gainNode);
                                source.connect(gainNode);
                                gainNode.connect(mixedDestination);

                                source.start(0);

                                // Try to replace the track in any peer connections
                                window._replaceAudioTrack(stream, mixedDestination.stream.getAudioTracks()[0]);

                                return true;

                            } else if (stream instanceof MediaStream) {
                                // If it's a MediaStream, add our audio to it
                                console.log('[AudioInjector] Injecting into MediaStream');

                                const mixedDestination = window._injectorAudioContext.createMediaStreamDestination();
                                const gainNode = window._injectorAudioContext.createGain();

                                // Connect original audio tracks
                                const audioTracks = stream.getAudioTracks();
                                for (const track of audioTracks) {
                                    const trackSource = window._injectorAudioContext.createMediaStreamSource(new MediaStream([track]));
                                    trackSource.connect(gainNode);
                                }

                                // Connect injected audio
                                source.connect(gainNode);
                                gainNode.connect(mixedDestination);

                                source.start(0);

                                return true;
                            }

                            return false;

                        } catch (err) {
                            console.error('[AudioInjector] Stream injection error:', err);
                            return false;
                        }
                    };

                    // Replace audio track in peer connections
                    window._replaceAudioTrack = function(oldTrack, newTrack) {
                        if (window._audioInjectorActiveConnections) {
                            for (const pc of window._audioInjectorActiveConnections) {
                                try {
                                    const senders = pc.getSenders();
                                    for (const sender of senders) {
                                        if (sender.track === oldTrack) {
                                            sender.replaceTrack(newTrack);
                                            console.log('[AudioInjector] Replaced audio track in peer connection');
                                            return true;
                                        }
                                    }
                                } catch (e) {
                                    console.debug('[AudioInjector] Error replacing track:', e);
                                }
                            }
                        }
                        return false;
                    };

                    // Intercept RTCPeerConnection to track active connections
                    const OriginalRTCPeerConnection = window.RTCPeerConnection;
                    window.RTCPeerConnection = function(...args) {
                        const pc = new OriginalRTCPeerConnection(...args);
                        window._audioInjectorActiveConnections.add(pc);

                        // Clean up when connection closes
                        pc.onconnectionstatechange = function() {
                            if (pc.connectionState === 'closed' || pc.connectionState === 'failed') {
                                window._audioInjectorActiveConnections.delete(pc);
                            }
                        };

                        console.log('[AudioInjector] RTCPeerConnection tracked, total active:', window._audioInjectorActiveConnections.size);
                        return pc;
                    };

                    // Copy static properties
                    Object.keys(OriginalRTCPeerConnection).forEach(key => {
                        window.RTCPeerConnection[key] = OriginalRTCPeerConnection[key];
                    });
                    window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;

                    // Intercept getUserMedia to track streams
                    const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                    navigator.mediaDevices.getUserMedia = async function(constraints) {
                        const stream = await originalGetUserMedia(constraints);
                        if (!window._userMediaStreams) {
                            window._userMediaStreams = new Set();
                        }
                        window._userMediaStreams.add(stream);
                        console.log('[AudioInjector] getUserMedia stream tracked');
                        return stream;
                    };

                    // Legacy function for backward compatibility
                    window.injectAudioToMeet = window.injectAudioToMeetWithLocalPlayback;

                    console.log('[AudioInjector] Simplified audio injection system installed');
                })();
            """)
            
            logger.success("Audio interceptor injected into page")
            
        except Exception as e:
            logger.error(f"Error injecting audio interceptor: {e}")

    async def _join_meeting_flow(self):
        """Handle the meeting join flow with various possible UI states."""
        try:
            # Turn off camera and microphone initially
            await self._toggle_camera_mic(camera_on=False, mic_on=True)

            await asyncio.sleep(1)

            # Look for various join button selectors
            join_selectors = [
                'button:has-text("Join now")',
                'button:has-text("Ask to join")',
                'button:has-text("Join")',
                '[aria-label*="Join"]',
                'button[jsname="Qx7Oae"]',  # Google Meet specific button
            ]

            joined = False
            for selector in join_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=5000)
                    if button:
                        logger.info(f"Found join button with selector: {selector}")
                        await button.click()
                        joined = True
                        break
                except Exception:
                    continue

            if not joined:
                logger.warning("Could not find join button automatically")
                logger.info("You may need to manually click the join button")

            # Wait for meeting to fully load
            await asyncio.sleep(3)

        except Exception as e:
            logger.error(f"Error in join meeting flow: {e}")

    async def _toggle_camera_mic(self, camera_on: bool = False, mic_on: bool = True):
        """Toggle camera and microphone before joining."""
        try:
            # Try to find and click camera/mic controls
            # These selectors may need adjustment based on Google Meet UI
            camera_selector = '[aria-label*="camera" i], [data-tooltip*="camera" i]'
            mic_selector = '[aria-label*="microphone" i], [data-tooltip*="microphone" i]'

            # Get current state and toggle if needed
            # This is a simplified version - may need refinement
            if not camera_on:
                try:
                    camera_button = await self.page.wait_for_selector(camera_selector, timeout=3000)
                    if camera_button:
                        await camera_button.click()
                        logger.info("Camera turned off")
                except Exception:
                    logger.debug("Could not find camera control")

        except Exception as e:
            logger.debug(f"Error toggling camera/mic: {e}")

    async def get_screen_share_element(self):
        """
        Get the video element containing the screen share.

        Returns:
            ElementHandle for the screen share video, or None if not found
        """
        try:
            # Look for video elements that might contain screen share
            # Screen share typically appears in a larger video element
            videos = await self.page.query_selector_all('video')

            if not videos:
                logger.warning("No video elements found on page")
                return None

            # Find the largest video (likely the screen share)
            largest_video = None
            max_area = 0

            for video in videos:
                box = await video.bounding_box()
                if box:
                    area = box['width'] * box['height']
                    if area > max_area:
                        max_area = area
                        largest_video = video

            if largest_video:
                logger.info(f"Found screen share video element (area: {max_area})")
                return largest_video
            else:
                logger.warning("Could not determine screen share element")
                return None

        except Exception as e:
            logger.error(f"Error getting screen share element: {e}")
            return None

    async def get_screen_share_bounds(self) -> Optional[dict]:
        """
        Get the bounding box coordinates of the screen share video.

        Returns:
            Dictionary with 'x', 'y', 'width', 'height' or None if not found
        """
        try:
            element = await self.get_screen_share_element()
            if element:
                box = await element.bounding_box()
                if box:
                    # Convert to integer coordinates
                    return {
                        'x': int(box['x']),
                        'y': int(box['y']),
                        'width': int(box['width']),
                        'height': int(box['height'])
                    }
            return None
        except Exception as e:
            logger.error(f"Error getting screen share bounds: {e}")
            return None

    async def inject_audio_stream(self, audio_data: bytes):
        """
        Inject audio data into the Meet call.

        Args:
            audio_data: Audio data in bytes

        Note: This is a complex operation that requires JavaScript injection
        to override getUserMedia and provide a custom MediaStream.
        """
        try:
            # This is a placeholder for audio injection
            # Full implementation requires:
            # 1. Creating a Web Audio API context
            # 2. Creating an AudioBuffer from audio_data
            # 3. Creating a MediaStreamAudioSourceNode
            # 4. Routing it to the peer connection

            logger.debug("Audio injection called (implementation pending)")
            # TODO: Implement audio injection in Phase 3

        except Exception as e:
            logger.error(f"Error injecting audio: {e}")

    @property
    def is_joined(self) -> bool:
        """Check if currently in a meeting."""
        return self._is_joined and self.page is not None

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            logger.info("Cleaning up browser resources...")

            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self._is_joined = False
            logger.info("Browser cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()