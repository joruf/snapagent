"""
Unit tests for the new canvas dialog.
"""

from __future__ import annotations

import unittest

try:
    from tests.qt_test_utils import ensure_qapp

    from src.new_canvas_dialog import NewCanvasDialog

    HAS_PYSIDE6 = True
except ModuleNotFoundError:
    HAS_PYSIDE6 = False


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 is required for new canvas dialog tests")
class TestNewCanvasDialog(unittest.TestCase):
    """
    Verifies new canvas dialog behavior.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures Qt application exists for dialog tests.

        Returns:
            None
        """

        cls._app = ensure_qapp()

    def test_preset_selection_updates_size_fields(self) -> None:
        """
        Ensures choosing a preset fills width and height fields.
        """

        dialog = NewCanvasDialog()
        full_hd_index = dialog.preset_combo.findData("full_hd")
        dialog.preset_combo.setCurrentIndex(full_hd_index)
        self.assertEqual(dialog.width_edit.text(), "1920")
        self.assertEqual(dialog.height_edit.text(), "1080")

    def test_custom_size_editing_switches_to_custom_preset(self) -> None:
        """
        Ensures manual size edits select the custom preset entry.
        """

        dialog = NewCanvasDialog()
        dialog.width_edit.setText("1600")
        dialog.height_edit.setText("900")
        self.assertEqual(dialog.preset_combo.currentData(), "custom")
        self.assertEqual(dialog.selected_size(), (1600, 900))
