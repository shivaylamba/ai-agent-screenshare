"""Drawing utilities for overlay annotations."""
from typing import Tuple
from simple_logger import logger
from overlay.macos_overlay import Annotation
from config import config


class DrawingEngine:
    """Engine for creating drawable annotations."""

    @staticmethod
    def create_arrow(
        start: Tuple[int, int],
        end: Tuple[int, int],
        color: str = None,
        duration: float = None
    ) -> Annotation:
        """
        Create an arrow annotation.

        Args:
            start: Start point (x, y)
            end: End point (x, y)
            color: Arrow color (hex)
            duration: Display duration in seconds

        Returns:
            Annotation object
        """
        position = (*start, *end)
        return Annotation(
            annotation_type='arrow',
            position=position,
            color=color or config.overlay.arrow_color,
            duration=duration
        )

    @staticmethod
    def create_highlight(
        x: int,
        y: int,
        width: int,
        height: int,
        color: str = None,
        duration: float = None
    ) -> Annotation:
        """
        Create a highlight annotation.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Width
            height: Height
            color: Highlight color (hex)
            duration: Display duration

        Returns:
            Annotation object
        """
        return Annotation(
            annotation_type='highlight',
            position=(x, y, width, height),
            color=color or config.overlay.highlight_color,
            duration=duration
        )

    @staticmethod
    def create_box(
        x: int,
        y: int,
        width: int,
        height: int,
        color: str = None,
        duration: float = None
    ) -> Annotation:
        """
        Create a bounding box annotation.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Width
            height: Height
            color: Box color (hex)
            duration: Display duration

        Returns:
            Annotation object
        """
        return Annotation(
            annotation_type='box',
            position=(x, y, width, height),
            color=color or config.overlay.arrow_color,
            duration=duration
        )

    @staticmethod
    def create_text(
        x: int,
        y: int,
        text: str,
        color: str = None,
        duration: float = None
    ) -> Annotation:
        """
        Create a text annotation.

        Args:
            x: X coordinate
            y: Y coordinate
            text: Text to display
            color: Text color (hex)
            duration: Display duration

        Returns:
            Annotation object
        """
        return Annotation(
            annotation_type='text',
            position=(x, y),
            color=color or config.overlay.text_color,
            text=text,
            duration=duration
        )

    @staticmethod
    def create_pointer(
        x: int,
        y: int,
        offset: int = 50,
        color: str = None,
        text: str = None,
        duration: float = None
    ) -> list[Annotation]:
        """
        Create a pointer (arrow + optional text).

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            offset: Offset for arrow start
            color: Color (hex)
            text: Optional text label
            duration: Display duration

        Returns:
            List of annotations
        """
        annotations = []

        # Create arrow pointing to target
        start_x = x - offset
        start_y = y - offset
        arrow = DrawingEngine.create_arrow(
            start=(start_x, start_y),
            end=(x, y),
            color=color,
            duration=duration
        )
        annotations.append(arrow)

        # Add text if provided
        if text:
            text_ann = DrawingEngine.create_text(
                x=start_x - 20,
                y=start_y - 20,
                text=text,
                color=color,
                duration=duration
            )
            annotations.append(text_ann)

        return annotations
