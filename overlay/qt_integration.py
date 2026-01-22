"""Qt overlay integration with asyncio."""
import asyncio
import threading
from typing import Optional
from PyQt6.QtWidgets import QApplication
from simple_logger import logger
from overlay.macos_overlay import MacOSOverlay, create_overlay_app


class QtOverlayIntegration:
    """Integrates Qt overlay with asyncio event loop."""

    def __init__(self):
        """Initialize Qt overlay integration."""
        self.app: Optional[QApplication] = None
        self.overlay: Optional[MacOSOverlay] = None
        self.qt_thread: Optional[threading.Thread] = None
        self._running = False

        logger.info("Qt overlay integration initialized")

    def start(self):
        """Start Qt application in separate thread."""
        if self._running:
            logger.warning("Qt overlay already running")
            return

        self._running = True
        self.qt_thread = threading.Thread(target=self._run_qt_loop, daemon=True)
        self.qt_thread.start()

        # Wait a bit for Qt to initialize
        import time
        time.sleep(0.5)

        logger.success("Qt overlay started")

    def _run_qt_loop(self):
        """Run Qt event loop in separate thread."""
        try:
            self.app, self.overlay = create_overlay_app()
            self.overlay.show_overlay()

            # Run Qt event loop
            self.app.exec()

        except Exception as e:
            logger.error(f"Error in Qt event loop: {e}")

    def get_overlay(self) -> Optional[MacOSOverlay]:
        """
        Get the overlay instance.

        Returns:
            MacOSOverlay instance or None
        """
        return self.overlay

    def stop(self):
        """Stop Qt application."""
        if not self._running:
            return

        self._running = False

        if self.app:
            # Quit Qt application
            self.app.quit()

        if self.qt_thread:
            self.qt_thread.join(timeout=2.0)

        logger.info("Qt overlay stopped")

    def is_running(self) -> bool:
        """
        Check if overlay is running.

        Returns:
            True if running
        """
        return self._running

