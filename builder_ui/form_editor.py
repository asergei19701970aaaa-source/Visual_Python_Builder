from __future__ import annotations

from .common import *

from .canvas import CanvasView, GraphScene, NodeItem


def _form_menu_titles(properties: dict[str, Any]) -> list[str]:
    raw = properties.get("menus", [])
    if isinstance(raw, str):
        try:
            raw = json.loads(raw or "[]")
        except (TypeError, ValueError, json.JSONDecodeError):
            raw = []
    if not isinstance(raw, list):
        return []
    return [
        str(item.get("title") or item.get("name") or "")
        for item in raw if isinstance(item, dict)
        and str(item.get("title") or item.get("name") or "")
    ]


class FormWindowItem(QGraphicsRectItem):
    TITLE_HEIGHT = 34
    MIN_WIDTH = 240
    MIN_HEIGHT = 160
    MENU_HEIGHT = 24

    def __init__(self, model: dict[str, Any]):
        props = model.setdefault("properties", {})
        width = int(props.get("width", 640))
        height = int(props.get("height", 420))
        super().__init__(0, 0, width, height + 34)
        self.model = model
        self.resizing = False
        self.setPos(50, 50)
        self.setZValue(0)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True
        )
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
            True,
        )
        self.setAcceptHoverEvents(True)

    def menu_height(self) -> int:
        return self.MENU_HEIGHT if _form_menu_titles(
            self.model.get("properties", {})
        ) else 0

    def _near_handle(self, point: QPointF) -> bool:
        rect = self.rect()
        return (
            point.x() >= rect.right() - 14
            and point.y() >= rect.bottom() - 14
        )

    def hoverMoveEvent(self, event):
        self.setCursor(
            Qt.CursorShape.SizeFDiagCursor
            if self._near_handle(event.pos())
            else Qt.CursorShape.ArrowCursor
        )
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._near_handle(event.pos())
        ):
            self.resizing = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            width = max(self.MIN_WIDTH, int(event.pos().x()))
            height = max(
                self.MIN_HEIGHT,
                int(event.pos().y()) - self.TITLE_HEIGHT,
            )
            self.setRect(
                0, 0, width, height + self.TITLE_HEIGHT
            )
            props = self.model.setdefault("properties", {})
            props["width"] = width
            props["height"] = height
            scene = self.scene()
            if isinstance(scene, FormScene):
                scene.changed_model.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        settings = menu.addAction("Настройки сетки…")
        fit = menu.addAction("Показать форму целиком")
        reset_zoom = menu.addAction("Масштаб 100%")
        selected = menu.exec(event.screenPos())
        scene = self.scene()
        if not isinstance(scene, FormScene):
            return
        if selected == settings:
            scene.form_action_requested.emit("grid_settings")
        elif selected == fit:
            scene.form_action_requested.emit("fit")
        elif selected == reset_zoom:
            scene.form_action_requested.emit("reset_zoom")

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor("#B9B8B5"), 1.3))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRect(rect)
        painter.setBrush(QColor("#F0EFED"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(
            QRectF(
                rect.left(), rect.top(),
                rect.width(), self.TITLE_HEIGHT,
            )
        )
        scene = self.scene()
        if isinstance(scene, FormScene) and scene.show_grid:
            painter.setPen(QPen(QColor("#ECEBE9"), 1))
            step = max(2, scene.snap_size)
            content_top = rect.top() + self.TITLE_HEIGHT + self.menu_height()
            x = rect.left() + step
            while x < rect.right():
                painter.drawLine(
                    QPointF(x, content_top),
                    QPointF(x, rect.bottom()),
                )
                x += step
            y = content_top + step
            while y < rect.bottom():
                painter.drawLine(
                    QPointF(rect.left(), y),
                    QPointF(rect.right(), y),
                )
                y += step
        painter.setPen(QColor("#2C2C2B"))
        painter.drawText(
            QRectF(
                rect.left() + 12, rect.top(),
                rect.width() - 24, self.TITLE_HEIGHT,
            ),
            Qt.AlignmentFlag.AlignVCenter,
            str(
                self.model.get("properties", {}).get(
                    "title", "Моя программа"
                )
            ),
        )
        menu_titles = _form_menu_titles(self.model.get("properties", {}))
        if menu_titles:
            menu_rect = QRectF(
                rect.left(), rect.top() + self.TITLE_HEIGHT,
                rect.width(), self.MENU_HEIGHT,
            )
            painter.fillRect(menu_rect, QColor("#F8F8F8"))
            painter.setPen(QPen(QColor("#D4D4D4"), 1))
            painter.drawLine(menu_rect.bottomLeft(), menu_rect.bottomRight())
            painter.setPen(QColor("#2C2C2B"))
            x = menu_rect.left() + 9
            for title in menu_titles:
                width = max(42, painter.fontMetrics().horizontalAdvance(title) + 18)
                painter.drawText(
                    QRectF(x, menu_rect.top(), width, menu_rect.height()),
                    Qt.AlignmentFlag.AlignCenter,
                    title,
                )
                x += width
        painter.setBrush(QColor("#2783DE"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(
            QRectF(rect.right() - 8, rect.bottom() - 8, 8, 8)
        )


class FormControlItem(QGraphicsRectItem):
    MIN_WIDTH = 32
    MIN_HEIGHT = 20

    @staticmethod
    def _content_top_offset(parent: QGraphicsItem) -> int:
        if isinstance(parent, FormWindowItem):
            return FormWindowItem.TITLE_HEIGHT + parent.menu_height()
        if (
            isinstance(parent, FormControlItem)
            and parent.model.get("properties", {}).get("_qt_class")
            == "QMdiSubWindow"
        ):
            return 24
        return 0

    def __init__(self, model: dict[str, Any], parent: QGraphicsItem):
        props = model.setdefault("properties", {})
        width = int(property_value(props, "width", "Width", default=120))
        height = int(property_value(props, "height", "Height", default=32))
        super().__init__(0, 0, width, height, parent)
        self.model = model
        self.resizing = False
        top_offset = self._content_top_offset(parent)
        self.setPos(
            int(property_value(props, "x", "Left", default=0)),
            int(property_value(props, "y", "Top", default=0)) + top_offset,
        )
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setZValue(float(model.get("z", 2)))

    def _near_handle(self, point: QPointF) -> bool:
        rect = self.rect()
        return (
            point.x() >= rect.right() - 11
            and point.y() >= rect.bottom() - 11
        )

    def hoverMoveEvent(self, event):
        self.setCursor(
            Qt.CursorShape.SizeFDiagCursor
            if self._near_handle(event.pos())
            else Qt.CursorShape.SizeAllCursor
        )
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._near_handle(
            event.pos()
        ):
            self.resizing = True
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            width = max(self.MIN_WIDTH, int(event.pos().x()))
            height = max(self.MIN_HEIGHT, int(event.pos().y()))
            self.setRect(0, 0, width, height)
            props = self.model.setdefault("properties", {})
            set_property_value(props, width, "width", "Width")
            set_property_value(props, height, "height", "Height")
            scene = self.scene()
            if isinstance(scene, FormScene):
                scene.changed_model.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)
        scene = self.scene()
        if isinstance(scene, FormScene):
            scene.reparent_control(self)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.scene()
            if isinstance(scene, FormScene) and scene.snap_enabled:
                step = scene.snap_size
                return QPointF(
                    round(value.x() / step) * step,
                    round(value.y() / step) * step,
                )
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            props = self.model.setdefault("properties", {})
            top_offset = self._content_top_offset(self.parentItem())
            set_property_value(
                props, max(0, round(value.x())), "x", "Left"
            )
            set_property_value(
                props, max(0, round(value.y() - top_offset)), "y", "Top"
            )
            scene = self.scene()
            if isinstance(scene, FormScene):
                scene.changed_model.emit()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        scene = self.scene()
        if self.model.get("type") == "DashboardCanvas" and isinstance(scene, FormScene):
            scene.node_action_requested.emit(str(self.model["id"]), "canvas_designer")
            event.accept(); return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        duplicate = menu.addAction("Дублировать")
        delete = menu.addAction("Удалить")
        menu.addSeparator()
        front = menu.addAction("На передний план")
        back = menu.addAction("На задний план")
        menu.addSeparator()
        properties = menu.addAction("Показать свойства")
        canvas_designer = menu.addAction("Открыть мышиный редактор Canvas…")
        canvas_designer.setVisible(self.model.get("type") == "DashboardCanvas")
        selected = menu.exec(event.screenPos())
        scene = self.scene()
        if not isinstance(scene, FormScene):
            return
        actions = {
            duplicate: "duplicate",
            delete: "delete",
            front: "front",
            back: "back",
            properties: "properties",
            canvas_designer: "canvas_designer",
        }
        action = actions.get(selected)
        if action:
            scene.node_action_requested.emit(
                str(self.model["id"]), action
            )

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        node_type = self.model["type"]
        props = self.model.get("properties", {})
        text = str(
            property_value(
                props, "text", "Text", "Caption", "String", default=""
            )
        )
        painter.setPen(QPen(QColor("#B8B7B4"), 1))
        painter.setBrush(QColor("#FFFFFF"))

        if node_type == "Button":
            painter.setBrush(QColor("#F0EFED"))
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        elif node_type == "Label":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(
                rect.adjusted(4, 0, -4, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
        elif node_type in {"LineEdit", "TextEdit"}:
            painter.drawRoundedRect(rect, 5, 5)
            shown = text or str(props.get("placeholder", ""))
            painter.setPen(QColor("#2C2C2B" if text else "#9A9894"))
            painter.drawText(
                rect.adjusted(7, 4, -7, -4),
                (
                    Qt.AlignmentFlag.AlignLeft
                    | (
                        Qt.AlignmentFlag.AlignTop
                        if node_type == "TextEdit"
                        else Qt.AlignmentFlag.AlignVCenter
                    )
                ),
                shown,
            )
        elif node_type == "CheckBox":
            painter.setPen(QPen(QColor("#9A9894"), 1))
            painter.drawRoundedRect(QRectF(3, (rect.height() - 15) / 2, 15, 15), 3, 3)
            if props.get("checked"):
                painter.setPen(QPen(QColor("#2783DE"), 2))
                painter.drawLine(
                    QPointF(6, rect.height() / 2),
                    QPointF(10, rect.height() / 2 + 4),
                )
                painter.drawLine(
                    QPointF(10, rect.height() / 2 + 4),
                    QPointF(16, rect.height() / 2 - 4),
                )
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(
                rect.adjusted(25, 0, 0, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
        elif node_type == "ComboBox":
            painter.drawRoundedRect(rect, 5, 5)
            first = str(props.get("items", "")).split("|")[0]
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(
                rect.adjusted(7, 0, -25, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                first,
            )
            painter.drawText(
                QRectF(rect.right() - 24, rect.top(), 24, rect.height()),
                Qt.AlignmentFlag.AlignCenter,
                "▾",
            )
        elif node_type == "ListWidget":
            painter.drawRect(rect)
            items = str(props.get("items", "")).split("|")
            y = rect.top() + 5
            painter.setPen(QColor("#2C2C2B"))
            for item in items[:6]:
                painter.drawText(
                    QRectF(rect.left() + 5, y, rect.width() - 10, 18),
                    Qt.AlignmentFlag.AlignLeft
                    | Qt.AlignmentFlag.AlignVCenter,
                    item,
                )
                y += 19
        elif node_type == "ProgressBar":
            painter.drawRect(rect)
            minimum = float(props.get("minimum", 0) or 0)
            maximum = max(minimum + 1.0, float(props.get("maximum", 100) or 100))
            value = float(props.get("value", 0) or 0)
            ratio = max(0.0, min(1.0, (value - minimum) / (maximum - minimum)))
            inverted = bool(props.get("inverted_appearance", False))
            vertical = str(props.get("orientation", "Horizontal")) == "Vertical"
            if vertical:
                fill_ratio = 1.0 - ratio if inverted else ratio
                fill_height = rect.height() * fill_ratio
                fill_rect = (
                    QRectF(rect.left(), rect.top(), rect.width(), fill_height)
                    if inverted
                    else QRectF(
                        rect.left(), rect.bottom() - fill_height,
                        rect.width(), fill_height,
                    )
                )
            else:
                fill_ratio = 1.0 - ratio if inverted else ratio
                fill_width = rect.width() * fill_ratio
                fill_rect = (
                    QRectF(rect.right() - fill_width, rect.top(), fill_width, rect.height())
                    if inverted
                    else QRectF(rect.left(), rect.top(), fill_width, rect.height())
                )
            painter.fillRect(fill_rect, QColor("#7AA7C7"))
            if props.get("text_visible", props.get("show_text", True)):
                painter.setPen(QColor("#202020"))
                shown = int(value) if value.is_integer() else value
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{shown}")
        elif node_type == "Slider":
            minimum = float(props.get("minimum", 0) or 0)
            maximum = float(props.get("maximum", 100) or 100)
            value = float(props.get("value", minimum) or 0)
            ratio = max(0.0, min(1.0, (value - minimum) / max(1.0, maximum - minimum)))
            inverted = bool(props.get("inverted_appearance", False))
            vertical = str(props.get("orientation", "Horizontal")) == "Vertical"
            painter.setPen(QPen(QColor("#888888"), 2))
            if vertical:
                # Qt places a vertical slider's minimum at the bottom.
                position_ratio = ratio if not inverted else 1.0 - ratio
                y = rect.bottom() - 8 - position_ratio * max(1.0, rect.height() - 16)
                painter.drawLine(
                    QPointF(rect.center().x(), rect.top() + 8),
                    QPointF(rect.center().x(), rect.bottom() - 8),
                )
                painter.setBrush(QColor("#2783DE"))
                painter.drawRoundedRect(
                    QRectF(rect.center().x() - 9, y - 5, 18, 10), 2, 2
                )
            else:
                position_ratio = 1.0 - ratio if inverted else ratio
                x = rect.left() + 8 + position_ratio * max(1.0, rect.width() - 16)
                painter.drawLine(
                    QPointF(rect.left() + 8, rect.center().y()),
                    QPointF(rect.right() - 8, rect.center().y()),
                )
                painter.setBrush(QColor("#2783DE"))
                painter.drawRoundedRect(
                    QRectF(x - 5, rect.center().y() - 9, 10, 18), 2, 2
                )
        elif node_type == "SpinBox":
            painter.drawRect(rect)
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(
                rect.adjusted(6, 0, -24, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(props.get("value", 0)),
            )
            painter.drawText(
                QRectF(rect.right() - 22, rect.top(), 22, rect.height()),
                Qt.AlignmentFlag.AlignCenter,
                "▲\n▼",
            )

        elif node_type == "TableWidget":
            painter.drawRect(rect)
            headers = str(props.get("columns", "")).split("|")
            count = max(1, len(headers))
            cell_w = rect.width() / count
            painter.fillRect(QRectF(rect.left(), rect.top(), rect.width(), 24), QColor("#E8E8E8"))
            painter.setPen(QColor("#777777"))
            for index, header in enumerate(headers):
                x = rect.left() + index * cell_w
                painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
                painter.drawText(QRectF(x + 3, rect.top(), cell_w - 6, 24), Qt.AlignmentFlag.AlignVCenter, header)
            for y in range(int(rect.top()) + 24, int(rect.bottom()), 22):
                painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
        elif node_type == "TableView":
            # A Designer QTableView has no embedded rows or columns.  Do not
            # invent sample headers: an empty model is rendered as an empty
            # white view, exactly as in Qt Designer.
            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(QPen(QColor("#7E858A"), 1))
            painter.drawRect(rect)
        elif node_type == "TreeWidget":
            painter.drawRect(rect)
            painter.fillRect(QRectF(rect.left(), rect.top(), rect.width(), 24), QColor("#E8E8E8"))
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(rect.adjusted(5, 0, -5, 0), Qt.AlignmentFlag.AlignTop, str(props.get("header", "Элементы")))
            y = rect.top() + 29
            for item in str(props.get("items", "")).split("|")[:6]:
                painter.drawText(QRectF(rect.left() + 10, y, rect.width() - 15, 18), Qt.AlignmentFlag.AlignVCenter, "› " + item)
                y += 19
        elif node_type == "DateEdit":
            painter.drawRect(rect)
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(rect.adjusted(6, 0, -24, 0), Qt.AlignmentFlag.AlignVCenter, str(props.get("date", "")))
            painter.drawText(QRectF(rect.right() - 24, rect.top(), 24, rect.height()), Qt.AlignmentFlag.AlignCenter, "▾")
        elif node_type == "Calendar":
            painter.drawRect(rect)
            painter.fillRect(QRectF(rect.left(), rect.top(), rect.width(), 28), QColor("#E8E8E8"))
            painter.setPen(QColor("#2C2C2B"))
            painter.drawText(QRectF(rect.left(), rect.top(), rect.width(), 28), Qt.AlignmentFlag.AlignCenter, str(props.get("date", "Календарь")))
            painter.drawText(rect.adjusted(8, 36, -8, -8), Qt.AlignmentFlag.AlignCenter, "Пн  Вт  Ср  Чт  Пт  Сб  Вс")
        elif node_type == "LCDNumber":
            painter.setBrush(QColor("#202522"))
            painter.drawRect(rect)
            painter.setPen(QColor("#8AF58A"))
            painter.drawText(rect.adjusted(5, 2, -5, -2), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(props.get("value", 0)))
        elif node_type in {"RadioButton","ToolButton","CommandLinkButton"}:
            painter.setBrush(QColor("#F0EFED")); painter.drawRoundedRect(rect,6,6); painter.setPen(QColor("#2C2C2B")); painter.drawText(rect.adjusted(8,2,-8,-2),Qt.AlignmentFlag.AlignCenter,text or str(props.get("description","Кнопка")))
        elif node_type == "GroupBox":
            painter.setBrush(QColor("#FAFAFA")); painter.drawRoundedRect(rect,5,5); painter.setPen(QColor("#4A4A4A")); painter.drawText(rect.adjusted(9,2,-6,-3),Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignLeft,str(props.get("title","Группа")))
        elif node_type in {"PlainTextEdit","TextBrowser"}:
            painter.setBrush(QColor("#FFFFFF")); painter.drawRect(rect); shown=str(props.get("text",props.get("html",props.get("placeholder","")))); painter.setPen(QColor("#333333")); painter.drawText(rect.adjusted(7,6,-7,-6),Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop,shown[:500])
        elif node_type in {"Dial"}:
            painter.setBrush(QColor("#E6E8EA")); painter.drawEllipse(rect.adjusted(4,4,-4,-4)); painter.setPen(QPen(QColor("#2783DE"),3)); painter.drawLine(rect.center(),QPointF(rect.center().x()+rect.width()*.25,rect.center().y()-rect.height()*.25))
        elif node_type in {"DoubleSpinBox","TimeEdit","DateTimeEdit","KeySequenceEdit"}:
            painter.setBrush(QColor("#FFFFFF")); painter.drawRect(rect); value=props.get("value",props.get("time",props.get("datetime",props.get("sequence","")))); painter.setPen(QColor("#2C2C2B")); painter.drawText(rect.adjusted(7,0,-24,0),Qt.AlignmentFlag.AlignVCenter,str(value)); painter.drawText(QRectF(rect.right()-22,rect.top(),22,rect.height()),Qt.AlignmentFlag.AlignCenter,"▲\n▼")
        elif node_type in {"ScrollBar"}:
            painter.setBrush(QColor("#E5E7E9"))
            painter.drawRoundedRect(rect, 4, 4)
            ratio = max(0, min(1, (
                float(props.get("value", 0)) - float(props.get("minimum", 0))
            ) / max(1, float(props.get("maximum", 100)) - float(props.get("minimum", 0)))))
            painter.setBrush(QColor("#7AA7C7"))
            if str(props.get("orientation", "Horizontal")) == "Vertical":
                y = rect.top() + 6 + ratio * max(1, rect.height() - 24)
                painter.drawRoundedRect(
                    QRectF(rect.left() + 3, y, rect.width() - 6, 16), 3, 3
                )
            else:
                x = rect.left() + 6 + ratio * max(1, rect.width() - 24)
                painter.drawRoundedRect(
                    QRectF(x, rect.top() + 3, 16, rect.height() - 6), 3, 3
                )
        elif node_type == "FontComboBox":
            painter.setBrush(QColor("#FFFFFF")); painter.drawRect(rect); painter.setPen(QColor("#2C2C2B")); painter.drawText(rect.adjusted(7,0,-22,0),Qt.AlignmentFlag.AlignVCenter,str(props.get("family","Segoe UI"))); painter.drawText(QRectF(rect.right()-22,rect.top(),22,rect.height()),Qt.AlignmentFlag.AlignCenter,"▾")
        elif node_type == "DialogButtonBox":
            names = [
                item.strip()
                for item in str(props.get("buttons", "Ok|Cancel")).split("|")
                if item.strip()
            ] or ["Ok", "Cancel"]
            captions = {
                "Ok": "ОК", "Cancel": "Отмена", "Save": "Сохранить",
                "SaveAll": "Сохранить всё", "Open": "Открыть",
                "Yes": "Да", "YesToAll": "Да для всех", "No": "Нет",
                "NoToAll": "Нет для всех", "Abort": "Прервать",
                "Retry": "Повторить", "Ignore": "Пропустить",
                "Close": "Закрыть", "Discard": "Не сохранять",
                "Help": "Справка", "Apply": "Применить",
                "Reset": "Сбросить", "RestoreDefaults": "По умолчанию",
            }
            vertical = str(props.get("orientation", "Horizontal")) == "Vertical"
            gap = 6.0
            if vertical:
                button_h = max(18.0, (rect.height() - gap * (len(names) - 1)) / len(names))
                boxes = [
                    QRectF(rect.left(), rect.top() + index * (button_h + gap), rect.width(), button_h)
                    for index in range(len(names))
                ]
            else:
                button_w = max(34.0, (rect.width() - gap * (len(names) - 1)) / len(names))
                boxes = [
                    QRectF(rect.left() + index * (button_w + gap), rect.top(), button_w, rect.height())
                    for index in range(len(names))
                ]
            painter.setPen(QPen(QColor("#9A9894"), 1))
            painter.setBrush(QColor("#F0EFED"))
            for name, box in zip(names, boxes):
                painter.drawRoundedRect(box, 4, 4)
                painter.setPen(QColor("#2C2C2B"))
                painter.drawText(box.adjusted(4, 0, -4, 0), Qt.AlignmentFlag.AlignCenter, captions.get(name, name))
                painter.setPen(QPen(QColor("#9A9894"), 1))
        elif node_type in {"Frame","HorizontalLine"}:
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(QColor("#7E858A"),max(1,int(props.get("line_width",1)))));
            if node_type=="HorizontalLine":
                if bool(props.get("vertical", False)):
                    painter.drawLine(
                        QPointF(rect.center().x(), rect.top()),
                        QPointF(rect.center().x(), rect.bottom()),
                    )
                else:
                    painter.drawLine(
                        QPointF(rect.left(), rect.center().y()),
                        QPointF(rect.right(), rect.center().y()),
                    )
            elif props.get("_qt_class") == "QMdiArea":
                painter.setBrush(QColor("#B8BEC5"))
                painter.drawRect(rect)
                painter.setBrush(QColor("#E8EBEE"))
                painter.drawRect(rect.adjusted(5, 5, -5, -5))
            elif props.get("_qt_class") == "QMdiSubWindow":
                painter.setBrush(QColor("#FFFFFF"))
                painter.drawRect(rect)
                painter.setBrush(QColor("#DCE8F4"))
                painter.drawRect(QRectF(rect.left(), rect.top(), rect.width(), 24))
                painter.setPen(QColor("#183B63"))
                painter.drawText(
                    QRectF(rect.left() + 8, rect.top(), rect.width() - 16, 24),
                    Qt.AlignmentFlag.AlignVCenter,
                    str(props.get("mdi_title", props.get("title", "Дочернее окно"))),
                )
            elif str(props.get("shape", "StyledPanel")) == "VLine":
                painter.drawLine(
                    QPointF(rect.center().x(), rect.top()),
                    QPointF(rect.center().x(), rect.bottom()),
                )
            elif str(props.get("shape", "StyledPanel")) == "HLine":
                painter.drawLine(
                    QPointF(rect.left(), rect.center().y()),
                    QPointF(rect.right(), rect.center().y()),
                )
            elif str(props.get("shape", "StyledPanel")) != "NoFrame":
                painter.drawRect(rect)
        elif node_type in {"Gauge","Speedometer","Tachometer","Knob"}:
            bg=QColor(str(props.get("background_color","#101820"))); primary=QColor(str(props.get("primary_color","#35C2FF"))); needle=QColor(str(props.get("needle_color","#FF5252"))); painter.setBrush(bg); painter.drawRoundedRect(rect,8,8); side=min(rect.width(),rect.height())*.62; c=rect.center(); box=QRectF(c.x()-side/2,c.y()-side/2,side,side); mn=float(props.get("minimum",0)); mx=max(mn+1,float(props.get("maximum",100))); ratio=max(0,min(1,(float(props.get("value",0))-mn)/(mx-mn))); painter.setPen(QPen(QColor("#26364A"),max(5,int(side*.08)))); painter.drawArc(box,225*16,-270*16); painter.setPen(QPen(primary,max(5,int(side*.08)))); painter.drawArc(box,225*16,int(-270*16*ratio)); a=math.radians(225-270*ratio); painter.setPen(QPen(needle,3)); painter.drawLine(c,QPointF(c.x()+math.cos(a)*side*.34,c.y()-math.sin(a)*side*.34)); painter.setPen(QColor("#F4F7FB")); painter.drawText(rect.adjusted(5,4,-5,-5),Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter,str(props.get("title",node_type)))
        elif node_type in {"Thermometer","LevelMeter"}:
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); mn=float(props.get("minimum",0)); mx=max(mn+1,float(props.get("maximum",100))); ratio=max(0,min(1,(float(props.get("value",0))-mn)/(mx-mn))); box=rect.adjusted(rect.width()*.32,32,-rect.width()*.32,-28); painter.fillRect(box,QColor("#26364A")); fill=QRectF(box.left(),box.bottom()-box.height()*ratio,box.width(),box.height()*ratio); painter.fillRect(fill,QColor(str(props.get("primary_color","#35C2FF")))); painter.setPen(QColor("#F4F7FB")); painter.drawText(rect.adjusted(4,4,-4,-4),Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter,str(props.get("title",node_type)))
        elif node_type == "LEDIndicator":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); color=QColor(str(props.get("alarm_color","#FF3B30")) if float(props.get("value",0))>=float(props.get("critical",90)) else str(props.get("primary_color","#35C2FF"))); radius=min(rect.width(),rect.height())*.24; painter.setBrush(color); painter.setPen(QPen(color.lighter(160),3)); painter.drawEllipse(rect.center(),radius,radius); painter.setPen(QColor("#F4F7FB")); painter.drawText(rect.adjusted(4,4,-4,-4),Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter,str(props.get("title","Светодиод")))
        elif node_type == "Compass":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); side=min(rect.width(),rect.height())*.6; c=rect.center(); painter.setPen(QPen(QColor("#F4F7FB"),2)); painter.drawEllipse(c,side/2,side/2); angle=math.radians(90-float(props.get("value",0))); painter.setPen(QPen(QColor(str(props.get("needle_color","#FF5252"))),4)); painter.drawLine(c,QPointF(c.x()+math.cos(angle)*side*.4,c.y()-math.sin(angle)*side*.4))
        elif node_type == "BatteryIndicator":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); box=rect.adjusted(18,rect.height()*.32,-28,-rect.height()*.32); painter.setPen(QPen(QColor("#F4F7FB"),2)); painter.drawRect(box); ratio=max(0,min(1,float(props.get("value",0))/max(1,float(props.get("maximum",100))))); inner=box.adjusted(4,4,-4,-4); inner.setWidth(inner.width()*ratio); painter.fillRect(inner,QColor(str(props.get("primary_color","#35C2FF"))))
        elif node_type in {"SignalIndicator","VUMeter"}:
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); ratio=max(0,min(1,float(props.get("value",0))/max(1,float(props.get("maximum",100))))); bars=8 if node_type=="VUMeter" else 5; w=(rect.width()-24)/bars;
            for i in range(bars):
                h=(i+1)*(rect.height()-45)/bars; painter.fillRect(QRectF(rect.left()+10+i*w,rect.bottom()-18-h,w-3,h),QColor(str(props.get("primary_color","#35C2FF"))) if ratio>i/bars else QColor("#26364A"))
        elif node_type in {"Sparkline","LineChart","Oscilloscope"}:
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); box=rect.adjusted(10,28,-10,-20); painter.setPen(QPen(QColor("#29445A"),1));
            for i in range(1,4): painter.drawLine(QPointF(box.left(),box.top()+box.height()*i/4),QPointF(box.right(),box.top()+box.height()*i/4))
            val=float(props.get("value",0)); pts=[QPointF(box.left()+i*box.width()/7,box.center().y()+math.sin(i*.9+val*.05)*box.height()*.28) for i in range(8)]; painter.setPen(QPen(QColor(str(props.get("primary_color","#35C2FF"))),2)); painter.drawPolyline(QPolygonF(pts))
        elif node_type == "BarChart":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); box=rect.adjusted(12,30,-12,-20); vals=(.35,.7,.5,.9,.62); w=box.width()/len(vals); painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor(str(props.get("primary_color","#35C2FF"))));
            for i,v in enumerate(vals): painter.drawRect(QRectF(box.left()+i*w+3,box.bottom()-box.height()*v,w-6,box.height()*v))
        elif node_type == "PieChart":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); side=min(rect.width(),rect.height())*.62; c=rect.center(); box=QRectF(c.x()-side/2,c.y()-side/2,side,side); painter.setBrush(QColor("#26364A")); painter.drawEllipse(box); ratio=max(0,min(1,float(props.get("value",0))/max(1,float(props.get("maximum",100))))); painter.setBrush(QColor(str(props.get("primary_color","#35C2FF")))); painter.drawPie(box,90*16,int(-360*16*ratio))
        elif node_type == "RadarChart":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); c=rect.center(); radius=min(rect.width(),rect.height())*.32; pts=[]; painter.setPen(QPen(QColor("#52667A"),1));
            for i in range(6):
                a=-math.pi/2+2*math.pi*i/6; tip=QPointF(c.x()+math.cos(a)*radius,c.y()+math.sin(a)*radius); painter.drawLine(c,tip); pts.append(QPointF(c.x()+math.cos(a)*radius*(.45+(i%3)*.2),c.y()+math.sin(a)*radius*(.45+(i%3)*.2)))
            painter.setPen(QPen(QColor(str(props.get("primary_color","#35C2FF"))),2)); painter.drawPolygon(QPolygonF(pts))
        elif node_type == "SevenSegmentDisplay":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); font=painter.font(); font.setFamily("Consolas"); font.setBold(True); font.setPixelSize(max(16,int(rect.height()*.38))); painter.setFont(font); painter.setPen(QColor(str(props.get("primary_color","#35C2FF")))); painter.drawText(rect,Qt.AlignmentFlag.AlignCenter,str(props.get("value",0)))
        elif node_type == "LEDMatrix":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); rows,cols=5,8; seed=int(float(props.get("value",0))); size=min(rect.width()/cols,rect.height()/rows)*.55;
            for yy in range(rows):
                for xx in range(cols):
                    on=((seed>>(xx%8))&1) if yy in (1,2,3) else ((xx+yy+seed)%5==0); center=QPointF(rect.left()+(xx+.5)*rect.width()/cols,rect.top()+(yy+.5)*rect.height()/rows); painter.setBrush(QColor(str(props.get("primary_color","#35C2FF"))) if on else QColor("#26364A")); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(center,size/2,size/2)
        elif node_type in {"XYPlot","HeatMap","Timeline","WaterfallChart","GeoMap","Waveform","SpectrumAnalyzer","MultiSegmentDisplay","CustomInstrument"}:
            bg=QColor(str(props.get("background_color","#101820"))); primary=QColor(str(props.get("primary_color","#35C2FF"))); secondary=QColor(str(props.get("secondary_color","#26364A"))); painter.setBrush(bg); painter.setPen(QPen(QColor(str(props.get("border_color","#52667A"))),2)); painter.drawRoundedRect(rect,8,8); box=rect.adjusted(10,28,-10,-20); painter.setPen(QPen(secondary,1));
            for ii in range(1,4): painter.drawLine(QPointF(box.left(),box.top()+box.height()*ii/4),QPointF(box.right(),box.top()+box.height()*ii/4))
            if node_type=="HeatMap":
                for yy in range(5):
                    for xx in range(8): painter.fillRect(QRectF(box.left()+xx*box.width()/8,box.top()+yy*box.height()/5,box.width()/8+.5,box.height()/5+.5),QColor.fromHsvF(.66*(1-((xx*13+yy*9)%100)/100),.8,.85))
            elif node_type in {"SpectrumAnalyzer","WaterfallChart"}:
                for ii in range(16):
                    level=.15+.8*abs(math.sin(ii*.55+float(props.get("value",0))*.03)); painter.fillRect(QRectF(box.left()+ii*box.width()/16+1,box.bottom()-box.height()*level,box.width()/16-2,box.height()*level),primary)
            elif node_type in {"MultiSegmentDisplay","CustomInstrument"}:
                font=painter.font(); font.setFamily("Consolas"); font.setBold(True); font.setPixelSize(max(16,int(rect.height()*.28))); painter.setFont(font); painter.setPen(primary); painter.drawText(box,Qt.AlignmentFlag.AlignCenter,str(props.get("value",0)))
            elif node_type=="GeoMap":
                painter.setBrush(QColor("#18334A")); painter.drawRect(box); painter.setBrush(QColor("#FF5252")); painter.setPen(QPen(QColor("#FFFFFF"),1)); painter.drawEllipse(box.center(),5,5)
            else:
                pts=[QPointF(box.left()+ii*box.width()/11,box.center().y()+math.sin(ii*.75+float(props.get("value",0))*.04)*box.height()*.3) for ii in range(12)]; painter.setPen(QPen(primary,2)); painter.drawPolyline(QPolygonF(pts))
            painter.setPen(QColor(str(props.get("text_color","#F4F7FB")))); painter.drawText(rect.adjusted(5,3,-5,-3),Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter,str(props.get("title",node_type)))
        elif node_type == "DashboardCanvas":
            painter.fillRect(rect,QColor(str(props.get("background_color","#101820")))); grid=QColor(str(props.get("grid_color","#26364A"))); step=max(8,int(props.get("grid_size",20))); painter.setPen(QPen(grid,1,Qt.PenStyle.DotLine))
            if props.get("show_grid",True):
                for xx in range(int(rect.left()),int(rect.right())+step,step): painter.drawLine(QPointF(xx,rect.top()),QPointF(xx,rect.bottom()))
                for yy in range(int(rect.top()),int(rect.bottom())+step,step): painter.drawLine(QPointF(rect.left(),yy),QPointF(rect.right(),yy))
            try: scene=json.loads(str(props.get("scene","[]")))
            except Exception: scene=[]
            for item in sorted(scene,key=lambda v:int(v.get("layer",0)) if isinstance(v,dict) else 0):
                if not isinstance(item,dict): continue
                kind=str(item.get("type","rect")).lower(); x=rect.left()+float(item.get("x",0)); y=rect.top()+float(item.get("y",0)); w=float(item.get("w",80)); h=float(item.get("h",50)); color=QColor(str(item.get("color","#35C2FF"))); box=QRectF(x,y,w,h); painter.setPen(QPen(color.lighter(140),2)); painter.setBrush(color)
                if kind in {"ellipse","circle"}: painter.drawEllipse(box)
                elif kind=="line": painter.drawLine(box.topLeft(),box.bottomRight())
                elif kind=="text": painter.setPen(color); painter.drawText(box,Qt.AlignmentFlag.AlignCenter,str(item.get("text","")))
                else: painter.drawRoundedRect(box,5,5); painter.setPen(QColor("#FFFFFF")); painter.drawText(box,Qt.AlignmentFlag.AlignCenter,str(item.get("text","")))
        elif node_type == "GridCanvas":
            painter.fillRect(rect, QColor(str(props.get("background_color", "#101820"))))
            columns = max(1, int(props.get("columns", 10)))
            rows = max(1, int(props.get("rows", 20)))
            try:
                initial = json.loads(str(props.get("initial_grid", "") or "[]"))
            except Exception:
                initial = []
            if isinstance(initial, list) and initial:
                rows = len(initial)
                columns = max(
                    (len(row) for row in initial if isinstance(row, list)),
                    default=columns,
                )
            palette = {}
            try:
                palette = json.loads(str(props.get("palette", "{}") or "{}"))
            except Exception:
                palette = {}
            cell = min(rect.width() / columns, rect.height() / rows)
            left = rect.left() + (rect.width() - columns * cell) / 2
            top = rect.top() + (rect.height() - rows * cell) / 2
            empty = str(props.get("empty_value", "0"))
            fallback = ("#35C2FF", "#FFB020", "#59FF88", "#FF5FA2")
            for row_index in range(rows):
                values = initial[row_index] if row_index < len(initial) and isinstance(initial[row_index], list) else []
                for column_index in range(columns):
                    value = values[column_index] if column_index < len(values) else empty
                    color = str(props.get("background_color", "#101820"))
                    if str(value) != empty:
                        color = str(palette.get(str(value), fallback[(column_index + row_index) % len(fallback)]))
                    box = QRectF(left + column_index * cell, top + row_index * cell, cell, cell)
                    painter.fillRect(box, QColor(color))
                    if props.get("show_grid", True):
                        painter.setPen(QPen(QColor(str(props.get("grid_color", "#26364A"))), 1))
                        painter.drawRect(box)
        elif node_type == "AnalogClock":
            painter.setBrush(QColor(str(props.get("background_color","#101820")))); painter.drawRoundedRect(rect,8,8); c=rect.center(); side=min(rect.width(),rect.height())*.62; painter.setPen(QPen(QColor("#F4F7FB"),2)); painter.drawEllipse(c,side/2,side/2); painter.drawLine(c,QPointF(c.x(),c.y()-side*.28)); painter.setPen(QPen(QColor(str(props.get("needle_color","#FF5252"))),2)); painter.drawLine(c,QPointF(c.x()+side*.24,c.y()))
        elif node_type.startswith("Delphi::"):
            original = node_type.split("::", 1)[1].lower()
            caption = text or COMPONENTS[node_type].caption
            painter.setFont(
                to_qfont(property_value(props, "Font", default="Arial,8"))
            )
            base_color = to_qcolor(
                property_value(props, "Color", default="#F0F0F0"),
                "#F0F0F0",
            )
            if (
                "led" in original
                and "ladder" not in original
                and "number" not in original
            ):
                state = bool(
                    property_value(
                        props, "Value", "State", "Checked",
                        default=False,
                    )
                )
                color = to_qcolor(
                    property_value(
                        props,
                        "ColorOn" if state else "ColorOff",
                        default="#33D05A" if state else "#59615B",
                    ),
                    "#33D05A" if state else "#59615B",
                )
                diameter = max(
                    8, min(rect.width(), rect.height()) - 6
                )
                circle = QRectF(
                    rect.center().x() - diameter / 2,
                    rect.center().y() - diameter / 2,
                    diameter,
                    diameter,
                )
                painter.setPen(QPen(QColor("#303532"), 1.5))
                painter.setBrush(color)
                painter.drawEllipse(circle)
                painter.setPen(QPen(QColor(255, 255, 255, 130), 2))
                painter.drawArc(
                    circle.adjusted(3, 3, -3, -3),
                    35 * 16,
                    70 * 16,
                )
            elif any(token in original for token in ("button", "bitbtn", "imgbtn")):
                painter.setBrush(base_color)
                painter.drawRoundedRect(rect, 5, 5)
                painter.setPen(QColor("#2C2C2B"))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, caption)
            elif "label" in original:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QColor("#2C2C2B"))
                painter.drawText(
                    rect.adjusted(4, 0, -4, 0),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    caption,
                )
            elif any(token in original for token in ("edit", "memo", "richedit")):
                painter.setBrush(base_color)
                painter.drawRect(rect)
                painter.setPen(QColor("#2C2C2B"))
                painter.drawText(
                    rect.adjusted(6, 3, -6, -3),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                    caption,
                )
            elif any(token in original for token in ("checkbox", "radiobutton")):
                painter.drawRect(
                    QRectF(3, max(2, (rect.height() - 14) / 2), 14, 14)
                )
                painter.setPen(QColor("#2C2C2B"))
                painter.drawText(
                    rect.adjusted(23, 0, 0, 0),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    caption,
                )
            elif any(token in original for token in ("progress", "trackbar", "scrollbar")):
                painter.setBrush(base_color)
                painter.drawRect(rect)
                painter.fillRect(
                    QRectF(
                        rect.left(), rect.top(),
                        max(3, rect.width() * 0.45), rect.height()
                    ),
                    to_qcolor(
                        property_value(
                            props, "ProgressColor", default="#7AA7C7"
                        ),
                        "#7AA7C7",
                    ),
                )
            elif any(
                token in original
                for token in ("gauge", "dial", "grapher")
            ):
                painter.setBrush(QColor("#202522"))
                painter.drawEllipse(rect)
                painter.setPen(QPen(QColor("#75D8FF"), 2))
                painter.drawLine(
                    rect.center(),
                    QPointF(rect.right() - 8, rect.center().y() - 8),
                )
            elif any(
                token in original
                for token in (
                    "panel", "groupbox", "scrollbox",
                    "pagecontrol", "tabcontrol",
                )
            ):
                painter.setBrush(
                    to_qcolor(property_value(props, "Color", default="#F0F0F0"))
                )
                painter.setPen(QPen(QColor("#7E858A"), 1))
                painter.drawRect(rect)
                painter.setPen(QColor("#2C2C2B"))
                painter.drawText(
                    rect.adjusted(7, 3, -7, -3),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                    caption,
                )
            elif any(
                token in original
                for token in ("image", "paintbox", "shape", "picture")
            ):
                painter.setBrush(base_color)
                painter.drawRect(rect)
                painter.setPen(QPen(QColor("#8A949C"), 1))
                painter.drawLine(rect.topLeft(), rect.bottomRight())
                painter.drawLine(rect.topRight(), rect.bottomLeft())
            else:
                painter.setBrush(base_color)
                painter.drawRect(rect)
                painter.setPen(QColor("#504A58"))
                painter.drawText(
                    rect.adjusted(5, 3, -5, -3),
                    Qt.AlignmentFlag.AlignCenter,
                    caption,
                )

        if self.isSelected():
            painter.setPen(QPen(QColor("#2783DE"), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)
            painter.setBrush(QColor("#2783DE"))
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            painter.drawRect(
                QRectF(rect.right() - 7, rect.bottom() - 7, 8, 8)
            )


class FormScene(QGraphicsScene):
    node_selected = Signal(object)
    changed_model = Signal()
    node_action_requested = Signal(str, str)
    form_action_requested = Signal(str)

    VISUAL_TYPES = {
        "Button",
        "Label",
        "LineEdit",
        "TextEdit",
        "CheckBox",
        "ComboBox",
        "ListWidget",
        "ProgressBar",
        "Slider",
        "SpinBox",
        "TableWidget",
        "TableView",
        "TreeWidget",
        "DateEdit",
        "Calendar",
        "LCDNumber",
        "RadioButton", "GroupBox", "Dial", "ToolButton", "PlainTextEdit",
        "DoubleSpinBox", "ScrollBar", "TimeEdit", "DateTimeEdit", "TextBrowser",
        "FontComboBox", "KeySequenceEdit", "CommandLinkButton", "DialogButtonBox", "Frame", "HorizontalLine",
        "Gauge", "Speedometer", "Tachometer", "Thermometer", "LevelMeter", "LEDIndicator",
        "Compass", "BatteryIndicator", "SignalIndicator", "Sparkline", "AnalogClock", "Knob",
        "LineChart", "BarChart", "PieChart", "RadarChart", "Oscilloscope", "VUMeter",
        "SevenSegmentDisplay", "LEDMatrix",
        "XYPlot", "HeatMap", "Timeline", "WaterfallChart", "GeoMap",
        "Waveform", "SpectrumAnalyzer", "MultiSegmentDisplay", "CustomInstrument", "DashboardCanvas", "GridCanvas",
    }

    def __init__(self):
        super().__init__()
        self.setSceneRect(-300, -300, 3600, 3000)
        self.setBackgroundBrush(QColor("#DEDEDC"))
        self.window_item: FormWindowItem | None = None
        self.controls: dict[str, FormControlItem] = {}
        self.graph_scene: GraphScene | None = None
        self.snap_enabled = True
        self.snap_size = 5
        self.show_grid = True
        self.selectionChanged.connect(self._selection_changed)

    def rebuild(self, graph_scene: GraphScene):
        self.graph_scene = graph_scene
        selected_id = None
        selected = [
            item for item in self.selectedItems() if isinstance(item, FormControlItem)
        ]
        if selected:
            selected_id = selected[0].model["id"]
        self.blockSignals(True)
        self.clear()
        self.controls = {}
        form_node = next(
            (
                item.model
                for item in graph_scene.nodes.values()
                if item.model["type"] == "Form"
            ),
            None,
        )
        if form_node is None:
            form_node = {
                "id": "_preview_form",
                "type": "Form",
                "properties": default_properties("Form"),
            }
        self.window_item = FormWindowItem(form_node)
        self.addItem(self.window_item)
        pending = [
            node.model for node in graph_scene.nodes.values()
            if is_visual_type(node.model["type"])
        ]
        # Parents are created before children. Broken/cyclic parent links are
        # safely repaired by falling back to the form.
        while pending:
            progress = False
            for model in list(pending):
                parent_id = model.get("parent_id")
                if parent_id and parent_id not in self.controls:
                    continue
                parent = self.controls.get(parent_id, self.window_item)
                control = FormControlItem(model, parent)
                self.controls[model["id"]] = control
                pending.remove(model)
                progress = True
                if model["id"] == selected_id:
                    control.setSelected(True)
            if not progress:
                for model in pending:
                    model.pop("parent_id", None)
                    self.controls[model["id"]] = FormControlItem(
                        model, self.window_item
                    )
                break
        self.blockSignals(False)
        # The scene follows the real form size and leaves navigation margins.
        bounds = self.itemsBoundingRect()
        width = max(2200.0, bounds.right() + 500.0)
        height = max(1600.0, bounds.bottom() + 500.0)
        self.setSceneRect(-300.0, -300.0, width + 300.0, height + 300.0)

    def container_at(
        self, scene_position: QPointF, exclude_id: str | None = None
    ) -> FormControlItem | None:
        candidates = []
        for item in self.controls.values():
            if item.model["id"] == exclude_id:
                continue
            spec = COMPONENTS[item.model["type"]]
            if not is_visual_container(spec):
                continue
            if item.sceneBoundingRect().contains(scene_position):
                candidates.append(item)
        return min(
            candidates,
            key=lambda item: item.sceneBoundingRect().width()
            * item.sceneBoundingRect().height(),
            default=None,
        )

    def reparent_control(self, item: FormControlItem):
        if self.window_item is None:
            return
        scene_pos = item.scenePos()
        target = self.container_at(
            item.sceneBoundingRect().center(), item.model["id"]
        )
        # Never make an item a child of one of its descendants.
        probe = target
        while probe is not None:
            if probe is item:
                target = None
                break
            probe = (
                probe.parentItem()
                if isinstance(probe.parentItem(), FormControlItem) else None
            )
        new_parent: QGraphicsItem = target or self.window_item
        if item.parentItem() is new_parent:
            return
        local = new_parent.mapFromScene(scene_pos)
        item.setParentItem(new_parent)
        item.setPos(local)
        if target is None:
            item.model.pop("parent_id", None)
            y = local.y() - FormWindowItem.TITLE_HEIGHT
        else:
            item.model["parent_id"] = target.model["id"]
            y = local.y()
        props = item.model.setdefault("properties", {})
        set_property_value(props, max(0, round(local.x())), "x", "Left")
        set_property_value(props, max(0, round(y)), "y", "Top")
        self.changed_model.emit()

    def _selection_changed(self):
        selected = [
            item for item in self.selectedItems() if isinstance(item, FormControlItem)
        ]
        if selected:
            self.node_selected.emit(selected[0].model)
            return
        form_selected = next(
            (
                item
                for item in self.selectedItems()
                if isinstance(item, FormWindowItem)
            ),
            None,
        )
        self.node_selected.emit(
            form_selected.model if form_selected else None
        )

    def contextMenuEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform()) if self.views() else None
        if isinstance(item, (FormControlItem, FormWindowItem)):
            super().contextMenuEvent(event)
            return
        menu = QMenu()
        grid = menu.addAction("Настройки сетки…")
        fit = menu.addAction("Показать всё")
        reset_zoom = menu.addAction("Масштаб 100%")
        selected = menu.exec(event.screenPos())
        if selected == grid:
            self.form_action_requested.emit("grid_settings")
        elif selected == fit:
            self.form_action_requested.emit("fit")
        elif selected == reset_zoom:
            self.form_action_requested.emit("reset_zoom")


class DashboardDesignerScene(QGraphicsScene):
    """Полный редактор Canvas: история, группы, направляющие и анимация."""
    GRID = 20
    HANDLE = 7
    history_changed = Signal(bool, bool)

    def __init__(self):
        super().__init__(-200, -200, 2200, 1600)
        self.tool = "select"
        self.color = "#35C2FF"
        self.text_value = "Текст"
        self.snap_enabled = True
        self.guides_enabled = True
        self._start = None
        self._draft = None
        self._resize = None
        self._gesture_before = None
        self._guide_lines = []
        self._selection_guard = False
        self._restoring = False
        self._undo = []
        self._redo = []
        self._style_clipboard = None
        self.setBackgroundBrush(QColor("#101820"))
        self.selectionChanged.connect(self._selection_changed)

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#101820"))
        painter.setPen(QPen(QColor("#26364A"), 1, Qt.PenStyle.DotLine))
        step = self.GRID
        x = int(rect.left()) - int(rect.left()) % step
        while x < rect.right():
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            x += step
        y = int(rect.top()) - int(rect.top()) % step
        while y < rect.bottom():
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            y += step

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if self.guides_enabled and self._guide_lines:
            painter.setPen(QPen(QColor("#FF4FD8"), 1, Qt.PenStyle.DashLine))
            for first, second in self._guide_lines:
                painter.drawLine(first, second)
        selected = self.selectedItems()
        if len(selected) != 1 or bool(selected[0].data(7)):
            return
        box = selected[0].sceneBoundingRect()
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.setBrush(QColor("#2783DE"))
        for point in self._handle_points(box).values():
            painter.drawRect(QRectF(
                point.x() - self.HANDLE, point.y() - self.HANDLE,
                self.HANDLE * 2, self.HANDLE * 2,
            ))

    def _snapshot(self):
        return copy.deepcopy(self.to_data())

    def _emit_history(self):
        self.history_changed.emit(len(self._undo) > 1, bool(self._redo))

    def _commit(self):
        if self._restoring:
            return
        value = self._snapshot()
        if not self._undo:
            self._undo = [value]
        elif value != self._undo[-1]:
            self._undo.append(value)
            self._undo = self._undo[-100:]
            self._redo.clear()
        self._emit_history()

    def undo(self):
        if len(self._undo) < 2:
            return
        self._redo.append(self._undo.pop())
        self._restore(self._undo[-1])
        self._emit_history()

    def redo(self):
        if not self._redo:
            return
        value = self._redo.pop()
        self._undo.append(copy.deepcopy(value))
        self._restore(value)
        self._emit_history()

    def _restore(self, value):
        self._restoring = True
        try:
            self.load_data(value, reset_history=False)
        finally:
            self._restoring = False

    def _handle_points(self, box):
        return {
            "tl": box.topLeft(), "tr": box.topRight(),
            "bl": box.bottomLeft(), "br": box.bottomRight(),
        }

    def _handle_at(self, point):
        selected = self.selectedItems()
        if len(selected) != 1 or bool(selected[0].data(7)):
            return None
        for name, center in self._handle_points(
                selected[0].sceneBoundingRect()).items():
            if QRectF(center.x() - self.HANDLE * 1.5,
                      center.y() - self.HANDLE * 1.5,
                      self.HANDLE * 3, self.HANDLE * 3).contains(point):
                return name
        return None

    def _snap(self, value):
        return round(value / self.GRID) * self.GRID if self.snap_enabled else value

    def _snap_point(self, point):
        return QPointF(self._snap(point.x()), self._snap(point.y()))

    def set_tool(self, tool):
        self.tool = tool

    def set_snap(self, enabled):
        self.snap_enabled = bool(enabled)

    def set_guides(self, enabled):
        self.guides_enabled = bool(enabled)
        if not enabled:
            self._guide_lines = []
        self.update()

    def _apply_lock_flags(self, item, locked=False):
        flags = (QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                 | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        if not locked:
            flags |= QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        item.setFlags(flags)
        item.setData(7, bool(locked))

    def _flags(self, item, locked=False):
        self._apply_lock_flags(item, locked)
        item.setData(0, self.tool)
        item.setData(1, self.color)
        item.setData(2, self.text_value)
        item.setZValue(max([i.zValue() for i in self.items()] or [0]) + 1)
        return item

    def _path(self, kind, w, h):
        path = QPainterPath(); path.moveTo(0, 0); path.lineTo(w, h)
        if kind == "arrow":
            angle = math.atan2(h, w); size = 13
            path.moveTo(w, h)
            path.lineTo(w-size*math.cos(angle-.55), h-size*math.sin(angle-.55))
            path.moveTo(w, h)
            path.lineTo(w-size*math.cos(angle+.55), h-size*math.sin(angle+.55))
        return path

    def create_item(self, kind, x, y, w, h, text="", color=None,
                    rotation=0, layer=None, item_id=None, group="",
                    locked=False, animation=None, font_size=14):
        previous = self.tool, self.color, self.text_value
        self.tool = kind; self.color = color or self.color
        self.text_value = text or self.text_value
        if kind == "ellipse":
            item = QGraphicsEllipseItem(0, 0, max(2, w), max(2, h))
        elif kind in {"line", "arrow"}:
            item = QGraphicsPathItem(self._path(kind, w, h))
            item.setData(3, float(w)); item.setData(4, float(h))
        elif kind == "text":
            item = QGraphicsSimpleTextItem(text or "Текст")
            font = item.font(); font.setPointSize(max(6, int(font_size))); item.setFont(font)
        else:
            item = QGraphicsRectItem(0, 0, max(2, w), max(2, h))
        if kind != "text":
            item.setPen(QPen(QColor(self.color).lighter(140), 2))
        if kind not in {"line", "arrow", "text"}:
            item.setBrush(QColor(self.color))
        if kind == "text":
            item.setBrush(QColor(self.color))
        self._flags(item, locked)
        item.setData(5, str(item_id or uuid.uuid4().hex[:12]))
        item.setData(6, str(group or ""))
        item.setData(8, dict(animation or {}))
        item.setPos(x, y); item.setRotation(rotation)
        if layer is not None:
            item.setZValue(float(layer))
        self.addItem(item)
        self.tool, self.color, self.text_value = previous
        return item

    def load_data(self, data, reset_history=True):
        self.clear()
        for value in data:
            if not isinstance(value, dict):
                continue
            self.create_item(
                str(value.get("type", "rect")),
                float(value.get("x", 0)), float(value.get("y", 0)),
                float(value.get("w", 80)), float(value.get("h", 50)),
                str(value.get("text", "")), str(value.get("color", "#35C2FF")),
                float(value.get("rotation", 0)), int(value.get("layer", 0)),
                value.get("id"), value.get("group", ""),
                bool(value.get("locked", False)), value.get("animation") or {},
                int(value.get("font_size", 14)),
            )
        self.tool = "select"
        if reset_history:
            self._undo = [self._snapshot()]
            self._redo = []
            self._emit_history()

    def _item_data(self, item):
        kind = str(item.data(0) or "rect"); scale = float(item.scale())
        text = str(item.data(2) or ""); color = str(item.data(1) or "#35C2FF")
        if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)):
            w, h = item.rect().width() * scale, item.rect().height() * scale
        elif isinstance(item, QGraphicsPathItem):
            w = float(item.data(3) or item.boundingRect().width()) * scale
            h = float(item.data(4) or item.boundingRect().height()) * scale
        else:
            w, h = item.boundingRect().width() * scale, item.boundingRect().height() * scale
            text = item.text()
        font_size = item.font().pointSize() if isinstance(item, QGraphicsSimpleTextItem) else 14
        return {
            "id": str(item.data(5) or uuid.uuid4().hex[:12]),
            "type": kind, "x": round(item.pos().x(), 1),
            "y": round(item.pos().y(), 1), "w": round(w, 1),
            "h": round(h, 1), "text": text, "color": color,
            "rotation": round(item.rotation(), 1), "layer": int(item.zValue()),
            "group": str(item.data(6) or ""), "locked": bool(item.data(7)),
            "animation": dict(item.data(8) or {}), "font_size": int(font_size),
        }

    def to_data(self):
        drawable = (QGraphicsRectItem, QGraphicsEllipseItem,
                    QGraphicsPathItem, QGraphicsSimpleTextItem)
        return [self._item_data(item) for item in
                sorted((i for i in self.items() if isinstance(i, drawable)),
                       key=lambda value: value.zValue())]

    def _selection_changed(self):
        if self._selection_guard:
            self.update(); return
        groups = {str(item.data(6) or "") for item in self.selectedItems()}
        groups.discard("")
        if groups:
            self._selection_guard = True
            try:
                for item in self.items():
                    if str(item.data(6) or "") in groups:
                        item.setSelected(True)
            finally:
                self._selection_guard = False
        self.update()

    def _begin_resize(self, handle, point):
        item = self.selectedItems()[0]; box = item.sceneBoundingRect()
        opposite = {"tl": box.bottomRight(), "tr": box.bottomLeft(),
                    "bl": box.topRight(), "br": box.topLeft()}[handle]
        self._resize = {"item": item, "handle": handle, "opposite": opposite,
                        "box": QRectF(box), "scale": float(item.scale())}

    def _resize_selected(self, point):
        state = self._resize
        if not state: return
        item, old, opposite = state["item"], state["box"], state["opposite"]
        width = max(4.0, abs(point.x() - opposite.x()))
        height = max(4.0, abs(point.y() - opposite.y()))
        ratio = max(width/max(1.0, old.width()), height/max(1.0, old.height()))
        item.setScale(max(.1, min(10.0, state["scale"] * ratio)))
        current = item.sceneBoundingRect()
        anchor = {"tl": current.bottomRight(), "tr": current.bottomLeft(),
                  "bl": current.topRight(), "br": current.topLeft()}[state["handle"]]
        item.setPos(item.pos() + (opposite - anchor)); self.update()

    def _update_guides(self):
        self._guide_lines = []
        if not self.guides_enabled or not self.selectedItems(): return
        moving = self.selectedItems()[0]; box = moving.sceneBoundingRect(); threshold = 5
        mine_x = (box.left(), box.center().x(), box.right())
        mine_y = (box.top(), box.center().y(), box.bottom())
        for other in self.items():
            if other in self.selectedItems(): continue
            target = other.sceneBoundingRect()
            for a in mine_x:
                for b in (target.left(), target.center().x(), target.right()):
                    if abs(a-b) <= threshold:
                        self._guide_lines.append((QPointF(b, self.sceneRect().top()), QPointF(b, self.sceneRect().bottom())))
            for a in mine_y:
                for b in (target.top(), target.center().y(), target.bottom()):
                    if abs(a-b) <= threshold:
                        self._guide_lines.append((QPointF(self.sceneRect().left(), b), QPointF(self.sceneRect().right(), b)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._gesture_before = self._snapshot()
        if self.tool == "select" and event.button() == Qt.MouseButton.LeftButton:
            handle = self._handle_at(event.scenePos())
            if handle:
                self._begin_resize(handle, event.scenePos()); event.accept(); return
            return super().mousePressEvent(event)
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        self._start = self._snap_point(event.scenePos())
        if self.tool == "text":
            self._draft = self.create_item("text", self._start.x(), self._start.y(),
                                           120, 30, self.text_value)
            self._start = None; event.accept(); return
        self._draft = self.create_item(self.tool, self._start.x(), self._start.y(),
                                       2, 2, self.text_value); event.accept()

    def mouseMoveEvent(self, event):
        if self._resize is not None:
            self._resize_selected(self._snap_point(event.scenePos())); event.accept(); return
        if self._start is None or self._draft is None:
            super().mouseMoveEvent(event)
            if (self.snap_enabled and self.tool == "select"
                    and event.buttons() & Qt.MouseButton.LeftButton):
                for item in self.selectedItems():
                    if not bool(item.data(7)): item.setPos(self._snap_point(item.pos()))
            if event.buttons() & Qt.MouseButton.LeftButton: self._update_guides()
            self.update(); return
        end = self._snap_point(event.scenePos())
        x, y = min(self._start.x(), end.x()), min(self._start.y(), end.y())
        w, h = max(2, abs(end.x()-self._start.x())), max(2, abs(end.y()-self._start.y()))
        self._draft.setPos(x, y)
        if isinstance(self._draft, (QGraphicsRectItem, QGraphicsEllipseItem)):
            self._draft.setRect(0, 0, w, h)
        elif isinstance(self._draft, QGraphicsPathItem):
            sx = 1 if end.x() >= self._start.x() else -1
            sy = 1 if end.y() >= self._start.y() else -1
            self._draft.setPath(self._path(str(self._draft.data(0)), w*sx, h*sy))
            self._draft.setData(3, w*sx); self._draft.setData(4, h*sy)
            self._draft.setPos(self._start)
        event.accept()

    def mouseReleaseEvent(self, event):
        handled = self._resize is not None or self._draft is not None
        if self._resize is not None: self._resize = None
        if self._draft is not None:
            self._draft.setSelected(True); self._draft = None; self._start = None
        if not handled: super().mouseReleaseEvent(event)
        self._guide_lines = []; self._commit(); self.update(); event.accept()

    def keyPressEvent(self, event):
        ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        if ctrl and event.key() == Qt.Key.Key_Z:
            self.redo() if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else self.undo(); event.accept(); return
        if ctrl and event.key() == Qt.Key.Key_Y:
            self.redo(); event.accept(); return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected(); event.accept(); return
        if ctrl and event.key() == Qt.Key.Key_D:
            self.duplicate_selected(); event.accept(); return
        moves = {Qt.Key.Key_Left: (-1, 0), Qt.Key.Key_Right: (1, 0),
                 Qt.Key.Key_Up: (0, -1), Qt.Key.Key_Down: (0, 1)}
        if event.key() in moves:
            dx, dy = moves[event.key()]
            step = self.GRID if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 1
            for item in self.selectedItems():
                if not bool(item.data(7)): item.moveBy(dx*step, dy*step)
            self.update(); self._commit(); event.accept(); return
        super().keyPressEvent(event)

    def delete_selected(self):
        for item in list(self.selectedItems()):
            if not bool(item.data(7)): self.removeItem(item)
        self._commit()

    def duplicate_selected(self):
        values = [self._item_data(item) for item in self.selectedItems()]
        self.clearSelection(); group_map = {}
        for value in values:
            value["x"] += self.GRID; value["y"] += self.GRID; value["id"] = None
            if value["group"]:
                group_map.setdefault(value["group"], uuid.uuid4().hex[:10])
                value["group"] = group_map[value["group"]]
            clone = self.create_item(
                value["type"], value["x"], value["y"], value["w"], value["h"],
                value["text"], value["color"], value["rotation"], value["layer"]+1,
                None, value["group"], False, value["animation"], value["font_size"])
            clone.setSelected(True)
        self._commit()

    def group_selected(self):
        items = self.selectedItems()
        if len(items) < 2: return
        group = uuid.uuid4().hex[:10]
        for item in items: item.setData(6, group)
        self._commit(); self.update()

    def ungroup_selected(self):
        for item in self.selectedItems(): item.setData(6, "")
        self._commit(); self.update()

    def set_locked(self, locked):
        for item in self.selectedItems():
            item.setData(7, bool(locked)); self._apply_lock_flags(item, bool(locked))
        self._commit(); self.update()

    def copy_style(self):
        items = self.selectedItems()
        if not items: return
        item = items[0]
        self._style_clipboard = {
            "color": str(item.data(1) or self.color),
            "font_size": item.font().pointSize() if isinstance(item, QGraphicsSimpleTextItem) else 14,
        }

    def paste_style(self):
        if not self._style_clipboard: return
        color = QColor(self._style_clipboard["color"])
        for item in self.selectedItems():
            item.setData(1, color.name(QColor.NameFormat.HexArgb))
            if isinstance(item, QGraphicsSimpleTextItem):
                item.setBrush(color); font=item.font(); font.setPointSize(self._style_clipboard["font_size"]); item.setFont(font)
            elif isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)):
                item.setBrush(color); item.setPen(QPen(color.lighter(140), 2))
            else: item.setPen(QPen(color.lighter(140), 2))
        self._commit(); self.update()

    def set_animation(self, kind, duration=1200, loop=True):
        for item in self.selectedItems():
            item.setData(8, {} if kind == "none" else {
                "type": str(kind), "duration": max(100, int(duration)), "loop": bool(loop)})
        self._commit()

    def rotate_selected(self, delta):
        for item in self.selectedItems():
            if not bool(item.data(7)): item.setRotation(item.rotation() + delta)
        self._commit(); self.update()

    def scale_selected(self, factor):
        for item in self.selectedItems():
            if not bool(item.data(7)): item.setScale(max(.1, min(10, item.scale()*factor)))
        self._commit(); self.update()

    def layer_selected(self, delta):
        for item in self.selectedItems(): item.setZValue(item.zValue() + delta)
        self._commit()

    def align_selected(self, mode):
        items = [i for i in self.selectedItems() if not bool(i.data(7))]
        if len(items) < 2: return
        boxes = [item.sceneBoundingRect() for item in items]
        if mode == "left": target = min(box.left() for box in boxes)
        elif mode == "right": target = max(box.right() for box in boxes)
        elif mode == "hcenter": target = sum(box.center().x() for box in boxes)/len(boxes)
        elif mode == "top": target = min(box.top() for box in boxes)
        elif mode == "bottom": target = max(box.bottom() for box in boxes)
        else: target = sum(box.center().y() for box in boxes)/len(boxes)
        for item, box in zip(items, boxes):
            if mode == "left": item.moveBy(target-box.left(), 0)
            elif mode == "right": item.moveBy(target-box.right(), 0)
            elif mode == "hcenter": item.moveBy(target-box.center().x(), 0)
            elif mode == "top": item.moveBy(0, target-box.top())
            elif mode == "bottom": item.moveBy(0, target-box.bottom())
            else: item.moveBy(0, target-box.center().y())
        self._commit(); self.update()

    def distribute_selected(self, axis):
        items = [i for i in self.selectedItems() if not bool(i.data(7))]
        if len(items) < 3: return
        if axis == "horizontal":
            items.sort(key=lambda i: i.sceneBoundingRect().center().x())
            first=items[0].sceneBoundingRect().center().x(); last=items[-1].sceneBoundingRect().center().x()
            for index,item in enumerate(items[1:-1],1):
                center=item.sceneBoundingRect().center(); item.moveBy(first+(last-first)*index/(len(items)-1)-center.x(),0)
        else:
            items.sort(key=lambda i: i.sceneBoundingRect().center().y())
            first=items[0].sceneBoundingRect().center().y(); last=items[-1].sceneBoundingRect().center().y()
            for index,item in enumerate(items[1:-1],1):
                center=item.sceneBoundingRect().center(); item.moveBy(0,first+(last-first)*index/(len(items)-1)-center.y())
        self._commit(); self.update()


class DashboardDesignerDialog(QDialog):
    def __init__(self, scene_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Визуальный конструктор Canvas 16.1")
        self.resize(1120, 740)
        layout = QVBoxLayout(self)
        tools = QToolBar(); tools.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        layout.addWidget(tools)
        self.scene = DashboardDesignerScene()
        self.view = CanvasView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        layout.addWidget(self.view, 1)
        group = QActionGroup(self); group.setExclusive(True)
        for key, label in (("select", "Указатель"), ("rect", "Прямоугольник"),
                           ("ellipse", "Эллипс"), ("line", "Линия"),
                           ("arrow", "Стрелка"), ("text", "Текст")):
            action = tools.addAction(label); action.setCheckable(True)
            group.addAction(action)
            action.triggered.connect(lambda checked, k=key: self.scene.set_tool(k))
            if key == "select": action.setChecked(True)
        tools.addSeparator()
        self.text_edit = QLineEdit("Текст"); self.text_edit.setMaximumWidth(130)
        self.text_edit.textChanged.connect(
            lambda value: setattr(self.scene, "text_value", value))
        tools.addWidget(self.text_edit)
        tools.addAction("Цвет…").triggered.connect(self.choose_color)
        snap = tools.addAction("Сетка 20")
        snap.setCheckable(True); snap.setChecked(True)
        snap.setToolTip("Привязывать создание и перемещение к сетке")
        snap.toggled.connect(self.scene.set_snap)
        guides = tools.addAction("Направляющие")
        guides.setCheckable(True); guides.setChecked(True)
        guides.toggled.connect(self.scene.set_guides)
        tools.addSeparator()
        undo = tools.addAction("Отменить"); undo.setShortcut(QKeySequence.StandardKey.Undo)
        redo = tools.addAction("Повторить"); redo.setShortcut(QKeySequence.StandardKey.Redo)
        undo.triggered.connect(self.scene.undo); redo.triggered.connect(self.scene.redo)
        undo.setEnabled(False); redo.setEnabled(False)
        self.scene.history_changed.connect(
            lambda can_undo, can_redo: (undo.setEnabled(can_undo), redo.setEnabled(can_redo)))
        duplicate = tools.addAction("Дубликат")
        duplicate.setShortcut(QKeySequence("Ctrl+D")); duplicate.triggered.connect(self.scene.duplicate_selected)
        delete = tools.addAction("Удалить")
        delete.setShortcut(QKeySequence.StandardKey.Delete); delete.triggered.connect(self.scene.delete_selected)
        tools.addSeparator()
        tools.addAction("Группа").triggered.connect(self.scene.group_selected)
        tools.addAction("Разгруппировать").triggered.connect(self.scene.ungroup_selected)
        tools.addAction("Блокировать").triggered.connect(lambda: self.scene.set_locked(True))
        tools.addAction("Разблокировать").triggered.connect(lambda: self.scene.set_locked(False))
        style_menu = QMenu("Стиль", self)
        style_menu.addAction("Копировать стиль").triggered.connect(self.scene.copy_style)
        style_menu.addAction("Применить стиль").triggered.connect(self.scene.paste_style)
        style_button = QToolButton(); style_button.setText("Стиль")
        style_button.setMenu(style_menu); style_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tools.addWidget(style_button)
        tools.addAction("Выше").triggered.connect(lambda: self.scene.layer_selected(1))
        tools.addAction("Ниже").triggered.connect(lambda: self.scene.layer_selected(-1))
        tools.addAction("↶15°").triggered.connect(lambda: self.scene.rotate_selected(-15))
        tools.addAction("↷15°").triggered.connect(lambda: self.scene.rotate_selected(15))
        tools.addSeparator()
        align_menu = QMenu("Выравнивание", self)
        for mode, label in (("left", "По левому краю"), ("hcenter", "По центру X"),
                            ("right", "По правому краю"), ("top", "По верхнему краю"),
                            ("vcenter", "По центру Y"), ("bottom", "По нижнему краю")):
            align_menu.addAction(label).triggered.connect(
                lambda checked=False, value=mode: self.scene.align_selected(value))
        align_menu.addSeparator()
        align_menu.addAction("Распределить по горизонтали").triggered.connect(
            lambda: self.scene.distribute_selected("horizontal"))
        align_menu.addAction("Распределить по вертикали").triggered.connect(
            lambda: self.scene.distribute_selected("vertical"))
        align_button = QToolButton(); align_button.setText("Выровнять")
        align_button.setMenu(align_menu); align_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tools.addWidget(align_button)
        animation_menu = QMenu("Анимация", self)
        for kind, label in (("none", "Нет"), ("pulse", "Пульсация"),
                            ("rotate", "Вращение"), ("blink", "Мигание"),
                            ("slide", "Плавное смещение")):
            animation_menu.addAction(label).triggered.connect(
                lambda checked=False, value=kind: self.scene.set_animation(value))
        animation_button = QToolButton(); animation_button.setText("Анимация")
        animation_button.setMenu(animation_menu); animation_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        tools.addWidget(animation_button)
        hint = QLabel(
            "Колесико — масштаб без дополнительных клавиш. Потяните пустое место ЛКМ — "
            "перемещение полотна. У выбранного объекта есть четыре ручки размера. "
            "Группы двигаются вместе; блокировка защищает объект. Ctrl+Z/Ctrl+Y — история; "
            "стрелки двигают на 1, Shift+стрелки — на 20."
        )
        hint.setWordWrap(True); layout.addWidget(hint)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.scene.load_data(scene_data)

    def choose_color(self):
        value = QColorDialog.getColor(QColor(self.scene.color), self, "Цвет фигуры")
        if value.isValid():
            self.scene.color = value.name(QColor.NameFormat.HexArgb)
            for item in self.scene.selectedItems():
                item.setData(1, self.scene.color)
                if isinstance(item, QGraphicsSimpleTextItem): item.setBrush(value)
                elif isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)): item.setBrush(value)
                if not isinstance(item, QGraphicsSimpleTextItem):
                    item.setPen(QPen(value.lighter(140), 2))
            self.scene._commit()

    def data(self):
        return self.scene.to_data()
