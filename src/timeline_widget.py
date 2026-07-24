"""
Timeline widget: scrub bar and draggable/resizable annotation bars for the
Snappix video editor.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.annotation_items import list_to_color
from src.video_models import VideoAnnotationModel

LABEL_WIDTH = 160
RULER_HEIGHT = 28
ROW_HEIGHT = 30
ROW_SPACING = 4
EDGE_HIT_PX = 6
MIN_ANNOTATION_DURATION_MS = 100

DRAG_MODE_PLAYHEAD = "playhead"
DRAG_MODE_MOVE = "move"
DRAG_MODE_START = "start"
DRAG_MODE_END = "end"


class TimelineWidget(QWidget):
    """
    Displays a scrub ruler and one row per video annotation, each shown as a
    draggable/resizable time-range bar.
    """

    seek_requested = Signal(int)
    annotation_time_changed = Signal(str, int, int)
    annotation_selected = Signal(str)

    def __init__(self) -> None:
        """
        Initializes the timeline with an empty annotation list.
        """

        super().__init__()
        self.setMinimumHeight(RULER_HEIGHT + ROW_HEIGHT + ROW_SPACING)
        self.setMouseTracking(True)
        self._duration_ms = 0
        self._position_ms = 0
        self._annotations: list[VideoAnnotationModel] = []
        self._selected_id = ""
        self._drag_mode = ""
        self._drag_annotation: VideoAnnotationModel | None = None
        self._drag_anchor_ms = 0
        self._drag_orig_start = 0
        self._drag_orig_end = 0

    def set_duration(self, duration_ms: int) -> None:
        """
        Sets the total timeline duration.

        Args:
            duration_ms: Video duration in milliseconds.

        Returns:
            None
        """

        self._duration_ms = max(1, duration_ms)
        self._resize_for_row_count()
        self.update()

    def set_position(self, position_ms: int) -> None:
        """
        Updates the playhead position and repaints.

        Args:
            position_ms: Current playhead position in milliseconds.

        Returns:
            None
        """

        self._position_ms = position_ms
        self.update()

    def set_annotations(self, annotations: list[VideoAnnotationModel]) -> None:
        """
        Replaces the annotation list shown as timeline rows.

        Args:
            annotations: Complete annotation list for the loaded video.

        Returns:
            None
        """

        self._annotations = annotations
        self._resize_for_row_count()
        self.update()

    def refresh(self) -> None:
        """
        Resizes rows and repaints after annotations changed in place elsewhere.

        Returns:
            None
        """

        self._resize_for_row_count()
        self.update()

    def selected_annotation_id(self) -> str:
        """
        Returns the currently selected annotation id.

        Returns:
            str: Selected annotation id, or empty string when none selected.
        """

        return self._selected_id

    def _resize_for_row_count(self) -> None:
        """
        Grows the widget's minimum height to fit all annotation rows.

        Returns:
            None
        """

        row_count = len(self._annotations)
        height = RULER_HEIGHT + row_count * (ROW_HEIGHT + ROW_SPACING) + ROW_SPACING
        self.setMinimumHeight(max(RULER_HEIGHT + ROW_HEIGHT + ROW_SPACING, height))

    def _track_area_rect(self) -> QRect:
        """
        Returns the rectangle available for the ms-to-pixel track area.

        Returns:
            QRect: Track area, excluding the left label column.
        """

        return QRect(LABEL_WIDTH, 0, max(1, self.width() - LABEL_WIDTH), self.height())

    def _ms_to_x(self, ms: int) -> int:
        """
        Converts a timeline position to a pixel x coordinate.

        Args:
            ms: Position in milliseconds.

        Returns:
            int: Pixel x coordinate within the track area.
        """

        track = self._track_area_rect()
        ratio = max(0.0, min(1.0, ms / self._duration_ms))
        return track.x() + int(ratio * track.width())

    def _x_to_ms(self, x: int) -> int:
        """
        Converts a pixel x coordinate to a clamped timeline position.

        Args:
            x: Pixel x coordinate.

        Returns:
            int: Clamped position in milliseconds within [0, duration].
        """

        track = self._track_area_rect()
        ratio = (x - track.x()) / max(1, track.width())
        ratio = max(0.0, min(1.0, ratio))
        return int(ratio * self._duration_ms)

    def _row_rect(self, index: int) -> QRect:
        """
        Returns the full-width rectangle for one annotation row.

        Args:
            index: Row index within the annotation list.

        Returns:
            QRect: Row rectangle including the label column.
        """

        top = RULER_HEIGHT + index * (ROW_HEIGHT + ROW_SPACING) + ROW_SPACING
        return QRect(0, top, self.width(), ROW_HEIGHT)

    def _bar_rect(self, index: int, annotation: VideoAnnotationModel) -> QRect:
        """
        Returns the draggable bar rectangle for one annotation row.

        Args:
            index: Row index within the annotation list.
            annotation: Annotation model for this row.

        Returns:
            QRect: Bar rectangle in widget coordinates.
        """

        row = self._row_rect(index)
        start_x = self._ms_to_x(annotation.start_ms)
        end_x = self._ms_to_x(annotation.end_ms)
        return QRect(start_x, row.y(), max(4, end_x - start_x), row.height())

    def paintEvent(self, _event) -> None:
        """
        Paints the ruler, playhead, and all annotation bars.

        Returns:
            None
        """

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track = self._track_area_rect()
        painter.fillRect(0, 0, self.width(), RULER_HEIGHT, QColor(40, 40, 40))
        painter.setPen(QPen(QColor(150, 150, 150)))
        tick_count = 10
        for tick in range(tick_count + 1):
            ms = int(self._duration_ms * tick / tick_count)
            x = self._ms_to_x(ms)
            painter.drawLine(x, RULER_HEIGHT - 6, x, RULER_HEIGHT)
            painter.drawText(x + 2, RULER_HEIGHT - 8, f"{ms / 1000:.1f}s")

        for index, annotation in enumerate(self._annotations):
            row = self._row_rect(index)
            painter.fillRect(
                QRect(0, row.y(), LABEL_WIDTH, row.height()), QColor(45, 45, 45)
            )
            label = f"{annotation.annotation_type}"
            if annotation.text:
                label += f": {annotation.text[:16]}"
            painter.setPen(QPen(QColor(220, 220, 220)))
            painter.drawText(
                QRect(6, row.y(), LABEL_WIDTH - 10, row.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label,
            )

            bar = self._bar_rect(index, annotation)
            color = list_to_color(annotation.stroke_rgba)
            fill_color = QColor(color)
            fill_color.setAlpha(140)
            painter.fillRect(bar, fill_color)
            border_color = QColor(255, 255, 255) if annotation.annotation_id == self._selected_id else color
            painter.setPen(QPen(border_color, 2))
            painter.drawRect(bar.adjusted(0, 0, -1, -1))

        playhead_x = self._ms_to_x(self._position_ms)
        painter.setPen(QPen(QColor(231, 76, 60), 2))
        painter.drawLine(playhead_x, 0, playhead_x, self.height())

    def _hit_test(self, pos) -> tuple[int, VideoAnnotationModel, str] | None:
        """
        Determines which annotation row/edge was hit by a mouse position.

        Args:
            pos: Mouse position in widget coordinates.

        Returns:
            tuple[int, VideoAnnotationModel, str] | None: Row index, annotation,
            and drag mode (move/start/end), or None when nothing was hit.
        """

        for index, annotation in enumerate(self._annotations):
            bar = self._bar_rect(index, annotation)
            if not bar.contains(pos):
                continue
            if pos.x() <= bar.x() + EDGE_HIT_PX:
                return index, annotation, DRAG_MODE_START
            if pos.x() >= bar.x() + bar.width() - EDGE_HIT_PX:
                return index, annotation, DRAG_MODE_END
            return index, annotation, DRAG_MODE_MOVE
        return None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Starts a playhead seek or an annotation bar drag.

        Args:
            event: Mouse press event.

        Returns:
            None
        """

        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position().toPoint()

        if pos.y() < RULER_HEIGHT:
            self._drag_mode = DRAG_MODE_PLAYHEAD
            self.seek_requested.emit(self._x_to_ms(pos.x()))
            return

        hit = self._hit_test(pos)
        if hit is None:
            return
        _index, annotation, mode = hit
        self._selected_id = annotation.annotation_id
        self.annotation_selected.emit(annotation.annotation_id)
        self._drag_mode = mode
        self._drag_annotation = annotation
        self._drag_anchor_ms = self._x_to_ms(pos.x())
        self._drag_orig_start = annotation.start_ms
        self._drag_orig_end = annotation.end_ms
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Updates the playhead or drags the active annotation bar/edge.

        Args:
            event: Mouse move event.

        Returns:
            None
        """

        pos = event.position().toPoint()

        if self._drag_mode == DRAG_MODE_PLAYHEAD:
            self.seek_requested.emit(self._x_to_ms(pos.x()))
            return

        if self._drag_mode and self._drag_annotation is not None:
            current_ms = self._x_to_ms(pos.x())
            annotation = self._drag_annotation
            if self._drag_mode == DRAG_MODE_MOVE:
                delta = current_ms - self._drag_anchor_ms
                duration = self._drag_orig_end - self._drag_orig_start
                new_start = max(0, min(self._duration_ms - duration, self._drag_orig_start + delta))
                new_end = new_start + duration
            elif self._drag_mode == DRAG_MODE_START:
                new_start = max(0, min(current_ms, annotation.end_ms - MIN_ANNOTATION_DURATION_MS))
                new_end = annotation.end_ms
            else:
                new_end = min(self._duration_ms, max(current_ms, annotation.start_ms + MIN_ANNOTATION_DURATION_MS))
                new_start = annotation.start_ms

            annotation.start_ms = new_start
            annotation.end_ms = new_end
            self.annotation_time_changed.emit(annotation.annotation_id, new_start, new_end)
            self.update()
            return

        cursor = Qt.CursorShape.ArrowCursor
        hit = self._hit_test(pos)
        if hit is not None:
            _index, _annotation, mode = hit
            if mode in (DRAG_MODE_START, DRAG_MODE_END):
                cursor = Qt.CursorShape.SizeHorCursor
            else:
                cursor = Qt.CursorShape.OpenHandCursor
        self.setCursor(cursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Ends the active drag operation.

        Args:
            event: Mouse release event.

        Returns:
            None
        """

        self._drag_mode = ""
        self._drag_annotation = None
