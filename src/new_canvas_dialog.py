"""
Dialog for creating a blank editor canvas with a custom size.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from src.canvas_size import (
    CANVAS_SIZE_PRESETS,
    DEFAULT_CANVAS_HEIGHT,
    DEFAULT_CANVAS_WIDTH,
    find_canvas_preset,
    parse_canvas_dimension,
    validate_canvas_size,
)


class NewCanvasDialog(QDialog):
    """
    Collects canvas dimensions from presets or custom user input.
    """

    def __init__(self, parent=None) -> None:
        """
        Initializes the new canvas dialog.

        Args:
            parent: Optional parent widget.
        """

        super().__init__(parent)
        self.setWindowTitle("New Canvas")
        self.setModal(True)
        self.resize(420, 180)
        self._updating_fields = False

        root_layout = QVBoxLayout(self)
        form = QFormLayout()

        self.preset_combo = QComboBox()
        for preset in CANVAS_SIZE_PRESETS:
            self.preset_combo.addItem(preset.label, preset.key)
        self.preset_combo.setToolTip("Choose a standard canvas size or enter a custom size.")
        form.addRow("Format:", self.preset_combo)

        size_row = QHBoxLayout()
        self.width_edit = QLineEdit(str(DEFAULT_CANVAS_WIDTH))
        self.width_edit.setValidator(QIntValidator(1, 99999, self))
        self.width_edit.setToolTip("Canvas width in pixels.")
        self.height_edit = QLineEdit(str(DEFAULT_CANVAS_HEIGHT))
        self.height_edit.setValidator(QIntValidator(1, 99999, self))
        self.height_edit.setToolTip("Canvas height in pixels.")
        size_row.addWidget(self.width_edit)
        size_row.addWidget(QLabel("×", alignment=Qt.AlignmentFlag.AlignCenter))
        size_row.addWidget(self.height_edit)
        form.addRow("Size:", size_row)

        root_layout.addLayout(form)

        hint = QLabel("Select a preset or enter your own width and height in pixels.")
        hint.setWordWrap(True)
        root_layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_dialog)
        buttons.rejected.connect(self.reject)
        root_layout.addWidget(buttons)

        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self.width_edit.textChanged.connect(self._on_custom_size_edited)
        self.height_edit.textChanged.connect(self._on_custom_size_edited)

        hd_index = self.preset_combo.findData("hd")
        if hd_index >= 0:
            self.preset_combo.setCurrentIndex(hd_index)

    def selected_size(self) -> tuple[int, int] | None:
        """
        Returns the accepted canvas size.

        Returns:
            tuple[int, int] | None: Width and height in pixels.
        """

        width = parse_canvas_dimension(self.width_edit.text())
        height = parse_canvas_dimension(self.height_edit.text())
        if width is None or height is None:
            return None
        is_valid, _message = validate_canvas_size(width, height)
        if not is_valid:
            return None
        return width, height

    def _on_preset_changed(self, index: int) -> None:
        """
        Applies the selected preset dimensions to the size fields.

        Args:
            index: Selected combo box index.

        Returns:
            None
        """

        preset_key = str(self.preset_combo.itemData(index))
        preset = find_canvas_preset(preset_key)
        if preset is None or preset.width is None or preset.height is None:
            return

        self._updating_fields = True
        self.width_edit.setText(str(preset.width))
        self.height_edit.setText(str(preset.height))
        self._updating_fields = False

    def _on_custom_size_edited(self, _text: str) -> None:
        """
        Switches the preset selector to custom when size fields are edited.

        Args:
            _text: Edited field text.

        Returns:
            None
        """

        if self._updating_fields:
            return
        custom_index = self.preset_combo.findData("custom")
        if custom_index >= 0:
            self.preset_combo.setCurrentIndex(custom_index)

    def _accept_dialog(self) -> None:
        """
        Validates user input before accepting the dialog.

        Returns:
            None
        """

        width = parse_canvas_dimension(self.width_edit.text())
        height = parse_canvas_dimension(self.height_edit.text())
        if width is None or height is None:
            QMessageBox.warning(
                self,
                "New Canvas",
                "Enter a valid width and height in pixels.",
            )
            return

        is_valid, message = validate_canvas_size(width, height)
        if not is_valid:
            QMessageBox.warning(self, "New Canvas", message)
            return

        self.accept()
