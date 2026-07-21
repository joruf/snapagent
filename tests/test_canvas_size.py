"""
Unit tests for canvas size helpers.
"""

from __future__ import annotations

import unittest

from src.canvas_size import (
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_CANVAS_WIDTH,
    find_canvas_preset,
    parse_canvas_dimension,
    validate_canvas_size,
)


class TestCanvasSize(unittest.TestCase):
    """
    Verifies canvas size parsing and validation.
    """

    def test_parse_canvas_dimension_accepts_valid_values(self) -> None:
        """
        Ensures valid dimension strings are parsed as integers.
        """

        self.assertEqual(parse_canvas_dimension("1920"), 1920)
        self.assertEqual(parse_canvas_dimension(" 720 "), 720)

    def test_parse_canvas_dimension_rejects_invalid_values(self) -> None:
        """
        Ensures invalid dimension strings are rejected.
        """

        self.assertIsNone(parse_canvas_dimension(""))
        self.assertIsNone(parse_canvas_dimension("abc"))
        self.assertIsNone(parse_canvas_dimension("0"))
        self.assertIsNone(parse_canvas_dimension("20000"))

    def test_validate_canvas_size_accepts_common_sizes(self) -> None:
        """
        Ensures common canvas sizes pass validation.
        """

        is_valid, message = validate_canvas_size(DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT)
        self.assertTrue(is_valid)
        self.assertEqual(message, "")

    def test_validate_canvas_size_rejects_out_of_range_values(self) -> None:
        """
        Ensures out-of-range canvas sizes are rejected.
        """

        is_valid, message = validate_canvas_size(0, 720)
        self.assertFalse(is_valid)
        self.assertIn("Width", message)

    def test_find_canvas_preset_returns_hd_defaults(self) -> None:
        """
        Ensures preset lookup returns expected HD dimensions.
        """

        preset = find_canvas_preset("hd")
        self.assertIsNotNone(preset)
        assert preset is not None
        self.assertEqual(preset.width, 1280)
        self.assertEqual(preset.height, 720)
