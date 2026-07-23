"""
Tests for live text style editing on selected annotations.
"""

from __future__ import annotations

import unittest

try:
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor, QPixmap
    from PySide6.QtWidgets import QGraphicsTextItem

    from src.annotation_items import ITEM_ROLE_TYPE, configure_graphics_item
    from src.annotation_shapes import TEXT_STYLE_BOX, TEXT_STYLE_PLAIN, StyledTextItem
    from src.editor_canvas import EditorCanvas, Tool
    from src.editor_window import EditorWindow
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required")
class TestLiveTextStyleEditing(unittest.TestCase):
    """
    Verifies font/size/style updates apply immediately to selected text.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures a QApplication exists.
        """

        cls._app = ensure_qapp()

    def test_created_text_is_selected_and_accepts_font_updates(self) -> None:
        """
        Ensures newly inserted text is selected and reacts to style changes.
        """

        window = EditorWindow(QPixmap(240, 160))
        canvas = window.canvas
        canvas.set_tool(Tool.TEXT)
        canvas.set_style(font_size=16, font_family="Sans Serif", apply_to_selection=False)
        item = canvas._create_text_item("Hello", QPointF(20, 30))  # pylint: disable=protected-access
        canvas._select_annotation_item(item)  # pylint: disable=protected-access
        self.assertTrue(item.isSelected())
        self.assertIsInstance(item, StyledTextItem)

        window.font_size_combo.setCurrentText("32")
        self.assertEqual(item.font().pointSize(), 32)

        window.font_family_combo.setCurrentText("DejaVu Sans")
        self.assertEqual(item.font().family(), "DejaVu Sans")

        window.text_bold_button.click()
        self.assertTrue(item.font().bold())
        window.close()

    def test_text_style_combo_updates_selected_container(self) -> None:
        """
        Ensures Style combo switches plain text to a boxed container live.
        """

        window = EditorWindow(QPixmap(240, 160))
        canvas = window.canvas
        item = canvas._create_text_item("Callout", QPointF(12, 18))  # pylint: disable=protected-access
        canvas._select_annotation_item(item)  # pylint: disable=protected-access
        self.assertEqual(item.text_style(), TEXT_STYLE_PLAIN)

        box_index = window.text_style_combo.findData(TEXT_STYLE_BOX)
        self.assertGreaterEqual(box_index, 0)
        window.text_style_combo.setCurrentIndex(box_index)
        self.assertEqual(item.text_style(), TEXT_STYLE_BOX)
        window.close()

    def test_legacy_graphics_text_font_updates_when_selected(self) -> None:
        """
        Ensures older QGraphicsTextItem annotations still accept font edits.
        """

        canvas = EditorCanvas()
        canvas.set_screenshot(QPixmap(200, 120))
        item = canvas._scene.addText("Legacy")  # pylint: disable=protected-access
        configure_graphics_item(item, "text")
        item.setSelected(True)
        self.assertEqual(item.data(ITEM_ROLE_TYPE), "text")
        self.assertIsInstance(item, QGraphicsTextItem)

        canvas.set_style(font_size=28, font_bold=True)
        self.assertEqual(item.font().pointSize(), 28)
        self.assertTrue(item.font().bold())


if __name__ == "__main__":
    unittest.main()
