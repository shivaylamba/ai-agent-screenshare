"""Annotation lifecycle management."""
import asyncio
from typing import List, Optional
from simple_logger import logger
from overlay.macos_overlay import Annotation, MacOSOverlay
from overlay.drawing_engine import DrawingEngine


class AnnotationManager:
    """Manages annotation lifecycle and display."""

    def __init__(self, overlay: Optional[MacOSOverlay] = None):
        """
        Initialize annotation manager.

        Args:
            overlay: MacOS overlay instance
        """
        self.overlay = overlay
        self.active_annotations: List[Annotation] = []
        self._cleanup_task = None

        logger.info("Annotation manager initialized")

    def set_overlay(self, overlay: MacOSOverlay):
        """
        Set the overlay instance.

        Args:
            overlay: MacOS overlay to use
        """
        self.overlay = overlay
        logger.info("Overlay set for annotation manager")

    async def add_annotation(self, annotation: Annotation):
        """
        Add an annotation to display.

        Args:
            annotation: Annotation to add
        """
        if not self.overlay:
            logger.warning("No overlay set, cannot add annotation")
            return

        self.overlay.add_annotation(annotation)
        self.active_annotations.append(annotation)

        logger.debug(f"Added {annotation.type} annotation (total: {len(self.active_annotations)})")

    async def add_annotations(self, annotations: List[Annotation]):
        """
        Add multiple annotations.

        Args:
            annotations: List of annotations to add
        """
        for annotation in annotations:
            await self.add_annotation(annotation)

    async def clear_all(self):
        """Clear all annotations."""
        if self.overlay:
            self.overlay.clear_annotations()

        self.active_annotations.clear()
        logger.info("Cleared all annotations")

    async def start_cleanup_loop(self):
        """Start background task to clean up expired annotations."""
        if self._cleanup_task:
            logger.warning("Cleanup loop already running")
            return

        logger.info("Starting annotation cleanup loop")
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Background loop to remove expired annotations."""
        try:
            while True:
                await asyncio.sleep(1)  # Check every second

                if self.overlay:
                    self.overlay.remove_expired_annotations()

        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")

    async def stop_cleanup_loop(self):
        """Stop the cleanup loop."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

            self._cleanup_task = None
            logger.info("Cleanup loop stopped")

    def get_active_count(self) -> int:
        """
        Get number of active annotations.

        Returns:
            Number of active annotations
        """
        return len(self.active_annotations)
