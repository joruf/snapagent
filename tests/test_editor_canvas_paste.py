"""
Unit tests for editor canvas clipboard paste behavior.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from PySide6.QtCore import QMimeData, QPoint, QUrl
    from PySide6.QtGui import QColor, QPixmap

    from tests.qt_test_utils import ensure_qapp

    HAS_PYSIDE6 = True
except ModuleNotFoundError:
    HAS_PYSIDE6 = False


def _solid_pixmap(width: int, height: int, color: QColor | None = None) -> QPixmap:
    """
    Creates a solid pixmap for paste tests.

    Args:
        width: Pixmap width.
        height: Pixmap height.
        color: Fill color.

    Returns:
        QPixmap: Solid pixmap.
    """

    pixmap = QPixmap(width, height)
    pixmap.fill(color or QColor(120, 180, 240, 255))
    return pixmap


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 is required for editor canvas paste tests")
class TestEditorCanvasPaste(unittest.TestCase):
    """
    Verifies clipboard image paste and blank canvas resizing.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures Qt application exists for graphics tests.
        """

        cls._app = ensure_qapp()

    def test_paste_image_selects_item_with_resize_support(self) -> None:
        """
        Ensures pasted images become selected movable annotations.
        """

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        canvas.set_screenshot(_solid_pixmap(400, 300))
        mime = QMimeData()
        mime.setImageData(_solid_pixmap(120, 80).toImage())

        with patch.object(canvas, "_pixmap_from_clipboard", return_value=_solid_pixmap(120, 80)):
            canvas.paste_from_clipboard(QPoint(200, 150))

        selected = canvas.scene().selectedItems()
        self.assertEqual(len(selected), 1)
        self.assertEqual(str(selected[0].data(1001)), "image")
        self.assertIsNotNone(canvas._resize_overlay_item)  # pylint: disable=protected-access

    def test_paste_image_file_from_clipboard_url(self) -> None:
        """
        Ensures copied image files can be pasted from clipboard URLs.
        """

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        canvas.set_screenshot(_solid_pixmap(400, 300))

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "clip.png"
            _solid_pixmap(96, 64).save(str(image_path), "PNG")
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(str(image_path))])

            pixmap = canvas._pixmap_from_clipboard(mime)  # pylint: disable=protected-access
            self.assertIsNotNone(pixmap)
            assert pixmap is not None
            self.assertEqual(pixmap.width(), 96)
            self.assertEqual(pixmap.height(), 64)

    def test_blank_canvas_adopts_pasted_image_dimensions(self) -> None:
        """
        Ensures an unused blank canvas resizes to the first pasted image.
        """

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        canvas.set_screenshot(_solid_pixmap(640, 480))
        canvas.set_blank_document(True)

        with patch.object(canvas, "_pixmap_from_clipboard", return_value=_solid_pixmap(220, 140)):
            canvas.paste_from_clipboard()

        self.assertEqual(canvas.document_rect().width(), 220.0)
        self.assertEqual(canvas.document_rect().height(), 140.0)
        self.assertFalse(canvas.is_blank_document())
        annotations = canvas.collect_annotations()
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].annotation_type, "image")
        self.assertAlmostEqual(annotations[0].x, 0.0, delta=1.0)
        self.assertAlmostEqual(annotations[0].y, 0.0, delta=1.0)

    def test_blank_canvas_does_not_resize_after_first_annotation_exists(self) -> None:
        """
        Ensures later pastes keep the current document size once content exists.
        """

        from src.annotation_items import add_annotation_to_scene
        from src.editor_canvas import EditorCanvas
        from src.models import AnnotationModel

        canvas = EditorCanvas()
        canvas.set_screenshot(_solid_pixmap(500, 400))
        canvas.set_blank_document(True)
        add_annotation_to_scene(
            canvas.scene(),
            AnnotationModel(
                annotation_type="rect",
                x=20.0,
                y=20.0,
                width=40.0,
                height=30.0,
                stroke_rgba=[255, 0, 0, 255],
                fill_rgba=[255, 0, 0, 80],
                stroke_width=2.0,
            ),
        )

        with patch.object(canvas, "_pixmap_from_clipboard", return_value=_solid_pixmap(180, 120)):
            canvas.paste_from_clipboard()

        self.assertEqual(canvas.document_rect().width(), 500.0)
        self.assertEqual(canvas.document_rect().height(), 400.0)
        self.assertTrue(canvas.is_blank_document())

    def test_paste_local_path_text_inserts_image(self) -> None:
        """
        Ensures clipboard text with a local image path pastes the image itself.
        """

        from PySide6.QtGui import QGuiApplication

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        canvas.set_screenshot(_solid_pixmap(400, 300))

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "photo.png"
            _solid_pixmap(88, 66).save(str(image_path), "PNG")
            mime = QMimeData()
            mime.setText(str(image_path))
            QGuiApplication.clipboard().setMimeData(mime)

            canvas.paste_from_clipboard()

        annotations = canvas.collect_annotations()
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].annotation_type, "image")
        self.assertAlmostEqual(annotations[0].width, 88.0, delta=2.0)
        self.assertAlmostEqual(annotations[0].height, 66.0, delta=2.0)

    def test_paste_gnome_copied_files_mime_inserts_image(self) -> None:
        """
        Ensures GNOME file-copy clipboard payloads paste as images.
        """

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        canvas.set_screenshot(_solid_pixmap(400, 300))

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "gnome.png"
            _solid_pixmap(72, 48).save(str(image_path), "PNG")
            mime = QMimeData()
            mime.setData(
                "x-special/gnome-copied-files",
                f"copy\nfile://{image_path}".encode("utf-8"),
            )

            pixmap = canvas._pixmap_from_clipboard(mime)  # pylint: disable=protected-access
            self.assertIsNotNone(pixmap)
            assert pixmap is not None
            self.assertEqual(pixmap.width(), 72)
            self.assertEqual(pixmap.height(), 48)

    def test_import_image_file_inserts_movable_image(self) -> None:
        """
        Ensures menu/file import inserts one image annotation.
        """

        from src.editor_canvas import EditorCanvas

        canvas = EditorCanvas()
        canvas.set_screenshot(_solid_pixmap(400, 300))

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "import.png"
            _solid_pixmap(110, 90).save(str(image_path), "PNG")
            imported = canvas.import_image_file(str(image_path))

        self.assertTrue(imported)
        annotations = canvas.collect_annotations()
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].annotation_type, "image")
        self.assertAlmostEqual(annotations[0].width, 110.0, delta=2.0)
        self.assertAlmostEqual(annotations[0].height, 90.0, delta=2.0)
