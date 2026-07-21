"""
Main screenshot editing window for SnapAgent.
"""

from __future__ import annotations

import tempfile
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QAction,
    QGuiApplication,
    QKeySequence,
    QPainter,
    QPageLayout,
    QPageSize,
    QPagedPaintDevice,
    QPdfWriter,
    QPixmap,
)
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.constants import (
    ABOUT_AUTHOR,
    ABOUT_WEBSITE,
    APP_FILE_EXTENSION,
    APP_NAME,
)
from src.editor_canvas import EditorCanvas, Tool
from src.models import AnnotationModel
from src.storage import (
    base64_png_to_pixmap,
    build_project_model,
    load_project,
    pixmap_to_base64_png,
    save_project,
)


class EditorWindow(QMainWindow):
    """
    Hosts the SnapAgent screenshot editor UI.
    """

    close_requested = Signal()

    def __init__(self, screenshot: QPixmap) -> None:
        """
        Initializes the editor with a screenshot image.

        Args:
            screenshot: Captured screenshot pixmap.
        """

        super().__init__()
        self.setWindowTitle(f"{APP_NAME} Editor")
        self.resize(1400, 900)
        self._current_project_path = ""
        self._recovery_path = f"{tempfile.gettempdir()}/snapagent-autosave{APP_FILE_EXTENSION}"
        self._minimize_to_tray_on_close = True

        self._record_history = True
        self._history: list[dict[str, Any]] = []
        self._history_index = -1

        container = QWidget(self)
        self.setCentralWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.canvas = EditorCanvas()
        self.canvas.set_screenshot(screenshot)
        self.canvas.content_changed.connect(self._on_canvas_changed)
        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        self.canvas.selection_style_changed.connect(self._on_selection_style_changed)
        self.canvas.crop_selection_changed.connect(self._on_crop_state_changed)

        self._toolbar_widget = self._build_toolbar()
        root.addWidget(self._toolbar_widget)
        root.addWidget(self.canvas)

        self.statusBar().showMessage("Ready")
        self._build_menu()
        self._push_history_state()
        self._autosave_timer = self.startTimer(30_000)
        self.setStyleSheet(
            "QMainWindow { background: #1f2430; color: #e7ecf2; }"
            "QMenuBar, QMenu, QStatusBar { background: #232938; color: #e7ecf2; }"
            "QToolButton, QPushButton { background: #2f3543; color: #e7ecf2; border: 1px solid #434d63; border-radius: 4px; padding: 4px 8px; }"
            "QToolButton:checked { background: #2f7dd1; border: 1px solid #2f7dd1; color: white; }"
            "QPushButton:hover, QToolButton:hover { background: #3a4357; }"
            "QSpinBox { background: #2f3543; border: 1px solid #434d63; border-radius: 4px; padding: 3px; }"
        )

    def _build_toolbar(self) -> QWidget:
        """
        Creates the slim top tool panel.

        Returns:
            QWidget: Toolbar container widget.
        """

        bar = QWidget(self)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self._tool_buttons: dict[str, QToolButton] = {}
        for tool_key, label in [
            (Tool.SELECT, "Select"),
            (Tool.RECT, "Rectangle"),
            (Tool.ELLIPSE, "Circle"),
            (Tool.LINE, "Line"),
            (Tool.ARROW, "Arrow"),
            (Tool.TEXT, "Text"),
            (Tool.CROP, "Crop"),
        ]:
            button = QToolButton()
            button.setText(label)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, t=tool_key: self._set_tool(t))
            layout.addWidget(button)
            self._tool_buttons[tool_key] = button
        self._tool_buttons[Tool.SELECT].setChecked(True)

        self.apply_crop_button = QPushButton("Apply Crop")
        self.apply_crop_button.setEnabled(False)
        self.apply_crop_button.clicked.connect(self.canvas.apply_pending_crop)
        layout.addWidget(self.apply_crop_button)

        self.stroke_button = QPushButton("Stroke")
        self.stroke_button.clicked.connect(self._choose_stroke_color)
        layout.addWidget(self.stroke_button)

        self.fill_button = QPushButton("Fill")
        self.fill_button.clicked.connect(self._choose_fill_color)
        layout.addWidget(self.fill_button)

        layout.addWidget(QLabel("Size"))
        self.stroke_size_spin = QSpinBox()
        self.stroke_size_spin.setRange(1, 32)
        self.stroke_size_spin.setValue(3)
        self.stroke_size_spin.valueChanged.connect(self._stroke_width_changed)
        layout.addWidget(self.stroke_size_spin)

        layout.addWidget(QLabel("Font"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 120)
        self.font_size_spin.setValue(16)
        self.font_size_spin.valueChanged.connect(self._font_size_changed)
        layout.addWidget(self.font_size_spin)

        self.zoom_label = QLabel("100%")
        layout.addWidget(self.zoom_label)

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 400)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(140)
        self.zoom_slider.setToolTip("Zoom: left smaller, right larger")
        self.zoom_slider.valueChanged.connect(self._zoom_slider_changed)
        layout.addWidget(self.zoom_slider)

        zoom_in = QPushButton("+")
        zoom_in.clicked.connect(self.canvas.zoom_in)
        layout.addWidget(zoom_in)
        zoom_out = QPushButton("-")
        zoom_out.clicked.connect(self.canvas.zoom_out)
        layout.addWidget(zoom_out)
        zoom_reset = QPushButton("Reset")
        zoom_reset.clicked.connect(self.canvas.reset_zoom)
        layout.addWidget(zoom_reset)

        layout.addStretch(1)
        return bar

    def _build_menu(self) -> None:
        """
        Builds application menus and actions.

        Returns:
            None
        """

        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        edit_menu = menu.addMenu("Edit")
        help_menu = menu.addMenu("Help")

        open_action = QAction("Open Project...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Save Project As...", self)
        save_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_action)

        save_action = QAction("Save Project", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        export_png = QAction("Export as PNG...", self)
        export_png.triggered.connect(lambda: self.export_image("PNG"))
        file_menu.addAction(export_png)

        export_jpg = QAction("Export as JPEG...", self)
        export_jpg.triggered.connect(lambda: self.export_image("JPG"))
        file_menu.addAction(export_jpg)

        export_pdf = QAction("Export as PDF...", self)
        export_pdf.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf)

        file_menu.addSeparator()

        print_action = QAction("Print...", self)
        print_action.setShortcut(QKeySequence.StandardKey.Print)
        print_action.triggered.connect(self.print_image)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        close_action = QAction("Close", self)
        close_action.setShortcut(QKeySequence.StandardKey.Close)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)
        edit_menu.addAction(self.redo_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(lambda: self.canvas.paste_from_clipboard())
        edit_menu.addAction(paste_action)

        copy_image_action = QAction("Copy Image", self)
        copy_image_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_image_action.triggered.connect(self.copy_current_image_to_clipboard)
        edit_menu.addAction(copy_image_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        shortcuts_action = QAction("Shortcuts & Manual", self)
        shortcuts_action.triggered.connect(self.show_manual)
        help_menu.addAction(shortcuts_action)

        self._update_undo_redo_actions()

    def _set_tool(self, tool: str) -> None:
        """
        Sets active tool and updates button selection state.

        Args:
            tool: Tool identifier.

        Returns:
            None
        """

        for key, button in self._tool_buttons.items():
            button.setChecked(key == tool)
        self.canvas.set_tool(tool)
        self.statusBar().showMessage(f"Tool: {tool}")

    def _choose_stroke_color(self) -> None:
        """
        Opens alpha-enabled color picker for stroke color.

        Returns:
            None
        """

        color = QColorDialog.getColor(
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel,
            parent=self,
            title="Select Stroke Color",
        )
        if color.isValid():
            self.canvas.set_style(stroke_color=color)
            self._push_history_state()

    def _choose_fill_color(self) -> None:
        """
        Opens alpha-enabled color picker for fill color.

        Returns:
            None
        """

        color = QColorDialog.getColor(
            options=QColorDialog.ColorDialogOption.ShowAlphaChannel,
            parent=self,
            title="Select Fill Color",
        )
        if color.isValid():
            self.canvas.set_style(fill_color=color)
            self._push_history_state()

    def _stroke_width_changed(self, value: int) -> None:
        """
        Updates active and selected item stroke width.

        Args:
            value: New stroke width.

        Returns:
            None
        """

        self.canvas.set_style(stroke_width=float(value))
        self._push_history_state()

    def _font_size_changed(self, value: int) -> None:
        """
        Updates active and selected text font size.

        Args:
            value: New font size in points.

        Returns:
            None
        """

        self.canvas.set_style(font_size=value)
        self._push_history_state()

    def _on_zoom_changed(self, zoom_factor: float) -> None:
        """
        Refreshes zoom status text.

        Args:
            zoom_factor: Current zoom factor.

        Returns:
            None
        """

        zoom_percent = int(zoom_factor * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(max(10, min(400, zoom_percent)))
        self.zoom_slider.blockSignals(False)

    def _zoom_slider_changed(self, value: int) -> None:
        """
        Applies absolute zoom from slider percentage value.

        Args:
            value: Slider zoom percentage.

        Returns:
            None
        """

        self.canvas.set_zoom_factor(float(value) / 100.0)

    def _on_canvas_changed(self) -> None:
        """
        Captures history state when canvas content changes.

        Returns:
            None
        """

        self._push_history_state()

    def _on_selection_style_changed(self, payload: dict[str, Any]) -> None:
        """
        Synchronizes toolbar controls to selected object style.

        Args:
            payload: Selected style payload.

        Returns:
            None
        """

        stroke_width = payload.get("stroke_width")
        if isinstance(stroke_width, (float, int)):
            self.stroke_size_spin.blockSignals(True)
            self.stroke_size_spin.setValue(max(1, int(stroke_width)))
            self.stroke_size_spin.blockSignals(False)
        font_size = payload.get("font_size")
        if isinstance(font_size, int):
            self.font_size_spin.blockSignals(True)
            self.font_size_spin.setValue(font_size)
            self.font_size_spin.blockSignals(False)

    def _on_crop_state_changed(self, is_active: bool) -> None:
        """
        Enables or disables crop apply button.

        Args:
            is_active: True when crop selection exists.

        Returns:
            None
        """

        self.apply_crop_button.setEnabled(is_active)

    def _serialize_state(self) -> dict[str, Any]:
        """
        Serializes complete editor state for undo history.

        Returns:
            dict[str, Any]: Snapshot payload.
        """

        return {
            "screenshot_png_base64": pixmap_to_base64_png(self.canvas.screenshot()),
            "annotations": [item.to_dict() for item in self.canvas.collect_annotations()],
        }

    def _restore_state(self, snapshot: dict[str, Any]) -> None:
        """
        Restores editor state from a history snapshot.

        Args:
            snapshot: Stored snapshot payload.

        Returns:
            None
        """

        screenshot = base64_png_to_pixmap(str(snapshot["screenshot_png_base64"]))
        annotations = [
            AnnotationModel.from_dict(item)
            for item in list(snapshot.get("annotations", []))
            if isinstance(item, dict)
        ]

        self._record_history = False
        self.canvas.set_screenshot(screenshot)
        self.canvas.load_annotations(annotations)
        self._record_history = True

    def _push_history_state(self) -> None:
        """
        Adds the current state to the undo history.

        Returns:
            None
        """

        if not self._record_history:
            return
        snapshot = self._serialize_state()
        if self._history and snapshot == self._history[self._history_index]:
            return
        self._history = self._history[: self._history_index + 1]
        self._history.append(snapshot)
        self._history_index += 1
        self._update_undo_redo_actions()

    def _update_undo_redo_actions(self) -> None:
        """
        Enables or disables undo and redo actions.

        Returns:
            None
        """

        self.undo_action.setEnabled(self._history_index > 0)
        self.redo_action.setEnabled(self._history_index < len(self._history) - 1)

    def undo(self) -> None:
        """
        Restores the previous history snapshot.

        Returns:
            None
        """

        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._restore_state(self._history[self._history_index])
        self._update_undo_redo_actions()

    def redo(self) -> None:
        """
        Restores the next history snapshot.

        Returns:
            None
        """

        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self._restore_state(self._history[self._history_index])
        self._update_undo_redo_actions()

    def save_project_as(self) -> None:
        """
        Saves current screenshot project to a SnapAgent file.

        Returns:
            None
        """

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "",
            f"{APP_NAME} Project (*{APP_FILE_EXTENSION})",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(APP_FILE_EXTENSION):
            file_path = f"{file_path}{APP_FILE_EXTENSION}"
        model = build_project_model(
            screenshot=self.canvas.screenshot(),
            annotation_models=self.canvas.collect_annotations(),
        )
        save_project(file_path, model)
        self._current_project_path = file_path
        self.statusBar().showMessage("Project saved")
        self._update_window_title()

    def save_project(self) -> None:
        """
        Saves project to current path or opens Save As.

        Returns:
            None
        """

        if not self._current_project_path:
            self.save_project_as()
            return
        model = build_project_model(
            screenshot=self.canvas.screenshot(),
            annotation_models=self.canvas.collect_annotations(),
        )
        save_project(self._current_project_path, model)
        self.statusBar().showMessage("Project saved")

    def open_project(self) -> None:
        """
        Loads a SnapAgent project from disk.

        Returns:
            None
        """

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            f"{APP_NAME} Project (*{APP_FILE_EXTENSION});;Legacy Project (*.lshot *.json)",
        )
        if not file_path:
            return
        model = load_project(file_path)
        self._record_history = False
        self.canvas.set_screenshot(base64_png_to_pixmap(model.screenshot_png_base64))
        self.canvas.load_annotations(model.annotations)
        self._record_history = True
        self._history.clear()
        self._history_index = -1
        self._push_history_state()
        self._current_project_path = file_path
        self._update_window_title()
        self.statusBar().showMessage("Project loaded")

    def export_image(self, fmt: str) -> None:
        """
        Exports composited image to PNG/JPG formats.

        Args:
            fmt: Target format (PNG/JPG).

        Returns:
            None
        """

        ext = fmt.lower()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export as {fmt}",
            "",
            f"{fmt} Files (*.{ext});;All Files (*)",
        )
        if not file_path:
            return
        if fmt == "PNG" and not file_path.lower().endswith(".png"):
            file_path = f"{file_path}.png"
        if fmt == "JPG" and not file_path.lower().endswith((".jpg", ".jpeg")):
            file_path = f"{file_path}.jpg"
        pixmap = self.canvas.export_composited_pixmap()
        pixmap.save(file_path, fmt)
        self.statusBar().showMessage(f"Exported {fmt}")

    def export_pdf(self) -> None:
        """
        Exports composited screenshot as a PDF page.

        Returns:
            None
        """

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export as PDF",
            "",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path = f"{file_path}.pdf"

        writer = QPdfWriter(file_path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Landscape)
        writer.setResolution(300)
        writer.setColorModel(QPagedPaintDevice.ColorModel.Rgb)

        pixmap = self.canvas.export_composited_pixmap()
        painter = QPainter(writer)
        page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
        scaled = pixmap.scaled(
            page_rect.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x_offset = int((page_rect.width() - scaled.width()) / 2)
        y_offset = int((page_rect.height() - scaled.height()) / 2)
        painter.drawPixmap(x_offset, y_offset, scaled)
        painter.end()
        self.statusBar().showMessage("Exported PDF")

    def print_image(self) -> None:
        """
        Opens a print dialog and prints composited image.

        Returns:
            None
        """

        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if not dialog.exec():
            return
        painter = QPainter(printer)
        pixmap = self.canvas.export_composited_pixmap()
        rect = painter.viewport()
        scaled = pixmap.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
        painter.drawPixmap(0, 0, scaled)
        painter.end()

    def copy_current_image_to_clipboard(self) -> None:
        """
        Copies current composited tab image into clipboard.

        Returns:
            None
        """

        pixmap = self.canvas.export_composited_pixmap()
        clipboard = QGuiApplication.clipboard()
        clipboard.setPixmap(pixmap)
        self.statusBar().showMessage("Image copied to clipboard")

    def show_about(self) -> None:
        """
        Displays About dialog information.

        Returns:
            None
        """

        QMessageBox.information(
            self,
            f"About {APP_NAME}",
            f"{APP_NAME}\n"
            f"Author: {ABOUT_AUTHOR}\n"
            f"Website: {ABOUT_WEBSITE}\n\n"
            "A Linux screenshot editor inspired by SnagIt.",
        )

    def show_manual(self) -> None:
        """
        Displays quick manual and shortcut list.

        Returns:
            None
        """

        QMessageBox.information(
            self,
            "Manual and Shortcuts",
            "How it works:\n"
            "1) Use the capture panel to create a screenshot.\n"
            "2) Annotate with tools in the top bar.\n"
            "3) Save project, export image, or print from File menu.\n\n"
            "Shortcuts:\n"
            "Ctrl+O: Open project\n"
            "Ctrl+S: Save project\n"
            "Ctrl+Shift+S: Save project as\n"
            "Ctrl+Z: Undo\n"
            "Ctrl+Y: Redo\n"
            "Ctrl+V: Paste text/image/image URL\n"
            "Enter: Apply crop selection\n"
            "Esc: Cancel crop selection\n"
            "Ctrl+P: Print\n"
            "Ctrl + Mouse Wheel: Zoom\n"
            "Esc: Cancel capture overlays",
        )

    def _update_window_title(self) -> None:
        """
        Updates title with current project file name.

        Returns:
            None
        """

        if not self._current_project_path:
            self.setWindowTitle(f"{APP_NAME} Editor")
            return
        self.setWindowTitle(f"{APP_NAME} Editor - {self._current_project_path}")

    def timerEvent(self, event) -> None:
        """
        Runs periodic auto-save every 30 seconds.

        Args:
            event: Timer event from Qt.

        Returns:
            None
        """

        if event.timerId() != self._autosave_timer:
            super().timerEvent(event)
            return

        if not self._current_project_path:
            target_path = self._recovery_path
        else:
            target_path = self._current_project_path
        model = build_project_model(
            screenshot=self.canvas.screenshot(),
            annotation_models=self.canvas.collect_annotations(),
        )
        save_project(target_path, model)

    def set_minimize_to_tray_on_close(self, enabled: bool) -> None:
        """
        Enables or disables close-to-tray behavior.

        Args:
            enabled: True to hide on close, False to close normally.

        Returns:
            None
        """

        self._minimize_to_tray_on_close = enabled

    def closeEvent(self, event) -> None:
        """
        Handles close button behavior for tray minimization.

        Args:
            event: Qt close event.

        Returns:
            None
        """

        if self._minimize_to_tray_on_close:
            self.close_requested.emit()
            event.ignore()
            return
        super().closeEvent(event)

