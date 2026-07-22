"""
Unit tests for pixel-tool option popup menus on the editor toolbar.
"""

from __future__ import annotations

import unittest

try:
    from PySide6.QtGui import QColor, QPixmap
    from PySide6.QtWidgets import QToolButton

    from src.editor_canvas import ERASE_MODE_FILL, ERASE_MODE_TRANSPARENT, Tool
    from src.editor_window import EditorWindow
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required for toolbar menu tests")
class TestPixelToolOptionMenus(unittest.TestCase):
    """
    Verifies Contiguous, erase-mode, blur, and wand options live on tool popups.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures Qt application exists for widget tests.
        """

        cls._app = ensure_qapp()

    def test_selection_tools_expose_erase_mode_menu(self) -> None:
        """
        Ensures marquee/lasso tool buttons open an erase-mode popup menu.
        """

        pixmap = QPixmap(80, 60)
        pixmap.fill(QColor(220, 220, 220))
        window = EditorWindow(pixmap)
        for tool in (Tool.SELECT_RECT, Tool.SELECT_ELLIPSE, Tool.SELECT_PATH):
            button = window._tool_buttons[tool]  # pylint: disable=protected-access
            self.assertIsNotNone(button.menu())
            self.assertEqual(
                button.popupMode(),
                QToolButton.ToolButtonPopupMode.MenuButtonPopup,
            )
            titles = [action.text() for action in button.menu().actions()]
            self.assertIn("Erase: Transparent", titles)
            self.assertIn("Erase: Fill color", titles)
        self.assertFalse(hasattr(window, "erase_mode_combo"))
        window.close()

    def test_magic_wand_menu_includes_tolerance_contiguous_and_erase(self) -> None:
        """
        Ensures Magic Wand menu includes tolerance slider plus Contiguous/erase.
        """

        pixmap = QPixmap(80, 60)
        pixmap.fill(QColor(220, 220, 220))
        window = EditorWindow(pixmap)
        button = window._tool_buttons[Tool.MAGIC_WAND]  # pylint: disable=protected-access
        titles = [action.text() for action in button.menu().actions() if action.text()]
        self.assertEqual(
            titles,
            ["Contiguous", "Erase: Transparent", "Erase: Fill color"],
        )
        self.assertFalse(hasattr(window, "wand_tolerance_spin"))
        self.assertFalse(hasattr(window, "wand_contiguous_button"))
        window.wand_tolerance_slider.setValue(64)
        self.assertEqual(window.canvas.wand_tolerance(), 64)
        self.assertEqual(window.wand_tolerance_label.text(), "64")
        window.close()

    def test_popup_actions_update_canvas_options(self) -> None:
        """
        Ensures menu actions drive canvas Contiguous and erase mode state.
        """

        pixmap = QPixmap(80, 60)
        pixmap.fill(QColor(220, 220, 220))
        window = EditorWindow(pixmap)
        self.assertTrue(window.canvas.wand_contiguous())
        window.wand_contiguous_action.setChecked(False)
        self.assertFalse(window.canvas.wand_contiguous())

        window.erase_fill_action.trigger()
        self.assertEqual(window.canvas.erase_mode(), ERASE_MODE_FILL)
        window.erase_transparent_action.trigger()
        self.assertEqual(window.canvas.erase_mode(), ERASE_MODE_TRANSPARENT)
        window.close()

    def test_blur_tool_menu_exposes_pixel_block_slider(self) -> None:
        """
        Ensures Blur exposes pixel block size only via its toolbar popup.
        """

        pixmap = QPixmap(80, 60)
        pixmap.fill(QColor(220, 220, 220))
        window = EditorWindow(pixmap)
        button = window._tool_buttons[Tool.BLUR]  # pylint: disable=protected-access
        self.assertIsNotNone(button.menu())
        self.assertEqual(
            button.popupMode(),
            QToolButton.ToolButtonPopupMode.MenuButtonPopup,
        )
        self.assertFalse(hasattr(window, "blur_block_spin"))
        self.assertFalse(hasattr(window, "blur_block_slider"))
        window.blur_block_menu_slider.setValue(24)
        self.assertEqual(window.canvas.blur_block_size(), 24)
        self.assertEqual(window.blur_block_menu_label.text(), "24")
        window.close()

    def test_crop_reclick_applies_pending_selection(self) -> None:
        """
        Ensures clicking Crop again applies a pending crop selection.
        """

        from PySide6.QtCore import QRectF
        from src.crop_item import CropSelectionItem

        pixmap = QPixmap(120, 80)
        pixmap.fill(QColor(220, 220, 220))
        window = EditorWindow(pixmap)
        self.assertFalse(hasattr(window, "apply_crop_button"))
        window._set_tool(Tool.CROP)  # pylint: disable=protected-access
        crop_item = CropSelectionItem(QRectF(10.0, 10.0, 40.0, 30.0))
        window.canvas.scene().addItem(crop_item)
        window.canvas._crop_item = crop_item  # pylint: disable=protected-access
        self.assertTrue(window.canvas.has_pending_crop())
        before = window.canvas.screenshot().size()
        window._on_tool_button_clicked(Tool.CROP)  # pylint: disable=protected-access
        after = window.canvas.screenshot().size()
        self.assertNotEqual((before.width(), before.height()), (after.width(), after.height()))
        self.assertFalse(window.canvas.has_pending_crop())
        window.close()


if __name__ == "__main__":
    unittest.main()
