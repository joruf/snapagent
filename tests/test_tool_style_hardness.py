"""
Tests for per-tool brush hardness and stroke style preferences.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.config import (
    AppConfig,
    ConfigManager,
    DEFAULT_TOOL_BRUSH_HARDNESS,
    DEFAULT_TOOL_STROKE_STYLES,
    normalize_brush_hardness,
    normalize_named_stroke_style,
    normalize_tool_brush_hardness,
    normalize_tool_stroke_styles,
)

try:
    from PySide6.QtGui import QColor, QPixmap
    from PySide6.QtWidgets import QComboBox, QSlider

    from src.annotation_items import STROKE_STYLE_DASH, STROKE_STYLE_DOT
    from src.editor_canvas import Tool
    from src.editor_window import EditorWindow
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


class TestToolStyleHardnessConfig(unittest.TestCase):
    """
    Verifies per-tool hardness and stroke-style normalization.
    """

    def test_normalize_brush_hardness_clamps(self) -> None:
        """
        Ensures hardness stays within 0–100.
        """

        self.assertEqual(normalize_brush_hardness(-5), 0)
        self.assertEqual(normalize_brush_hardness(140), 100)
        self.assertEqual(normalize_brush_hardness("55"), 55)

    def test_normalize_tool_brush_hardness_merges_defaults(self) -> None:
        """
        Ensures unknown tools are ignored and defaults fill missing keys.
        """

        values = normalize_tool_brush_hardness({"brush": 40, "mystery": 9})
        self.assertEqual(values["brush"], 40)
        self.assertEqual(values["eraser"], DEFAULT_TOOL_BRUSH_HARDNESS["eraser"])
        self.assertNotIn("mystery", values)

    def test_normalize_named_stroke_style_falls_back(self) -> None:
        """
        Ensures invalid style names fall back to solid.
        """

        self.assertEqual(normalize_named_stroke_style("dash"), "dash")
        self.assertEqual(normalize_named_stroke_style("nope"), "solid")

    def test_normalize_tool_stroke_styles_merges_defaults(self) -> None:
        """
        Ensures style maps keep defaults for missing tools.
        """

        styles = normalize_tool_stroke_styles({"line": "dot", "mystery": "dash"})
        self.assertEqual(styles["line"], "dot")
        self.assertEqual(styles["arrow"], DEFAULT_TOOL_STROKE_STYLES["arrow"])
        self.assertNotIn("mystery", styles)

    def test_config_roundtrip_persists_hardness_and_styles(self) -> None:
        """
        Ensures hardness and stroke styles survive config save/load.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            manager = ConfigManager(path)
            config = AppConfig(
                tool_brush_hardness={"brush": 25, "eraser": 90},
                tool_stroke_styles={"line": "dash", "rect": "dot"},
            )
            manager.save(config)
            restored = manager.load()
            self.assertEqual(restored.tool_brush_hardness["brush"], 25)
            self.assertEqual(restored.tool_brush_hardness["eraser"], 90)
            self.assertEqual(restored.tool_stroke_styles["line"], "dash")
            self.assertEqual(restored.tool_stroke_styles["rect"], "dot")


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required for editor menu tests")
class TestToolStyleHardnessEditor(unittest.TestCase):
    """
    Verifies tool popup menus expose hardness and stroke style.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures Qt application exists for widget tests.
        """

        cls._app = ensure_qapp()

    def test_palette_no_longer_exposes_hard_or_line_style(self) -> None:
        """
        Ensures Harden and Line style were removed from the Style palette.
        """

        window = EditorWindow(QPixmap(80, 60))
        self.assertFalse(hasattr(window, "brush_hardness_slider"))
        self.assertFalse(hasattr(window, "brush_hardness_label"))
        self.assertFalse(hasattr(window, "stroke_style_combo"))
        window.close()

    def test_brush_and_eraser_menus_expose_hardness(self) -> None:
        """
        Ensures Brush and Eraser popups include a Hard slider.
        """

        window = EditorWindow(QPixmap(80, 60))
        for tool in (Tool.BRUSH, Tool.ERASER):
            self.assertIn(tool, window._tool_hardness_sliders)  # pylint: disable=protected-access
            slider = window._tool_hardness_sliders[tool]  # pylint: disable=protected-access
            self.assertIsInstance(slider, QSlider)
            self.assertEqual(slider.minimum(), 0)
            self.assertEqual(slider.maximum(), 100)
        self.assertNotIn(Tool.LINE, window._tool_hardness_sliders)  # pylint: disable=protected-access
        window.close()

    def test_shape_menus_expose_stroke_style(self) -> None:
        """
        Ensures shape/line tool popups include a Style combo.
        """

        window = EditorWindow(QPixmap(80, 60))
        for tool in (Tool.RECT, Tool.ELLIPSE, Tool.LINE, Tool.ARROW):
            self.assertIn(tool, window._tool_style_combos)  # pylint: disable=protected-access
            combo = window._tool_style_combos[tool]  # pylint: disable=protected-access
            self.assertIsInstance(combo, QComboBox)
            self.assertGreaterEqual(combo.count(), 4)
        self.assertNotIn(Tool.BRUSH, window._tool_style_combos)  # pylint: disable=protected-access
        window.close()

    def test_switching_tools_restores_hardness_and_style(self) -> None:
        """
        Ensures Brush/Line keep independent hardness and style defaults.
        """

        window = EditorWindow(QPixmap(120, 90))
        window.apply_tool_brush_hardness({"brush": 20, "eraser": 95}, emit_signal=False)
        window.apply_tool_stroke_styles(
            {"line": STROKE_STYLE_DASH, "arrow": STROKE_STYLE_DOT},
            emit_signal=False,
        )
        window._set_tool(Tool.BRUSH)  # pylint: disable=protected-access
        self.assertEqual(window.canvas.brush_hardness(), 20.0)
        window._set_tool(Tool.ERASER)  # pylint: disable=protected-access
        self.assertEqual(window.canvas.brush_hardness(), 95.0)
        window._set_tool(Tool.LINE)  # pylint: disable=protected-access
        self.assertEqual(window.canvas._style.stroke_style, STROKE_STYLE_DASH)  # pylint: disable=protected-access
        window._set_tool(Tool.ARROW)  # pylint: disable=protected-access
        self.assertEqual(window.canvas._style.stroke_style, STROKE_STYLE_DOT)  # pylint: disable=protected-access
        window.close()

    def test_tool_menu_hardness_updates_default(self) -> None:
        """
        Ensures the Brush popup Hard slider updates the tool default.
        """

        window = EditorWindow(QPixmap(100, 80))
        window._set_tool(Tool.BRUSH)  # pylint: disable=protected-access
        received: list[dict[str, int]] = []
        window.tool_brush_hardness_changed.connect(received.append)
        slider = window._tool_hardness_sliders[Tool.BRUSH]  # pylint: disable=protected-access
        slider.setValue(33)
        self.assertEqual(window.canvas.brush_hardness(), 33.0)
        self.assertEqual(received[-1]["brush"], 33)
        window.close()

    def test_tool_menu_style_updates_default(self) -> None:
        """
        Ensures the Line popup Style combo updates the tool default.
        """

        window = EditorWindow(QPixmap(100, 80))
        window._set_tool(Tool.LINE)  # pylint: disable=protected-access
        received: list[dict[str, str]] = []
        window.tool_stroke_styles_changed.connect(received.append)
        combo = window._tool_style_combos[Tool.LINE]  # pylint: disable=protected-access
        index = combo.findData(STROKE_STYLE_DASH)
        self.assertGreaterEqual(index, 0)
        combo.setCurrentIndex(index)
        self.assertEqual(window.canvas._style.stroke_style, STROKE_STYLE_DASH)  # pylint: disable=protected-access
        self.assertEqual(received[-1]["line"], STROKE_STYLE_DASH)
        window.close()
