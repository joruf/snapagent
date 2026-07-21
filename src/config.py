"""
Application configuration model and persistence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.theme import DEFAULT_THEME, normalize_theme_name


@dataclass(slots=True)
class AppConfig:
    """
    Defines persisted SnapAgent user settings.

    Attributes:
        autostart_enabled: Whether app launches at desktop login.
        theme: Active UI theme identifier (light or dark).
    """

    autostart_enabled: bool = False
    theme: str = DEFAULT_THEME


class ConfigManager:
    """
    Reads and writes SnapAgent configuration.
    """

    def __init__(self, config_path: Path) -> None:
        """
        Initializes the manager with target path.

        Args:
            config_path: JSON configuration file path.
        """

        self.config_path = config_path

    def load(self) -> AppConfig:
        """
        Loads configuration from disk or returns defaults.

        Returns:
            AppConfig: Loaded or fallback configuration.
        """

        if not self.config_path.exists():
            return AppConfig()
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppConfig()
        return AppConfig(
            autostart_enabled=bool(payload.get("autostart_enabled", False)),
            theme=normalize_theme_name(str(payload.get("theme", DEFAULT_THEME))),
        )

    def save(self, config: AppConfig) -> None:
        """
        Persists configuration as JSON.

        Args:
            config: Configuration model to store.

        Returns:
            None
        """

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "autostart_enabled": config.autostart_enabled,
            "theme": normalize_theme_name(config.theme),
        }
        self.config_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
