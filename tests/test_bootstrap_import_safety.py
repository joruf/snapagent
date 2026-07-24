"""
Regression test: run.py's top-level imports must stay PySide6-free.

run.py bootstraps a local .venv and installs PySide6 on first run (see
_ensure_qt_runtime / _reexec_into_venv_if_available), but that bootstrap logic
only runs inside `if __name__ == "__main__":`, at the very bottom of the file.
Every import above that point executes immediately when the module loads —
with whatever interpreter the user happened to invoke (often the system
python3, which has no PySide6 yet). If any top-level import (directly or
transitively) pulls in PySide6, the app crashes with ModuleNotFoundError
before the self-installing bootstrap ever gets a chance to run.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_PROBE_SCRIPT = """
import builtins
import sys

_original_import = builtins.__import__


def _blocking_import(name, *args, **kwargs):
    if name == "PySide6" or name.startswith("PySide6."):
        raise ModuleNotFoundError(f"No module named '{name}'")
    return _original_import(name, *args, **kwargs)


builtins.__import__ = _blocking_import
sys.path.insert(0, "__PROJECT_ROOT__")
import run  # noqa: F401 -- importing (not running __main__) exercises only top-level code.
print("BOOTSTRAP_IMPORT_OK")
"""


class TestBootstrapImportSafety(unittest.TestCase):
    """
    Verifies run.py can be imported (top-level code only) with PySide6 unavailable.
    """

    def test_module_level_imports_do_not_require_pyside6(self) -> None:
        """
        Ensures importing run.py never touches PySide6 before the bootstrap
        (_ensure_qt_runtime / _reexec_into_venv_if_available) has a chance to
        install it and re-exec into the .venv interpreter.
        """

        script = _PROBE_SCRIPT.replace("__PROJECT_ROOT__", str(_PROJECT_ROOT))
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"Importing run.py required PySide6 before the bootstrap check "
            f"could run.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn("BOOTSTRAP_IMPORT_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
