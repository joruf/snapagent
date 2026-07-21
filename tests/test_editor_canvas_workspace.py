"""
Unit tests for editor canvas workspace and document separation.
"""

from __future__ import annotations

import unittest

try:
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QPixmap

    HAS_PYSIDE6 = True
except ModuleNotFoundError:
    HAS_PYSIDE6 = False


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 is required for editor canvas tests")
class TestEditorCanvasWorkspace(unittest.TestCase):
    """
    Verifies pasteboard layout and export bounds.
    """

    def test_scene_rect_is_larger_than_document(self) -> None:
        """
        Ensures the gray workspace extends beyond the drawable document.
        """

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        pixmap = QPixmap(400, 300)
        pixmap.fill()
        canvas.set_screenshot(pixmap)

        document_rect = canvas.document_rect()
        scene_rect = canvas.sceneRect()

        self.assertEqual(document_rect.width(), 400.0)
        self.assertEqual(document_rect.height(), 300.0)
        self.assertGreater(scene_rect.width(), document_rect.width())
        self.assertGreater(scene_rect.height(), document_rect.height())
        self.assertTrue(scene_rect.contains(document_rect))

    def test_export_uses_document_bounds_only(self) -> None:
        """
        Ensures composited export excludes the surrounding pasteboard.
        """

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        pixmap = QPixmap(320, 240)
        pixmap.fill()
        canvas.set_screenshot(pixmap)

        exported = canvas.export_composited_pixmap()

        self.assertEqual(exported.width(), 320)
        self.assertEqual(exported.height(), 240)

    def test_refresh_workspace_theme_updates_pasteboard_color(self) -> None:
        """
        Ensures theme changes update workspace chrome colors.
        """

        from src.editor_canvas import EditorCanvas
        from src.theme import THEME_DARK, THEME_LIGHT, get_theme_colors

        canvas = EditorCanvas()
        canvas.refresh_workspace_theme(THEME_LIGHT)
        light_workspace = get_theme_colors(THEME_LIGHT).editor_workspace
        self.assertEqual(
            canvas.backgroundBrush().color().name(),
            QColor(light_workspace).name(),
        )

        canvas.refresh_workspace_theme(THEME_DARK)
        dark_workspace = get_theme_colors(THEME_DARK).editor_workspace
        self.assertEqual(
            canvas.backgroundBrush().color().name(),
            QColor(dark_workspace).name(),
        )
