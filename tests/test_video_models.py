"""
Unit tests for video project data models.
"""

from __future__ import annotations

import unittest

from src.video_models import VideoAnnotationModel, VideoProjectModel


class TestVideoAnnotationModel(unittest.TestCase):
    """
    Verifies round-trip serialization for time-ranged video annotations.
    """

    def test_round_trip_preserves_time_range_and_id(self) -> None:
        """
        Ensures to_dict/from_dict preserves start/end times and the stable id.
        """

        annotation = VideoAnnotationModel(
            annotation_type="rect",
            start_ms=1000,
            end_ms=4000,
            x=10.0,
            y=20.0,
            width=100.0,
            height=50.0,
            stroke_rgba=[255, 0, 0, 255],
            fill_rgba=[255, 0, 0, 70],
            stroke_width=3.0,
        )
        restored = VideoAnnotationModel.from_dict(annotation.to_dict())
        self.assertEqual(restored.annotation_id, annotation.annotation_id)
        self.assertEqual(restored.start_ms, 1000)
        self.assertEqual(restored.end_ms, 4000)
        self.assertEqual(restored.annotation_type, "rect")

    def test_from_dict_generates_id_when_missing(self) -> None:
        """
        Ensures loading legacy/incomplete data still yields a usable id.
        """

        restored = VideoAnnotationModel.from_dict({"annotation_type": "text"})
        self.assertTrue(restored.annotation_id)

    def test_distinct_annotations_get_distinct_ids(self) -> None:
        """
        Ensures each newly created annotation gets a unique identifier.
        """

        first = VideoAnnotationModel(
            annotation_type="rect",
            start_ms=0,
            end_ms=1000,
            x=0.0,
            y=0.0,
            width=10.0,
            height=10.0,
            stroke_rgba=[0, 0, 0, 255],
            fill_rgba=[0, 0, 0, 0],
            stroke_width=1.0,
        )
        second = VideoAnnotationModel(
            annotation_type="rect",
            start_ms=0,
            end_ms=1000,
            x=0.0,
            y=0.0,
            width=10.0,
            height=10.0,
            stroke_rgba=[0, 0, 0, 255],
            fill_rgba=[0, 0, 0, 0],
            stroke_width=1.0,
        )
        self.assertNotEqual(first.annotation_id, second.annotation_id)


class TestVideoProjectModel(unittest.TestCase):
    """
    Verifies round-trip serialization for the full video project document.
    """

    def test_round_trip_preserves_video_metadata_and_annotations(self) -> None:
        """
        Ensures to_dict/from_dict preserves dimensions, duration, and annotations.
        """

        annotation = VideoAnnotationModel(
            annotation_type="arrow",
            start_ms=500,
            end_ms=2500,
            x=1.0,
            y=2.0,
            width=30.0,
            height=40.0,
            stroke_rgba=[0, 255, 0, 255],
            fill_rgba=[0, 255, 0, 0],
            stroke_width=2.0,
        )
        model = VideoProjectModel(
            format_name="snappix-video-project",
            format_version=1,
            video_width=1280,
            video_height=720,
            duration_ms=10000,
            framerate=30.0,
            video_path_in_archive="assets/source.mp4",
            annotations=[annotation],
        )
        restored = VideoProjectModel.from_dict(model.to_dict())
        self.assertEqual(restored.video_width, 1280)
        self.assertEqual(restored.video_height, 720)
        self.assertEqual(restored.duration_ms, 10000)
        self.assertEqual(len(restored.annotations), 1)
        self.assertEqual(restored.annotations[0].annotation_type, "arrow")
        self.assertEqual(restored.annotations[0].start_ms, 500)


if __name__ == "__main__":
    unittest.main()
