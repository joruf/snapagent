"""
End-to-end style tests for core editor workflows.
"""

from __future__ import annotations

import os
import tempfile
import unittest

try:
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QImage, QPixmap

    from src.editor_window import EditorWindow
    from src.models import AnnotationModel
    from src.storage import build_project_model, save_project
    from tests.qt_test_utils import ensure_qapp

    PYSIDE6_AVAILABLE = True
except ModuleNotFoundError:
    PYSIDE6_AVAILABLE = False


def _solid_pixmap(width: int, height: int) -> QPixmap:
    """
    Creates a solid screenshot pixmap for workflow tests.

    Args:
        width: Output width in pixels.
        height: Output height in pixels.

    Returns:
        QPixmap: Filled pixmap.
    """

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor(255, 255, 255, 255))
    return QPixmap.fromImage(image)


@unittest.skipUnless(PYSIDE6_AVAILABLE, "PySide6 is required for E2E editor tests")
class TestE2EEditorFlow(unittest.TestCase):
    """
    Verifies capture-edit-crop-export and recovery workflows.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures a QApplication instance exists for widget tests.
        """

        cls._app = ensure_qapp()

    def test_core_edit_crop_export_flow(self) -> None:
        """
        Verifies an annotation remains editable after crop and exports succeed.
        """

        window = EditorWindow(_solid_pixmap(320, 200))
        annotation = AnnotationModel(
            annotation_type="text",
            x=60.0,
            y=70.0,
            width=140.0,
            height=60.0,
            stroke_rgba=[20, 20, 20, 255],
            fill_rgba=[0, 0, 0, 0],
            stroke_width=1.0,
            text="Line 1\nLine 2",
            font_size=18,
            font_family="Sans Serif",
            font_bold=True,
            font_italic=True,
            font_underline=True,
        )
        window.canvas.load_annotations([annotation])

        item = next(
            candidate
            for candidate in window.canvas.scene().items()
            if str(candidate.data(1001) or "") == "text"
        )
        item.setSelected(True)
        self.assertTrue(window.canvas.resize_selected_items(1.2))

        window.canvas._apply_crop(QRectF(20.0, 20.0, 240.0, 140.0))  # pylint: disable=protected-access
        cropped_annotations = window.canvas.collect_annotations()
        self.assertEqual(len(cropped_annotations), 1)
        self.assertEqual(cropped_annotations[0].annotation_type, "text")

        with tempfile.TemporaryDirectory() as temp_dir:
            png_path = os.path.join(temp_dir, "flow.png")
            jpg_path = os.path.join(temp_dir, "flow.jpg")
            pdf_path = os.path.join(temp_dir, "flow.pdf")

            self.assertTrue(window.canvas.export_composited_pixmap().save(png_path, "PNG"))
            self.assertTrue(window.canvas.export_composited_pixmap().save(jpg_path, "JPG", 90))
            window._write_pdf_to_path(pdf_path, 300)  # pylint: disable=protected-access

            self.assertTrue(os.path.isfile(png_path))
            self.assertTrue(os.path.isfile(jpg_path))
            self.assertTrue(os.path.isfile(pdf_path))
            self.assertGreater(os.path.getsize(png_path), 0)
            self.assertGreater(os.path.getsize(jpg_path), 0)
            self.assertGreater(os.path.getsize(pdf_path), 0)

        window.close()

    def test_recovery_snapshot_can_be_loaded(self) -> None:
        """
        Verifies recovery snapshot loading into a fresh editor tab.
        """

        recovery_path = EditorWindow.recovery_snapshot_path()
        EditorWindow.discard_recovery_snapshot()

        source_window = EditorWindow(_solid_pixmap(200, 120))
        source_window.canvas.load_annotations(
            [
                AnnotationModel(
                    annotation_type="rect",
                    x=10.0,
                    y=12.0,
                    width=80.0,
                    height=40.0,
                    stroke_rgba=[255, 0, 0, 255],
                    fill_rgba=[255, 0, 0, 80],
                    stroke_width=2.0,
                )
            ]
        )
        project = build_project_model(
            source_window.canvas.screenshot(),
            source_window.canvas.collect_annotations(),
        )
        save_project(recovery_path, project)
        source_window.close()

        target_window = EditorWindow(_solid_pixmap(100, 100))
        self.assertTrue(target_window.load_recovery_snapshot())
        loaded = target_window.canvas.collect_annotations()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].annotation_type, "rect")
        target_window.close()

        EditorWindow.discard_recovery_snapshot()
