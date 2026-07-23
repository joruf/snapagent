"""
Raster export helpers for Snappix (SVG wrappers around composited pixmaps).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QSize
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgGenerator


def write_pixmap_as_svg(pixmap: QPixmap, path: str | Path) -> bool:
    """
    Writes one composited pixmap as a standard SVG file.

    Uses Qt's SVG generator so the result is a normal SVG document that embeds
    the raster screenshot (not a reconstructed vector scene).

    Args:
        pixmap: Source composited image.
        path: Destination ``.svg`` file path.

    Returns:
        bool: True when the SVG file was written successfully.
    """

    if pixmap.isNull():
        return False

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    width = max(1, int(pixmap.width()))
    height = max(1, int(pixmap.height()))

    generator = QSvgGenerator()
    generator.setFileName(str(target))
    generator.setSize(QSize(width, height))
    generator.setViewBox(QRect(0, 0, width, height))
    generator.setTitle("Snappix export")
    generator.setDescription("Composited screenshot exported as SVG")

    painter = QPainter(generator)
    if not painter.isActive():
        return False
    try:
        painter.drawPixmap(0, 0, pixmap)
    finally:
        painter.end()

    try:
        return target.is_file() and target.stat().st_size > 0
    except OSError:
        return False
