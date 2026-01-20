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
