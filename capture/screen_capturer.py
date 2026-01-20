"""Screen capture for monitoring shared screens in Google Meet."""
import asyncio
import io
from typing import Optional, Callable
import numpy as np
import cv2
from PIL import Image
import mss
from simple_logger import logger
from config import config
from utils.performance import measure_time_async, Timer


class ScreenCapturer:
    """Captures screen content from specific regions."""

    def __init__(self, region: Optional[dict] = None):
        """
        Initialize screen capturer.

        Args:
            region: Dictionary with 'x', 'y', 'width', 'height' for capture region
                   If None, will capture entire primary screen
        """
        self.region = region
        self.sct = mss.mss()
        self.last_frame: Optional[np.ndarray] = None
        self.frame_count = 0

        logger.info(f"Screen capturer initialized with region: {region}")

    def update_region(self, region: dict):
        """
        Update the capture region (e.g., when screen share bounds change).

        Args:
            region: Dictionary with 'x', 'y', 'width', 'height'
        """
        self.region = region
        logger.info(f"Capture region updated to: {region}")

    @measure_time_async("capture_frame")
    async def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the screen region.

        Returns:
            numpy array with the captured frame in BGR format, or None if capture fails
        """
        try:
            if not self.region:
                # Capture primary monitor if no region specified
                monitor = self.sct.monitors[1]
            else:
                # Use specified region
                monitor = {
                    'top': self.region['y'],
                    'left': self.region['x'],
                    'width': self.region['width'],
                    'height': self.region['height']
                }

            # Capture the screen
            screenshot = self.sct.grab(monitor)

            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            # Convert to numpy array (RGB)
            frame = np.array(img)

            # Convert RGB to BGR (OpenCV format)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            self.last_frame = frame
            self.frame_count += 1

            return frame

        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None

    async def capture_frame_optimized(self) -> Optional[np.ndarray]:
        """
        Capture and optimize frame for AI processing.
        - Downscales if necessary
        - Maintains aspect ratio

        Returns:
            Optimized numpy array or None
        """
        frame = await self.capture_frame()

        if frame is None:
            return None

        try:
            # Get current dimensions
            height, width = frame.shape[:2]

            # Downscale if width exceeds max_width
            if width > config.screen.max_width:
                scale_factor = config.screen.max_width / width
                new_width = config.screen.max_width
                new_height = int(height * scale_factor)

                frame = cv2.resize(
                    frame,
                    (new_width, new_height),
                    interpolation=cv2.INTER_AREA
                )

                logger.debug(f"Frame downscaled from {width}x{height} to {new_width}x{new_height}")

            return frame

        except Exception as e:
            logger.error(f"Error optimizing frame: {e}")
            return frame

    def detect_significant_change(
        self,
        current_frame: np.ndarray,
        threshold: Optional[float] = None
    ) -> bool:
        """
        Detect if there's a significant change between current and last frame.

        Args:
            current_frame: Current frame to compare
            threshold: Change threshold (0-1), uses config value if None

        Returns:
            True if change exceeds threshold, False otherwise
        """
        if self.last_frame is None:
            return True

        try:
            threshold = threshold or config.screen.change_threshold

            # Ensure both frames have the same shape
            if current_frame.shape != self.last_frame.shape:
                return True

            # Calculate absolute difference
            diff = cv2.absdiff(current_frame, self.last_frame)

            # Convert to grayscale for easier processing
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            # Count pixels with significant change (threshold at 30)
            changed_pixels = np.sum(diff_gray > 30)
            total_pixels = diff_gray.size

            # Calculate percentage of changed pixels
            change_percentage = changed_pixels / total_pixels

            is_significant = change_percentage > threshold

            if is_significant:
                logger.debug(f"Significant change detected: {change_percentage:.2%}")

            return is_significant

        except Exception as e:
            logger.error(f"Error detecting change: {e}")
            return True  # Assume change on error

    def frame_to_jpeg(self, frame: np.ndarray, quality: Optional[int] = None) -> bytes:
        """
        Convert frame to JPEG bytes for transmission.

        Args:
            frame: Frame in BGR format
            quality: JPEG quality (1-100), uses config value if None

        Returns:
            JPEG image as bytes
        """
        try:
            quality = quality or config.screen.jpeg_quality

            # Encode frame to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)

            return buffer.tobytes()

        except Exception as e:
            logger.error(f"Error converting frame to JPEG: {e}")
            return b''

    def frame_to_base64(self, frame: np.ndarray) -> str:
        """
        Convert frame to base64 string for API transmission.

        Args:
            frame: Frame in BGR format

        Returns:
            Base64 encoded string
        """
        import base64

        try:
            jpeg_bytes = self.frame_to_jpeg(frame)
            return base64.b64encode(jpeg_bytes).decode('utf-8')

        except Exception as e:
            logger.error(f"Error converting frame to base64: {e}")
            return ''

    async def start_continuous_capture(
        self,
        callback: Callable[[np.ndarray], None],
        check_for_changes: bool = True
    ):
        """
        Start continuous frame capture loop.

        Args:
            callback: Async function to call with each captured frame
            check_for_changes: If True, only call callback when significant change detected
        """
        logger.info("Starting continuous screen capture")
        logger.info(f"Target FPS: {config.screen.fps}")
        logger.info(f"Change detection: {check_for_changes}")

        frame_interval = 1.0 / config.screen.fps

        try:
            while True:
                with Timer("capture_loop", log_threshold=2.0):
                    # Capture frame
                    frame = await self.capture_frame_optimized()

                    if frame is None:
                        logger.warning("Failed to capture frame")
                        await asyncio.sleep(frame_interval)
                        continue

                    # Check for significant changes if enabled
                    if check_for_changes:
                        if not self.detect_significant_change(frame):
                            await asyncio.sleep(frame_interval)
                            continue

                    # Call the callback with the frame
                    if asyncio.iscoroutinefunction(callback):
                        await callback(frame)
                    else:
                        callback(frame)

                    # Update last frame for next comparison
                    self.last_frame = frame

                    # Maintain target FPS
                    await asyncio.sleep(frame_interval)

        except asyncio.CancelledError:
            logger.info("Screen capture loop cancelled")
        except Exception as e:
            logger.error(f"Error in continuous capture: {e}")

    def save_frame(self, frame: np.ndarray, filename: str):
        """
        Save frame to disk for debugging.

        Args:
            frame: Frame to save
            filename: Output filename (e.g., 'screenshot.jpg')
        """
        try:
            cv2.imwrite(filename, frame)
            logger.debug(f"Frame saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving frame: {e}")

    def get_frame_info(self, frame: np.ndarray) -> dict:
        """
        Get information about a frame.

        Args:
            frame: Frame to analyze

        Returns:
            Dictionary with frame information
        """
        if frame is None:
            return {}

        height, width = frame.shape[:2]
        channels = frame.shape[2] if len(frame.shape) > 2 else 1

        return {
            'width': width,
            'height': height,
            'channels': channels,
            'dtype': str(frame.dtype),
            'size_bytes': frame.nbytes,
            'size_mb': frame.nbytes / (1024 * 1024)
        }

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.sct:
                self.sct.close()
                logger.info("Screen capturer cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
