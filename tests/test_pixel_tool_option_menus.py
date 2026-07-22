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
    Verifies Contiguous and erase-mode options live on toolbar popup menus.
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

    def test_magic_wand_menu_includes_contiguous_and_erase(self) -> None:
        """
        Ensures Magic Wand menu includes Contiguous plus erase modes.
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
        self.assertFalse(hasattr(window, "wand_contiguous_button"))
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


if __name__ == "__main__":
    unittest.main()
