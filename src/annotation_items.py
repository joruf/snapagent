"""
Annotation item definitions and conversion helpers.
"""

from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from typing import cast

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
)

from src.models import AnnotationModel

ITEM_ROLE_TYPE = 1001


@dataclass(slots=True)
class StyleState:
    """
    Aggregates drawing style options used for new annotations.

    Attributes:
        stroke_color: Pen color.
        fill_color: Brush color.
        text_color: Text color.
        stroke_width: Pen thickness.
        font_size: Font size for text annotations.
        font_family: Font family for text annotations.
    """

    stroke_color: QColor
    fill_color: QColor
    text_color: QColor
    stroke_width: float
    font_size: int
    font_family: str


class ArrowItem(QGraphicsLineItem):
    """
    Draws a line with an arrow head at the end.
    """

    def paint(
        self,
        painter: QPainter,
        option,
        widget=None,
    ) -> None:
        """
        Paints the arrow with line and end-cap triangle.

        Args:
            painter: Painter used by Qt.
            option: Style option from Qt.
            widget: Optional target widget.

        Returns:
            None
        """

        super().paint(painter, option, widget)
        line = self.line()
        if line.length() < 1:
            return

        pen = self.pen()
        painter.setPen(pen)
        painter.setBrush(pen.color())

        angle = math.radians(line.angle())
        size = max(8.0, pen.widthF() * 3.0)
        p2 = line.p2()
        left = QPointF(
            p2.x() + size * math.cos(angle + math.radians(150)),
            p2.y() - size * math.sin(angle + math.radians(150)),
        )
        right = QPointF(
            p2.x() + size * math.cos(angle - math.radians(150)),
            p2.y() - size * math.sin(angle - math.radians(150)),
        )
        path = QPainterPath()
        path.moveTo(p2)
        path.lineTo(left)
        path.lineTo(right)
        path.closeSubpath()
        painter.drawPath(path)


def color_to_list(color: QColor) -> list[int]:
    """
    Converts QColor into RGBA integer components.

    Args:
        color: Source QColor.

    Returns:
        list[int]: [r, g, b, a] values.
    """

    return [color.red(), color.green(), color.blue(), color.alpha()]


def list_to_color(values: list[int]) -> QColor:
    """
    Converts RGBA list into QColor.

    Args:
        values: [r, g, b, a] values.

    Returns:
        QColor: Converted color.
    """

    if len(values) != 4:
        return QColor(255, 0, 0, 255)
    return QColor(values[0], values[1], values[2], values[3])


def create_pen(style: StyleState) -> QPen:
    """
    Creates a pen from current style.

    Args:
        style: Active style state.

    Returns:
        QPen: Configured pen.
    """

    pen = QPen(style.stroke_color, style.stroke_width)
    pen.setCosmetic(False)
    return pen


def configure_graphics_item(item: QGraphicsItem, annotation_type: str) -> None:
    """
    Applies generic selection flags and metadata to an item.

    Args:
        item: Graphics item to configure.
        annotation_type: Logical annotation type.

    Returns:
        None
    """

    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
    item.setData(ITEM_ROLE_TYPE, annotation_type)


def annotation_from_item(item: QGraphicsItem) -> AnnotationModel | None:
    """
    Converts a graphics item to a serializable annotation model.

    Args:
        item: Scene item.

    Returns:
        AnnotationModel | None: Serialized annotation or None if unsupported.
    """

    annotation_type = str(item.data(ITEM_ROLE_TYPE) or "")
    if annotation_type in {"rect", "ellipse"}:
        shape_item = cast(QGraphicsRectItem | QGraphicsEllipseItem, item)
        rect = shape_item.rect().translated(shape_item.pos())
        pen = shape_item.pen()
        brush = shape_item.brush()
        return AnnotationModel(
            annotation_type=annotation_type,
            x=rect.x(),
            y=rect.y(),
            width=rect.width(),
            height=rect.height(),
            stroke_rgba=color_to_list(pen.color()),
            fill_rgba=color_to_list(brush.color()),
            stroke_width=pen.widthF(),
        )

    if annotation_type in {"line", "arrow"}:
        line_item = cast(QGraphicsLineItem, item)
        line = line_item.line()
        pen = line_item.pen()
        return AnnotationModel(
            annotation_type=annotation_type,
            x=line.p1().x() + line_item.pos().x(),
            y=line.p1().y() + line_item.pos().y(),
            width=line.p2().x() - line.p1().x(),
            height=line.p2().y() - line.p1().y(),
            stroke_rgba=color_to_list(pen.color()),
            fill_rgba=[0, 0, 0, 0],
            stroke_width=pen.widthF(),
        )

    if annotation_type == "text":
        text_item = cast(QGraphicsTextItem, item)
        rect = text_item.boundingRect().translated(text_item.pos())
        color = text_item.defaultTextColor()
        return AnnotationModel(
            annotation_type=annotation_type,
            x=rect.x(),
            y=rect.y(),
            width=rect.width(),
            height=rect.height(),
            stroke_rgba=color_to_list(color),
            fill_rgba=[0, 0, 0, 0],
            stroke_width=1.0,
            text=text_item.toPlainText(),
            font_size=text_item.font().pointSize(),
            font_family=text_item.font().family(),
        )

    if annotation_type == "image":
        image_item = cast(QGraphicsPixmapItem, item)
        rect = image_item.boundingRect().translated(image_item.pos())
        return AnnotationModel(
            annotation_type=annotation_type,
            x=rect.x(),
            y=rect.y(),
            width=rect.width(),
            height=rect.height(),
            stroke_rgba=[0, 0, 0, 0],
            fill_rgba=[0, 0, 0, 0],
            stroke_width=0.0,
            payload={"image_png_base64": image_item.data(2001)},
        )

    return None


def add_annotation_to_scene(
    scene: QGraphicsScene,
    annotation: AnnotationModel,
) -> QGraphicsItem | None:
    """
    Recreates one annotation model as a scene item.

    Args:
        scene: Target graphics scene.
        annotation: Serialized annotation model.

    Returns:
        QGraphicsItem | None: Created item.
    """

    stroke = list_to_color(annotation.stroke_rgba)
    fill = list_to_color(annotation.fill_rgba)
    pen = QPen(stroke, annotation.stroke_width)
    rect = QRectF(annotation.x, annotation.y, annotation.width, annotation.height)

    if annotation.annotation_type == "rect":
        item = scene.addRect(rect, pen, fill)
        configure_graphics_item(item, "rect")
        return item
    if annotation.annotation_type == "ellipse":
        item = scene.addEllipse(rect, pen, fill)
        configure_graphics_item(item, "ellipse")
        return item
    if annotation.annotation_type == "line":
        item = scene.addLine(
            annotation.x,
            annotation.y,
            annotation.x + annotation.width,
            annotation.y + annotation.height,
            pen,
        )
        configure_graphics_item(item, "line")
        return item
    if annotation.annotation_type == "arrow":
        item = ArrowItem(
            annotation.x,
            annotation.y,
            annotation.x + annotation.width,
            annotation.y + annotation.height,
        )
        item.setPen(pen)
        configure_graphics_item(item, "arrow")
        scene.addItem(item)
        return item
    if annotation.annotation_type == "text":
        item = scene.addText(annotation.text)
        font = QFont(item.font())
        font.setPointSize(annotation.font_size)
        if annotation.font_family:
            font.setFamily(annotation.font_family)
        item.setFont(font)
        item.setDefaultTextColor(stroke)
        item.setPos(annotation.x, annotation.y)
        configure_graphics_item(item, "text")
        item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        return item
    if annotation.annotation_type == "image":
        encoded = str(annotation.payload.get("image_png_base64", ""))
        if not encoded:
            return None
        item = QGraphicsPixmapItem(_decode_base64_to_pixmap(encoded))
        item.setPos(annotation.x, annotation.y)
        item.setScale(
            1.0 if item.pixmap().width() == 0 else annotation.width / item.pixmap().width()
        )
        configure_graphics_item(item, "image")
        item.setData(2001, encoded)
        scene.addItem(item)
        return item

    return None


def _decode_base64_to_pixmap(value: str) -> QPixmap:
    """
    Decodes Base64 PNG data to QPixmap.

    Args:
        value: Base64 encoded PNG bytes.

    Returns:
        QPixmap: Decoded pixmap.
    """

    data = base64.b64decode(value.encode("utf-8"))
    image = QImage()
    image.loadFromData(data, "PNG")
    return QPixmap.fromImage(image)

