"""
Regression tests for editor session recovery across mixed tab types.

_collect_editor_session_tabs() used to iterate every tab in self.editor_tabs
and unconditionally call EditorWindow-only methods (flush_recovery_snapshot,
recovery_path, set_recovery_path) on each one. Once VideoEditorWindow tabs
started sharing the same QTabWidget, closing the editor host crashed with
AttributeError because video tabs don't implement that recovery API by
design (see _create_video_editor_tab in run.py).
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

try:
    from PySide6.QtWidgets import QApplication, QTabWidget, QWidget

    from tests.qt_test_utils import ensure_qapp

    HAS_PYSIDE6 = True
except ModuleNotFoundError:
    HAS_PYSIDE6 = False


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 is required for editor session recovery tests")
class TestCollectEditorSessionTabsSkipsVideoTabs(unittest.TestCase):
    """
    Verifies _collect_editor_session_tabs ignores video editor tabs entirely.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Ensures a Qt application exists.
        """

        cls._app = ensure_qapp()

    def test_video_tabs_are_skipped_without_error(self) -> None:
        """
        Ensures a mixed tab strip (image + video editor tabs) can be collected
        for session recovery without raising, and only the image tab is kept.
        """

        from run import AppController

        controller = object.__new__(AppController)
        controller.editor_tabs = QTabWidget()

        image_editor = QWidget()
        image_editor.flush_recovery_snapshot = MagicMock()
        image_editor.recovery_path = MagicMock(return_value="/tmp/recovery-image.sfp")
        image_editor.set_recovery_path = MagicMock()
        image_editor._current_project_path = ""
        controller.editor_tabs.addTab(image_editor, "Screenshot 1")

        # A bare QWidget stands in for VideoEditorWindow: it has none of the
        # image-editor recovery methods, exactly like the real class.
        video_editor = QWidget()
        controller.editor_tabs.addTab(video_editor, "Recording 1")
        controller.video_editors = [video_editor]
        controller.editors = [image_editor]

        tabs = controller._collect_editor_session_tabs()

        image_editor.flush_recovery_snapshot.assert_called_once()
        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0].title, "Screenshot 1")


if __name__ == "__main__":
    unittest.main()
