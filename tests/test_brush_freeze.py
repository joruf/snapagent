"""
Regression tests against brush painting freezes on large screenshots.
"""

from __future__ import annotations

import time
import unittest

from src.brush_paint import (
    MAX_STAMPS_PER_SEGMENT,
    clamp_brush_radius,
    _sample_segment_points,
)

try:
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor, QImage, QPixmap
    from PySide6.QtWidgets import QWidget

    from src.editor_canvas import Tool
    from src.editor_window import EditorWindow
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


class TestBrushPaintSafety(unittest.TestCase):
    """
    Verifies brush helpers cannot explode into unbounded work.
    """

    def test_sample_points_are_capped(self) -> None:
        """
        Ensures long segments never generate unbounded stamp counts.
        """

        if not PYSIDE6_AVAILABLE:
            self.skipTest("PySide6 is required")
        points = _sample_segment_points(QPointF(0, 0), QPointF(10000, 0), 0.01)
        # +1 because endpoints inclusive.
        self.assertLessEqual(len(points), MAX_STAMPS_PER_SEGMENT + 1)

    def test_brush_radius_is_clamped(self) -> None:
        """
        Ensures extreme radii collapse to the safety cap.
        """

        self.assertEqual(clamp_brush_radius(9999.0), 128.0)
        self.assertGreaterEqual(clamp_brush_radius(0.01), 0.25)


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required for brush freeze tests")
class TestBrushStrokePerformance(unittest.TestCase):
    """
    Verifies interactive brush strokes reuse one buffer and stay responsive.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures QApplication exists for Qt widgets.
        """

        cls._app = ensure_qapp()

    def test_brush_stroke_reuses_paint_buffer(self) -> None:
        """
        Ensures one stroke keeps a single paint image instead of reallocating.
        """

        image = QImage(800, 600, QImage.Format.Format_ARGB32)
        image.fill(QColor(240, 240, 240, 255))
        window = EditorWindow(QPixmap.fromImage(image))
        canvas = window.canvas
        canvas.set_tool(Tool.BRUSH)
        canvas.set_style(stroke_width=12.0, stroke_color=QColor(255, 0, 0, 200))
        canvas._begin_brush_stroke()  # pylint: disable=protected-access
        canvas._brush_painting = True  # pylint: disable=protected-access
        first_buffer = canvas._brush_paint_image  # pylint: disable=protected-access
        self.assertIsNotNone(first_buffer)
        canvas._paint_brush_segment(QPointF(10, 10), QPointF(40, 30))  # pylint: disable=protected-access
        canvas._paint_brush_segment(QPointF(40, 30), QPointF(90, 80))  # pylint: disable=protected-access
        self.assertIs(canvas._brush_paint_image, first_buffer)  # pylint: disable=protected-access
        canvas._finish_brush_stroke(commit=True)  # pylint: disable=protected-access
        self.assertIsNone(canvas._brush_paint_image)  # pylint: disable=protected-access
        window.close()

    def test_many_brush_moves_on_large_image_stay_bounded(self) -> None:
        """
        Ensures a burst of brush moves on a large image finishes quickly.
        """

        image = QImage(1920, 1080, QImage.Format.Format_ARGB32)
        image.fill(QColor(255, 255, 255, 255))
        window = EditorWindow(QPixmap.fromImage(image))
        canvas = window.canvas
        canvas.set_tool(Tool.BRUSH)
        canvas.set_style(stroke_width=16.0, stroke_color=QColor(0, 0, 255, 255))
        canvas._brush_painting = True  # pylint: disable=protected-access
        canvas._begin_brush_stroke()  # pylint: disable=protected-access
        started = time.perf_counter()
        point = QPointF(20.0, 20.0)
        for index in range(40):
            next_point = QPointF(20.0 + index * 8.0, 20.0 + (index % 5) * 3.0)
            canvas._paint_brush_segment(point, next_point)  # pylint: disable=protected-access
            point = next_point
        elapsed = time.perf_counter() - started
        canvas._finish_brush_stroke(commit=True)  # pylint: disable=protected-access
        # 40 full-frame copies used to stall for seconds; buffered path must stay snappy.
        self.assertLess(elapsed, 2.5)
        window.close()

    def test_many_eraser_moves_on_large_image_stay_bounded(self) -> None:
        """
        Ensures eraser strokes share the same buffered, non-blocking path as brush.
        """

        image = QImage(1920, 1080, QImage.Format.Format_ARGB32)
        image.fill(QColor(40, 120, 200, 255))
        window = EditorWindow(QPixmap.fromImage(image))
        canvas = window.canvas
        canvas.set_tool(Tool.ERASER)
        canvas.set_style(stroke_width=20.0, stroke_color=QColor(255, 255, 255, 255))
        canvas._brush_painting = True  # pylint: disable=protected-access
        canvas._brush_erase_mode = True  # pylint: disable=protected-access
        canvas._begin_brush_stroke()  # pylint: disable=protected-access
        started = time.perf_counter()
        point = QPointF(30.0, 30.0)
        for index in range(40):
            next_point = QPointF(30.0 + index * 7.0, 30.0 + (index % 4) * 4.0)
            canvas._paint_brush_segment(point, next_point)  # pylint: disable=protected-access
            point = next_point
        elapsed = time.perf_counter() - started
        canvas._finish_brush_stroke(commit=True)  # pylint: disable=protected-access
        self.assertLess(elapsed, 2.5)
        window.close()

    def test_set_tool_releases_active_brush_stroke(self) -> None:
        """
        Ensures switching tools cannot leave a stuck mouse grab / paint state.
        """

        window = EditorWindow(QPixmap(200, 120))
        canvas = window.canvas
        canvas.set_tool(Tool.BRUSH)
        canvas._brush_painting = True  # pylint: disable=protected-access
        canvas._brush_stroke_dirty = True  # pylint: disable=protected-access
        canvas._begin_brush_stroke()  # pylint: disable=protected-access
        canvas.set_tool(Tool.SELECT)
        self.assertFalse(canvas._brush_painting)  # pylint: disable=protected-access
        self.assertIsNone(canvas._brush_paint_image)  # pylint: disable=protected-access
        self.assertIsNone(QWidget.mouseGrabber())
        window.close()


if __name__ == "__main__":
    unittest.main()
