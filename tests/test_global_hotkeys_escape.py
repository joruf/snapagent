"""
Unit tests for the always-registered Escape-stops-recording global hotkey.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.config import AppConfig
from src.global_hotkeys import GlobalHotkeyManager, HotkeyBridge


class TestEscapeStopsRecording(unittest.TestCase):
    """
    Verifies apply_config always includes an Escape binding for recording_stop.
    """

    def test_escape_binding_is_registered_by_default(self) -> None:
        """
        Ensures <esc> is present in the pynput mapping and triggers recording_stop.
        """

        bridge = HotkeyBridge()
        manager = GlobalHotkeyManager(bridge)
        received: list[str] = []
        bridge.triggered.connect(received.append)

        captured_mapping = {}

        def fake_global_hotkeys(mapping):
            captured_mapping.update(mapping)
            fake_listener = MagicMock()
            return fake_listener

        with patch("src.global_hotkeys.PYNPUT_AVAILABLE", True), patch(
            "src.global_hotkeys.keyboard"
        ) as mock_keyboard:
            mock_keyboard.GlobalHotKeys.side_effect = fake_global_hotkeys
            result = manager.apply_config(AppConfig())

        self.assertTrue(result)
        self.assertIn("<esc>", captured_mapping)

        captured_mapping["<esc>"]()
        self.assertEqual(received, ["recording_stop"])

    def test_escape_does_not_override_an_explicit_user_binding(self) -> None:
        """
        Ensures a (currently impossible, but future-proofed) explicit binding
        to the exact "<esc>" pynput spec is not silently overwritten.
        """

        bridge = HotkeyBridge()
        manager = GlobalHotkeyManager(bridge)
        received: list[str] = []
        bridge.triggered.connect(received.append)

        captured_mapping = {}

        def fake_global_hotkeys(mapping):
            captured_mapping.update(mapping)
            return MagicMock()

        config = AppConfig()
        with patch("src.global_hotkeys.PYNPUT_AVAILABLE", True), patch(
            "src.global_hotkeys.hotkey_spec_to_pynput",
            side_effect=lambda spec: "<esc>" if spec == config.hotkey_capture_region else None,
        ), patch("src.global_hotkeys.keyboard") as mock_keyboard:
            mock_keyboard.GlobalHotKeys.side_effect = fake_global_hotkeys
            manager.apply_config(config)

        captured_mapping["<esc>"]()
        self.assertEqual(received, ["capture_region"])


if __name__ == "__main__":
    unittest.main()
