"""
Qt test helpers for headless unit tests.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication


def ensure_qapp() -> QApplication:
    """
    Returns a shared QApplication instance for tests.

    Returns:
        QApplication: Existing or newly created application.
    """

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

