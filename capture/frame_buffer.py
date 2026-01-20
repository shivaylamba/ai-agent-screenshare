"""Frame buffer for managing captured screen frames."""
import asyncio
from collections import deque
from typing import Optional, Deque
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from simple_logger import logger


@dataclass
class Frame:
    """Represents a captured frame with metadata."""
    data: np.ndarray
    timestamp: datetime
    frame_number: int
    changed: bool = True
    processed: bool = False


class FrameBuffer:
    """Buffer for managing captured frames with history."""

    def __init__(self, max_size: int = 10):
        """
        Initialize frame buffer.

        Args:
            max_size: Maximum number of frames to keep in buffer
        """
        self.max_size = max_size
        self.frames: Deque[Frame] = deque(maxlen=max_size)
        self.current_frame_number = 0
        self._lock = asyncio.Lock()

        logger.info(f"Frame buffer initialized with max size: {max_size}")

    async def add_frame(
        self,
        frame_data: np.ndarray,
        changed: bool = True
    ) -> Frame:
        """
        Add a new frame to the buffer.

        Args:
            frame_data: Frame data as numpy array
            changed: Whether this frame represents a significant change

        Returns:
            Frame object that was added
        """
        async with self._lock:
            frame = Frame(
                data=frame_data,
                timestamp=datetime.now(),
                frame_number=self.current_frame_number,
                changed=changed,
                processed=False
            )

            self.frames.append(frame)
            self.current_frame_number += 1

            return frame

    async def get_latest_frame(self) -> Optional[Frame]:
        """
        Get the most recent frame.

        Returns:
            Latest Frame object or None if buffer is empty
        """
        async with self._lock:
            if not self.frames:
                return None
            return self.frames[-1]

    async def get_latest_unprocessed_frame(self) -> Optional[Frame]:
        """
        Get the most recent frame that hasn't been processed.

        Returns:
            Latest unprocessed Frame object or None if all processed
        """
        async with self._lock:
            for frame in reversed(self.frames):
                if not frame.processed:
                    return frame
            return None

    async def mark_frame_processed(self, frame_number: int):
        """
        Mark a frame as processed.

        Args:
            frame_number: Frame number to mark as processed
        """
        async with self._lock:
            for frame in self.frames:
                if frame.frame_number == frame_number:
                    frame.processed = True
                    logger.debug(f"Frame {frame_number} marked as processed")
                    break

    async def get_frame_by_number(self, frame_number: int) -> Optional[Frame]:
        """
        Get a specific frame by its number.

        Args:
            frame_number: Frame number to retrieve

        Returns:
            Frame object or None if not found
        """
        async with self._lock:
            for frame in self.frames:
                if frame.frame_number == frame_number:
                    return frame
            return None

    async def get_recent_frames(self, count: int = 5) -> list[Frame]:
        """
        Get the N most recent frames.

        Args:
            count: Number of frames to retrieve

        Returns:
            List of Frame objects (most recent last)
        """
        async with self._lock:
            return list(self.frames)[-count:]

    async def get_changed_frames(self) -> list[Frame]:
        """
        Get all frames marked as changed.

        Returns:
            List of Frame objects with significant changes
        """
        async with self._lock:
            return [frame for frame in self.frames if frame.changed]

    async def clear_buffer(self):
        """Clear all frames from the buffer."""
        async with self._lock:
            self.frames.clear()
            logger.info("Frame buffer cleared")

    async def get_buffer_stats(self) -> dict:
        """
        Get statistics about the buffer.

        Returns:
            Dictionary with buffer statistics
        """
        async with self._lock:
            total_frames = len(self.frames)
            changed_frames = sum(1 for f in self.frames if f.changed)
            processed_frames = sum(1 for f in self.frames if f.processed)
            unprocessed_frames = total_frames - processed_frames

            return {
                'total_frames': total_frames,
                'changed_frames': changed_frames,
                'processed_frames': processed_frames,
                'unprocessed_frames': unprocessed_frames,
                'buffer_utilization': f"{(total_frames / self.max_size) * 100:.1f}%",
                'current_frame_number': self.current_frame_number
            }

    def get_size(self) -> int:
        """
        Get current number of frames in buffer.

        Returns:
            Number of frames
        """
        return len(self.frames)

    def is_empty(self) -> bool:
        """
        Check if buffer is empty.

        Returns:
            True if empty, False otherwise
        """
        return len(self.frames) == 0

    def is_full(self) -> bool:
        """
        Check if buffer is at max capacity.

        Returns:
            True if full, False otherwise
        """
        return len(self.frames) >= self.max_size


class FrameRateController:
    """Controls frame processing rate to avoid overwhelming downstream systems."""

    def __init__(self, target_fps: float = 2.0):
        """
        Initialize frame rate controller.

        Args:
            target_fps: Target frames per second for processing
        """
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.last_process_time = 0.0
        self._lock = asyncio.Lock()

        logger.info(f"Frame rate controller initialized: {target_fps} FPS")

    async def should_process_frame(self) -> bool:
        """
        Check if enough time has passed to process another frame.

        Returns:
            True if frame should be processed, False to skip
        """
        async with self._lock:
            import time
            current_time = time.time()

            if current_time - self.last_process_time >= self.frame_interval:
                self.last_process_time = current_time
                return True

            return False

    async def wait_for_next_frame(self):
        """Wait until it's time to process the next frame."""
        async with self._lock:
            import time
            current_time = time.time()
            elapsed = current_time - self.last_process_time

            if elapsed < self.frame_interval:
                wait_time = self.frame_interval - elapsed
                await asyncio.sleep(wait_time)

            self.last_process_time = time.time()

    def update_target_fps(self, new_fps: float):
        """
        Update the target FPS.

        Args:
            new_fps: New target frames per second
        """
        self.target_fps = new_fps
        self.frame_interval = 1.0 / new_fps
        logger.info(f"Frame rate updated to {new_fps} FPS")


class FrameQualityAnalyzer:
    """Analyzes frame quality to determine if frame is suitable for processing."""

    @staticmethod
    def is_frame_valid(frame: np.ndarray) -> bool:
        """
        Check if frame is valid for processing.

        Args:
            frame: Frame data to validate

        Returns:
            True if frame is valid, False otherwise
        """
        if frame is None:
            return False

        if frame.size == 0:
            return False

        # Check if frame has reasonable dimensions
        if len(frame.shape) < 2:
            return False

        height, width = frame.shape[:2]
        if width < 100 or height < 100:
            logger.warning(f"Frame too small: {width}x{height}")
            return False

        return True

    @staticmethod
    def calculate_frame_brightness(frame: np.ndarray) -> float:
        """
        Calculate average brightness of frame.

        Args:
            frame: Frame data in BGR format

        Returns:
            Average brightness (0-255)
        """
        import cv2

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))

    @staticmethod
    def is_frame_too_dark(frame: np.ndarray, threshold: float = 20.0) -> bool:
        """
        Check if frame is too dark to process.

        Args:
            frame: Frame data
            threshold: Darkness threshold (0-255)

        Returns:
            True if frame is too dark
        """
        brightness = FrameQualityAnalyzer.calculate_frame_brightness(frame)
        return brightness < threshold

    @staticmethod
    def is_frame_blank(frame: np.ndarray, threshold: float = 10.0) -> bool:
        """
        Check if frame is mostly blank/uniform.

        Args:
            frame: Frame data
            threshold: Standard deviation threshold

        Returns:
            True if frame appears blank
        """
        import cv2

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate standard deviation
        std_dev = float(np.std(gray))

        return std_dev < threshold
