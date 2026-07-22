"""
Unit tests for Snappix CLI helpers.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from src.cli import (
        EXPORT_PRESET_DOCS,
        EXPORT_PRESET_LIGHTWEIGHT,
        EXPORT_PRESET_PRINT,
        EXPORT_PRESET_WEB,
        _resolve_output_path,
        resolve_export_preset,
    )

    _HAS_CLI_RUNTIME = True
except ModuleNotFoundError:
    _HAS_CLI_RUNTIME = False


@unittest.skipUnless(_HAS_CLI_RUNTIME, "PySide6 runtime not available")
class CliHelpersTest(unittest.TestCase):
    """
    Tests non-interactive CLI helper functions.
    """

    def test_resolve_export_preset_web(self) -> None:
        """
        Resolves expected defaults for web preset.

        Returns:
            None
        """

        self.assertEqual(resolve_export_preset(EXPORT_PRESET_WEB), (82, 150))

    def test_resolve_export_preset_docs(self) -> None:
        """
        Resolves expected defaults for docs preset.

        Returns:
            None
        """

        self.assertEqual(resolve_export_preset(EXPORT_PRESET_DOCS), (90, 300))

    def test_resolve_export_preset_print(self) -> None:
        """
        Resolves expected defaults for print preset.

        Returns:
            None
        """

        self.assertEqual(resolve_export_preset(EXPORT_PRESET_PRINT), (96, 600))

    def test_resolve_export_preset_lightweight(self) -> None:
        """
        Resolves expected defaults for lightweight preset.

        Returns:
            None
        """

        self.assertEqual(resolve_export_preset(EXPORT_PRESET_LIGHTWEIGHT), (72, 120))

    def test_resolve_export_preset_fallback(self) -> None:
        """
        Resolves fallback defaults for unknown presets.

        Returns:
            None
        """

        self.assertEqual(resolve_export_preset("unknown"), (90, 300))

    def test_resolve_output_path_appends_extension(self) -> None:
        """
        Appends missing output extension.

        Returns:
            None
        """

        self.assertEqual(_resolve_output_path("/tmp/sample", "png"), "/tmp/sample.png")

    def test_resolve_output_path_replaces_extension(self) -> None:
        """
        Replaces mismatched extension with expected one.

        Returns:
            None
        """

        self.assertEqual(_resolve_output_path("/tmp/sample.jpg", "png"), "/tmp/sample.png")


@unittest.skipUnless(_HAS_CLI_RUNTIME, "PySide6 runtime not available")
class CliBatchExportTest(unittest.TestCase):
    """
    Tests batch export command flow with mocked exporters.
    """

    def test_batch_export_success(self) -> None:
        """
        Returns success when all project exports succeed.

        Returns:
            None
        """

        from src import cli as cli_module

        with tempfile.TemporaryDirectory() as temp_dir:
            project_a = Path(temp_dir) / "a.sfp"
            project_b = Path(temp_dir) / "b.sfp"
            project_a.write_text("x", encoding="utf-8")
            project_b.write_text("x", encoding="utf-8")
            output_dir = Path(temp_dir) / "out"
            with patch.object(cli_module, "_run_export_command", return_value=0) as export_mock:
                code = cli_module._run_batch_export_command(
                    projects=[str(project_a), str(project_b)],
                    output_dir=str(output_dir),
                    formats=["png", "jpg"],
                    jpg_quality=90,
                    pdf_dpi=300,
                )

        self.assertEqual(code, 0)
        self.assertEqual(export_mock.call_count, 4)

    def test_batch_export_partial_failure(self) -> None:
        """
        Returns partial-failure code when some exports fail.

        Returns:
            None
        """

        from src import cli as cli_module

        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir) / "a.sfp"
            project.write_text("x", encoding="utf-8")
            output_dir = Path(temp_dir) / "out"
            with patch.object(
                cli_module,
                "_run_export_command",
                side_effect=[0, 2],
            ):
                code = cli_module._run_batch_export_command(
                    projects=[str(project)],
                    output_dir=str(output_dir),
                    formats=["png", "jpg"],
                    jpg_quality=90,
                    pdf_dpi=300,
                )

        self.assertEqual(code, 3)


if __name__ == "__main__":
    unittest.main()
