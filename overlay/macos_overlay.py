"""Transparent overlay window for macOS."""
import sys
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath
from simple_logger import logger
from config import config


class Annotation:
    """Represents a visual annotation."""

    def __init__(
        self,
        annotation_type: str,
        position: Tuple,
        color: str = None,
        text: Optional[str] = None,
        duration: float = None
    ):
        """
        Initialize annotation.

        Args:
            annotation_type: Type of annotation ('arrow', 'highlight', 'box', 'text')
            position: Position tuple (varies by type)
            color: Color as hex string
            text: Text content (for text annotations)
            duration: How long to show (seconds)
        """
        self.type = annotation_type
        self.position = position
        self.color = color or config.overlay.arrow_color
        self.text = text
        self.duration = duration or config.overlay.default_duration
        self.created_at = None  # Will be set when added to overlay


class MacOSOverlay(QWidget):
    """Transparent overlay window for macOS."""

    def __init__(self):
        """Initialize macOS overlay."""
        super().__init__()

        self.annotations: List[Annotation] = []
        self._app = None

        self._init_window()
        self._init_timer()

        logger.info("macOS overlay initialized")

    def _init_window(self):
        """Initialize the overlay window."""
        # Set window flags for transparency and always on top
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # Click-through
        )

        # Set window to be transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Make fullscreen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        logger.info(f"Overlay window initialized: {screen.width()}x{screen.height()}")

    def _init_timer(self):
        """Initialize refresh timer."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)

        # Calculate interval from FPS
        interval = int(1000 / config.overlay.refresh_rate)
        self.timer.start(interval)

        logger.info(f"Overlay refresh timer started: {config.overlay.refresh_rate} FPS")

    def paintEvent(self, event):
        """Paint the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw all annotations
        for annotation in self.annotations:
            self._draw_annotation(painter, annotation)

    def _draw_annotation(self, painter: QPainter, annotation: Annotation):
        """Draw a single annotation."""
        try:
            color = QColor(annotation.color)
            color.setAlpha(int(config.overlay.opacity * 255))

            if annotation.type == 'arrow':
                self._draw_arrow(painter, annotation, color)
            elif annotation.type == 'highlight':
                self._draw_highlight(painter, annotation, color)
            elif annotation.type == 'box':
                self._draw_box(painter, annotation, color)
            elif annotation.type == 'text':
                self._draw_text(painter, annotation, color)

        except Exception as e:
            logger.error(f"Error drawing annotation: {e}")

    def _draw_arrow(self, painter: QPainter, annotation: Annotation, color: QColor):
        """Draw an arrow."""
        if len(annotation.position) != 4:
            return

        x1, y1, x2, y2 = annotation.position

        pen = QPen(color, config.overlay.arrow_thickness)
        painter.setPen(pen)

        # Draw line
        painter.drawLine(QPoint(x1, y1), QPoint(x2, y2))

        # Draw arrowhead
        self._draw_arrowhead(painter, x1, y1, x2, y2, color)

    def _draw_arrowhead(self, painter, x1, y1, x2, y2, color):
        """Draw arrowhead at the end of an arrow."""
        import math

        # Calculate angle
        angle = math.atan2(y2 - y1, x2 - x1)

        # Arrowhead size
        arrow_size = 15

        # Calculate arrowhead points
        angle1 = angle + math.pi * 3 / 4
        angle2 = angle - math.pi * 3 / 4

        p1_x = x2 - arrow_size * math.cos(angle1)
        p1_y = y2 - arrow_size * math.sin(angle1)
        p2_x = x2 - arrow_size * math.cos(angle2)
        p2_y = y2 - arrow_size * math.sin(angle2)

        # Draw arrowhead
        path = QPainterPath()
        path.moveTo(x2, y2)
        path.lineTo(p1_x, p1_y)
        path.lineTo(p2_x, p2_y)
        path.closeSubpath()

        painter.fillPath(path, color)

    def _draw_highlight(self, painter: QPainter, annotation: Annotation, color: QColor):
        """Draw a highlight rectangle."""
        if len(annotation.position) != 4:
            return

        x, y, width, height = annotation.position

        color.setAlpha(int(config.overlay.opacity * 100))  # More transparent for highlights
        painter.fillRect(x, y, width, height, color)

    def _draw_box(self, painter: QPainter, annotation: Annotation, color: QColor):
        """Draw a bounding box."""
        if len(annotation.position) != 4:
            return

        x, y, width, height = annotation.position

        pen = QPen(color, config.overlay.arrow_thickness)
        painter.setPen(pen)
        painter.drawRect(x, y, width, height)

    def _draw_text(self, painter: QPainter, annotation: Annotation, color: QColor):
        """Draw text."""
        if len(annotation.position) != 2 or not annotation.text:
            return

        x, y = annotation.position

        # Set font
        font = QFont()
        font.setPointSize(config.overlay.text_size)
        font.setBold(True)
        painter.setFont(font)

        # Set color
        painter.setPen(color)

        # Draw text with background
        text_color = QColor(config.overlay.text_color)
        painter.setPen(text_color)

        # Draw text background
        metrics = painter.fontMetrics()
        text_rect = metrics.boundingRect(annotation.text)
        text_rect.moveCenter(QPoint(x, y))

        bg_color = QColor("#000000")
        bg_color.setAlpha(128)
        painter.fillRect(text_rect.adjusted(-5, -5, 5, 5), bg_color)

        # Draw text
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, annotation.text)

    def add_annotation(self, annotation: Annotation):
        """
        Add an annotation to the overlay.

        Args:
            annotation: Annotation to add
        """
        import time
        annotation.created_at = time.time()
        self.annotations.append(annotation)
        logger.debug(f"Added {annotation.type} annotation")

    def clear_annotations(self):
        """Clear all annotations."""
        self.annotations.clear()
        logger.debug("Cleared all annotations")

    def remove_expired_annotations(self):
        """Remove annotations that have expired."""
        import time
        current_time = time.time()

        initial_count = len(self.annotations)
        self.annotations = [
            ann for ann in self.annotations
            if current_time - ann.created_at < ann.duration
        ]

        removed = initial_count - len(self.annotations)
        if removed > 0:
            logger.debug(f"Removed {removed} expired annotations")

    def show_overlay(self):
        """Show the overlay window."""
        self.show()
        logger.info("Overlay shown")

    def hide_overlay(self):
        """Hide the overlay window."""
        self.hide()
        logger.info("Overlay hidden")


def create_overlay_app() -> Tuple[QApplication, MacOSOverlay]:
    """
    Create QApplication and overlay window.

    Returns:
        Tuple of (QApplication, MacOSOverlay)
    """
    app = QApplication(sys.argv)
    overlay = MacOSOverlay()
    return app, overlay
