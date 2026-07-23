"""
Tests for standard SVG export of composited screenshots.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from PySide6.QtGui import QColor, QPixmap

    from src.cli import _run_export_command
    from src.image_export import write_pixmap_as_svg
    from src.models import AnnotationModel, ProjectModel
    from src.storage import save_project
    from src.constants import PROJECT_FORMAT_NAME, PROJECT_FORMAT_VERSION
    from src.storage import pixmap_to_base64_png
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


def _solid_pixmap(width: int, height: int, color: QColor) -> QPixmap:
    """
    Creates a solid color pixmap.

    Args:
        width: Image width.
        height: Image height.
        color: Fill color.

    Returns:
        QPixmap: Solid pixmap.
    """

    pixmap = QPixmap(width, height)
    pixmap.fill(color)
    return pixmap


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required for SVG export tests")
class TestSvgExport(unittest.TestCase):
    """
    Verifies normal SVG export of composited images.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures a Qt application exists.
        """

        cls._app = ensure_qapp()

    def test_write_pixmap_as_svg_creates_svg_document(self) -> None:
        """
        Ensures SVG export writes a non-empty SVG file with an svg root.
        """

        pixmap = _solid_pixmap(64, 48, QColor(20, 120, 200, 255))
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "shot.svg"
            self.assertTrue(write_pixmap_as_svg(pixmap, target))
            self.assertTrue(target.is_file())
            content = target.read_text(encoding="utf-8", errors="ignore")
            self.assertIn("<svg", content.lower())
            self.assertGreater(target.stat().st_size, 100)

    def test_write_pixmap_as_svg_rejects_null_pixmap(self) -> None:
        """
        Ensures null pixmaps do not create SVG files.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "empty.svg"
            self.assertFalse(write_pixmap_as_svg(QPixmap(), target))
            self.assertFalse(target.exists())

    def test_cli_export_svg(self) -> None:
        """
        Ensures the CLI export command can write SVG output.
        """

        pixmap = _solid_pixmap(40, 30, QColor(255, 0, 0, 255))
        model = ProjectModel(
            format_name=PROJECT_FORMAT_NAME,
            format_version=PROJECT_FORMAT_VERSION,
            canvas_width=40,
            canvas_height=30,
            screenshot_png_base64=pixmap_to_base64_png(pixmap),
            annotations=[
                AnnotationModel(
                    annotation_type="rect",
                    x=4.0,
                    y=4.0,
                    width=12.0,
                    height=10.0,
                    stroke_rgba=[0, 0, 0, 255],
                    fill_rgba=[0, 255, 0, 80],
                    stroke_width=2.0,
                )
            ],
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "demo.sfp"
            output_path = Path(temp_dir) / "demo.svg"
            save_project(project_path, model)
            result = _run_export_command(
                project_path=str(project_path),
                output_path=str(output_path),
                fmt="svg",
                jpg_quality=90,
                pdf_dpi=300,
            )
            self.assertEqual(result, 0)
            self.assertTrue(output_path.is_file())
            self.assertIn("<svg", output_path.read_text(encoding="utf-8", errors="ignore").lower())
