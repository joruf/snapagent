"""
Unit tests for the video editor timeline widget's drag/resize geometry.
"""

from __future__ import annotations

import unittest

try:
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    from src.timeline_widget import (
        EDGE_HIT_PX,
        LABEL_WIDTH,
        RULER_HEIGHT,
        TimelineWidget,
    )
    from src.video_models import VideoAnnotationModel
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


def _make_annotation(start_ms: int = 2000, end_ms: int = 4000) -> "VideoAnnotationModel":
    """
    Builds one test annotation spanning a known time range.

    Args:
        start_ms: Annotation start time in milliseconds.
        end_ms: Annotation end time in milliseconds.

    Returns:
        VideoAnnotationModel: Test annotation.
    """

    return VideoAnnotationModel(
        annotation_type="rect",
        start_ms=start_ms,
        end_ms=end_ms,
        x=0.0,
        y=0.0,
        width=10.0,
        height=10.0,
        stroke_rgba=[255, 0, 0, 255],
        fill_rgba=[255, 0, 0, 70],
        stroke_width=2.0,
    )


def _mouse_event(event_type, x: float, y: float) -> "QMouseEvent":
    """
    Builds a synthetic left-button mouse event at one widget-local position.

    Args:
        event_type: QMouseEvent.Type value.
        x: Local x coordinate.
        y: Local y coordinate.

    Returns:
        QMouseEvent: Constructed event.
    """

    point = QPointF(x, y)
    return QMouseEvent(
        event_type,
        point,
        point,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required for timeline widget tests")
class TestTimelineWidgetDragging(unittest.TestCase):
    """
    Verifies playhead seeking and body/edge drag math on the timeline widget.

    Uses a fixed 660px-wide widget with a 10000ms duration, giving a track
    area of (660 - LABEL_WIDTH) = 500px representing 10000ms (20ms/px), and a
    test annotation spanning [2000, 4000]ms which maps to bar x=[260, 360].
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures a Qt application exists for widget creation.
        """

        ensure_qapp()

    def _make_widget(self, annotation) -> TimelineWidget:
        """
        Builds a sized TimelineWidget with one annotation row.

        Args:
            annotation: Annotation to display as the single timeline row.

        Returns:
            TimelineWidget: Configured widget.
        """

        widget = TimelineWidget()
        widget.resize(660, RULER_HEIGHT + 60)
        widget.set_duration(10000)
        widget.set_annotations([annotation])
        return widget

    def _row_mid_y(self) -> float:
        """
        Returns the vertical center of the first annotation row.

        Returns:
            float: Y coordinate within the first row.
        """

        return RULER_HEIGHT + 15.0

    def test_body_drag_moves_both_start_and_end(self) -> None:
        """
        Ensures dragging the bar body shifts start/end together, preserving duration.
        """

        annotation = _make_annotation()
        widget = self._make_widget(annotation)
        row_y = self._row_mid_y()

        widget.mousePressEvent(_mouse_event(QMouseEvent.Type.MouseButtonPress, 300.0, row_y))
        widget.mouseMoveEvent(_mouse_event(QMouseEvent.Type.MouseMove, 400.0, row_y))
        widget.mouseReleaseEvent(_mouse_event(QMouseEvent.Type.MouseButtonRelease, 400.0, row_y))

        self.assertEqual(annotation.start_ms, 4000)
        self.assertEqual(annotation.end_ms, 6000)

    def test_left_edge_drag_changes_only_start(self) -> None:
        """
        Ensures dragging the left edge changes only start_ms.
        """

        annotation = _make_annotation()
        widget = self._make_widget(annotation)
        row_y = self._row_mid_y()

        # Bar left edge is at x=260; stay within EDGE_HIT_PX of it.
        press_x = 260.0 + (EDGE_HIT_PX / 2.0)
        widget.mousePressEvent(_mouse_event(QMouseEvent.Type.MouseButtonPress, press_x, row_y))
        widget.mouseMoveEvent(_mouse_event(QMouseEvent.Type.MouseMove, 310.0, row_y))
        widget.mouseReleaseEvent(_mouse_event(QMouseEvent.Type.MouseButtonRelease, 310.0, row_y))

        self.assertEqual(annotation.start_ms, 3000)
        self.assertEqual(annotation.end_ms, 4000)

    def test_right_edge_drag_changes_only_end(self) -> None:
        """
        Ensures dragging the right edge changes only end_ms.
        """

        annotation = _make_annotation()
        widget = self._make_widget(annotation)
        row_y = self._row_mid_y()

        # Bar right edge is at x=360; stay within EDGE_HIT_PX of it.
        press_x = 360.0 - (EDGE_HIT_PX / 2.0)
        widget.mousePressEvent(_mouse_event(QMouseEvent.Type.MouseButtonPress, press_x, row_y))
        widget.mouseMoveEvent(_mouse_event(QMouseEvent.Type.MouseMove, 450.0, row_y))
        widget.mouseReleaseEvent(_mouse_event(QMouseEvent.Type.MouseButtonRelease, 450.0, row_y))

        self.assertEqual(annotation.start_ms, 2000)
        self.assertEqual(annotation.end_ms, 5800)

    def test_body_drag_clamps_to_duration_bounds(self) -> None:
        """
        Ensures a body drag cannot push the annotation past the timeline bounds.
        """

        annotation = _make_annotation(start_ms=8000, end_ms=9500)
        widget = self._make_widget(annotation)
        row_y = self._row_mid_y()

        # Bar for [8000, 9500]ms: x = [160 + 8000/20, 160 + 9500/20] = [560, 635].
        widget.mousePressEvent(_mouse_event(QMouseEvent.Type.MouseButtonPress, 600.0, row_y))
        widget.mouseMoveEvent(_mouse_event(QMouseEvent.Type.MouseMove, 660.0, row_y))
        widget.mouseReleaseEvent(_mouse_event(QMouseEvent.Type.MouseButtonRelease, 660.0, row_y))

        duration = 1500
        self.assertEqual(annotation.end_ms - annotation.start_ms, duration)
        self.assertLessEqual(annotation.end_ms, 10000)

    def test_ruler_click_emits_seek_requested(self) -> None:
        """
        Ensures clicking the ruler area emits a seek request instead of dragging a bar.
        """

        annotation = _make_annotation()
        widget = self._make_widget(annotation)
        seeks: list[int] = []
        widget.seek_requested.connect(seeks.append)

        widget.mousePressEvent(
            _mouse_event(QMouseEvent.Type.MouseButtonPress, 410.0, RULER_HEIGHT - 5.0)
        )

        self.assertEqual(seeks, [5000])
        self.assertEqual(annotation.start_ms, 2000)
        self.assertEqual(annotation.end_ms, 4000)


if __name__ == "__main__":
    unittest.main()
