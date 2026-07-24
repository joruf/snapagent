"""
Unit tests for the blinking recording-border overlay.
"""

from __future__ import annotations

import unittest

try:
    from PySide6.QtCore import QRect

    from src.capture import (
        RECORDING_BORDER_THICKNESS,
        RecordingBorderOverlay,
    )
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required for recording border overlay tests")
class TestRecordingBorderOverlay(unittest.TestCase):
    """
    Verifies the overlay is positioned entirely outside the recorded pixels.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures a Qt application exists for widget creation.
        """

        ensure_qapp()

    def test_geometry_surrounds_capture_rect_without_overlapping_it(self) -> None:
        """
        Ensures the overlay's outer geometry is exactly the capture rect
        expanded by the border thickness on every side, so the recorded
        pixels themselves stay untouched by the drawn border.
        """

        capture_rect = QRect(100, 200, 640, 480)
        overlay = RecordingBorderOverlay(capture_rect)
        try:
            geometry = overlay.geometry()
            self.assertEqual(geometry.x(), capture_rect.x() - RECORDING_BORDER_THICKNESS)
            self.assertEqual(geometry.y(), capture_rect.y() - RECORDING_BORDER_THICKNESS)
            self.assertEqual(
                geometry.width(), capture_rect.width() + 2 * RECORDING_BORDER_THICKNESS
            )
            self.assertEqual(
                geometry.height(), capture_rect.height() + 2 * RECORDING_BORDER_THICKNESS
            )
        finally:
            overlay.close()

    def test_set_paused_stops_blinking(self) -> None:
        """
        Ensures pausing freezes the border in its visible phase instead of blinking.
        """

        overlay = RecordingBorderOverlay(QRect(0, 0, 100, 100))
        try:
            overlay.set_paused(True)
            self.assertTrue(overlay._paused)  # pylint: disable=protected-access
            overlay._on_blink_tick()  # pylint: disable=protected-access
            # A paused overlay should not toggle its blink phase on tick.
            self.assertTrue(overlay._blink_on)  # pylint: disable=protected-access

            overlay.set_paused(False)
            overlay._on_blink_tick()  # pylint: disable=protected-access
            self.assertFalse(overlay._blink_on)  # pylint: disable=protected-access
        finally:
            overlay.close()


if __name__ == "__main__":
    unittest.main()
