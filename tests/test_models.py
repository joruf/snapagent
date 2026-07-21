"""
Unit tests for project data models.
"""

from __future__ import annotations

import unittest

from src.constants import PROJECT_FORMAT_NAME, PROJECT_FORMAT_VERSION
from src.models import AnnotationModel, ProjectModel


class TestAnnotationModel(unittest.TestCase):
    """
    Verifies serialization and default behavior of annotations.
    """

    def test_to_dict_includes_font_family(self) -> None:
        """
        Ensures text styling fields are serialized.
        """

        model = AnnotationModel(
            annotation_type="text",
            x=10.0,
            y=20.0,
            width=30.0,
            height=40.0,
            stroke_rgba=[1, 2, 3, 4],
            fill_rgba=[5, 6, 7, 8],
            stroke_width=2.5,
            text="hello",
            font_size=18,
            font_family="DejaVu Sans",
            payload={"k": "v"},
        )

        payload = model.to_dict()
        self.assertEqual(payload["font_family"], "DejaVu Sans")
        self.assertEqual(payload["font_size"], 18)
        self.assertEqual(payload["text"], "hello")

    def test_from_dict_uses_defaults(self) -> None:
        """
        Ensures missing fields are restored with defaults.
        """

        model = AnnotationModel.from_dict({})
        self.assertEqual(model.annotation_type, "rect")
        self.assertEqual(model.stroke_rgba, [255, 0, 0, 255])
        self.assertEqual(model.fill_rgba, [255, 0, 0, 70])
        self.assertEqual(model.font_size, 16)
        self.assertEqual(model.font_family, "")


class TestProjectModel(unittest.TestCase):
    """
    Verifies project-level serialization and defaults.
    """

    def test_project_roundtrip_preserves_annotations(self) -> None:
        """
        Ensures to_dict and from_dict keep annotation content.
        """

        annotation = AnnotationModel(
            annotation_type="line",
            x=1.0,
            y=2.0,
            width=3.0,
            height=4.0,
            stroke_rgba=[10, 20, 30, 255],
            fill_rgba=[0, 0, 0, 0],
            stroke_width=1.5,
        )
        project = ProjectModel(
            format_name=PROJECT_FORMAT_NAME,
            format_version=PROJECT_FORMAT_VERSION,
            canvas_width=640,
            canvas_height=480,
            screenshot_png_base64="abc",
            annotations=[annotation],
            metadata={"source": "unit-test"},
        )

        restored = ProjectModel.from_dict(project.to_dict())
        self.assertEqual(restored.format_name, PROJECT_FORMAT_NAME)
        self.assertEqual(restored.format_version, PROJECT_FORMAT_VERSION)
        self.assertEqual(restored.canvas_width, 640)
        self.assertEqual(restored.canvas_height, 480)
        self.assertEqual(len(restored.annotations), 1)
        self.assertEqual(restored.annotations[0].annotation_type, "line")
        self.assertEqual(restored.metadata.get("source"), "unit-test")

