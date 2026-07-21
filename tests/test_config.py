"""
Unit tests for configuration persistence.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.config import AppConfig, ConfigManager
from src.theme import THEME_LIGHT


class TestConfigManager(unittest.TestCase):
    """
    Verifies load and save behavior for app settings.
    """

    def test_load_returns_defaults_for_missing_file(self) -> None:
        """
        Ensures missing config file uses default values.
        """

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            manager = ConfigManager(config_path)
            config = manager.load()
            self.assertFalse(config.autostart_enabled)
            self.assertEqual(config.theme, "dark")

    def test_load_returns_defaults_for_invalid_json(self) -> None:
        """
        Ensures invalid JSON does not crash and falls back.
        """

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text("{invalid", encoding="utf-8")
            manager = ConfigManager(config_path)
            config = manager.load()
            self.assertFalse(config.autostart_enabled)
            self.assertEqual(config.theme, "dark")

    def test_save_and_load_roundtrip(self) -> None:
        """
        Ensures saved configuration can be loaded again.
        """

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "nested" / "config.json"
            manager = ConfigManager(config_path)
            manager.save(AppConfig(autostart_enabled=True, theme=THEME_LIGHT))

            restored = manager.load()
            self.assertTrue(restored.autostart_enabled)
            self.assertEqual(restored.theme, THEME_LIGHT)

