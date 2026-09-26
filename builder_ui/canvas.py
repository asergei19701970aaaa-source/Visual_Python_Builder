from __future__ import annotations

import html

from .common import *
from model_contract import (
    normalize_node_model,
    port_identifier,
    repair_mdi_parentage,
    split_port_identifier,
)
from .property_panel import PropertyPanel
from connection_advisor import (
    advise_connection,
    connection_passport,
    data_type_name,
    normalize_data_type,
)
from user_help import component_search_text

CONTAINER_PROXY_TYPES = {
    "ContainerEventInput",
    "ContainerDataInput",
    "ContainerEventOutput",
    "ContainerDataOutput",
}
CONTAINER_PROXY_SIDES = {
    "ContainerEventInput": "left",
    "ContainerEventOutput": "right",
    "ContainerDataInput": "top",
    "ContainerDataOutput": "bottom",
}


class PaletteListWidget(QListWidget):
    height_changed = Signal()

    def __init__(self):
        super().__init__()
        self._drag_press_position = None
        self.setDragEnabled(True)
        self.setDragDropMode(
            QAbstractItemView.DragDropMode.DragOnly
        )
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

    def refresh_height(self):
        visible_count = sum(
            not self.item(index).isHidden()
            for index in range(self.count())
        )
        grid_width = max(1, self.gridSize().width())
        available = max(grid_width, self.viewport().width())
        columns = max(1, available // grid_width)
        rows = max(1, math.ceil(visible_count / columns))
        height = rows * self.gridSize().height() + self.frameWidth() * 2 + 4
        if self.height() != height:
            self.setFixedHeight(height)
            self.height_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_height()

    def wheelEvent(self, event):
        # The only scrollbar belongs to the containing palette panel.
        event.ignore()

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            return
        type_name = str(item.data(Qt.ItemDataRole.UserRole))
        mime = QMimeData()
        mime.setData(
            "application/x-visual-python-component",
            type_name.encode("utf-8"),
        )
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(item.icon().pixmap(32, 32))
        drag.exec(Qt.DropAction.CopyAction)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_press_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._drag_press_position is not None
            and (
                event.position().toPoint()
                - self._drag_press_position
            ).manhattanLength()
            >= QApplication.startDragDistance()
        ):
            self.startDrag(Qt.DropAction.CopyAction)
            self._drag_press_position = None
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_press_position = None
        super().mouseReleaseEvent(event)


class HelperPaletteListWidget(PaletteListWidget):
    """Палитра графических помощников с отдельным MIME-типом."""

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            return
        helper_type = str(item.data(Qt.ItemDataRole.UserRole) or "helper:note")
        mime = QMimeData()
        mime.setData(
            "application/x-visual-python-helper",
            helper_type.encode("utf-8"),
        )
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(item.icon().pixmap(32, 32))
        drag.exec(Qt.DropAction.CopyAction)


class ContainerPaletteListWidget(PaletteListWidget):
    """Палитра прозрачных контейнеров с отдельным MIME-типом."""

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            return
        template_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not template_id:
            return
        mime = QMimeData()
        mime.setData(
            "application/x-visual-python-container",
            template_id.encode("utf-8"),
        )
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(item.icon().pixmap(32, 32))
        drag.exec(Qt.DropAction.CopyAction)


class CollapsibleSection(QWidget):
    expansion_changed = Signal(bool)

    def __init__(
        self, title: str, expanded: bool = False, nested: bool = False
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.button = QToolButton()
        self.button.setText(title)
        self.button.setCheckable(True)
        self.button.setChecked(expanded)
        self.button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.button.setArrowType(
            Qt.ArrowType.DownArrow
            if expanded
            else Qt.ArrowType.RightArrow
        )
        self.button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        if nested:
            self.button.setStyleSheet(
                "QToolButton {"
                "background:#59636D; color:#FFFFFF;"
                "border:1px solid #343B42;"
                "border-left:5px solid #E28A3B;"
                "text-align:left; font-weight:600;"
                "padding:3px 6px; margin-left:8px; min-height:20px;"
                "}"
                "QToolButton:checked {"
                "background:#3F6F8F; border-left-color:#FFB15C;"
                "}"
            )
        else:
            self.button.setStyleSheet(
                "QToolButton {"
                "background:#DEDEDE; color:#202020;"
                "border:1px solid #AFAFAF; text-align:left;"
                "font-weight:600; padding:3px 5px; min-height:20px;"
                "}"
                "QToolButton:checked { background:#CFE3F1; }"
            )
        layout.addWidget(self.button)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(
            2 if nested else 0, 2, 0, 2
        )
        self.content_layout.setSpacing(1)
        self.content.setVisible(expanded)
        layout.addWidget(self.content)
        self.button.toggled.connect(self.set_expanded)

    def set_expanded(self, expanded: bool):
        self.button.blockSignals(True)
        self.button.setChecked(expanded)
        self.button.blockSignals(False)
        self.button.setArrowType(
            Qt.ArrowType.DownArrow
            if expanded
            else Qt.ArrowType.RightArrow
        )
        self.content.setVisible(expanded)
        self.updateGeometry()
        self.expansion_changed.emit(expanded)


class DockTitleBar(QWidget):
    def __init__(self, dock: QDockWidget, title: str, side: str):
        super().__init__(dock)
        self.dock = dock
        self.side = side
        self.collapsed = False
        self.label = QLabel(title)
        self.label.setStyleSheet("font-weight:600;")
        self.toggle = QToolButton()
        self.toggle.setFixedSize(20, 20)
        self.toggle.setToolTip("Свернуть панель вбок")
        self.toggle.clicked.connect(self.toggle_collapsed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 1, 2, 1)
        layout.setSpacing(2)
        layout.addWidget(self.label)
        layout.addStretch(1)
        layout.addWidget(self.toggle)
        self._update_arrow()

    def _update_arrow(self):
        if self.side == "left":
            self.toggle.setText("▶" if self.collapsed else "◀")
        else:
            self.toggle.setText("◀" if self.collapsed else "▶")

    def toggle_collapsed(self):
        self.collapsed = not self.collapsed
        content = self.dock.widget()
        if content is not None:
            content.setVisible(not self.collapsed)
        self.label.setVisible(not self.collapsed)
        if self.collapsed:
            self.dock.setMinimumWidth(26)
            self.dock.setMaximumWidth(28)
            self.toggle.setToolTip("Развернуть панель")
        else:
            self.dock.setMaximumWidth(16777215)
            self.dock.setMinimumWidth(
                245 if self.side == "left" else 280
            )
            self.toggle.setToolTip("Свернуть панель вбок")
        self._update_arrow()


class CanvasView(QGraphicsView):
    """Общий вид схемы, формы и Canvas с мышиной навигацией."""
    zoom_changed = Signal(int)
    component_dropped = Signal(str, QPointF)
    container_dropped = Signal(str, QPointF)

    def __init__(self, scene):
        super().__init__(scene)
        self._panning = False
        self._pan_position = None
        self._pan_button = None
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setSceneRect(scene.sceneRect())
        self.horizontalScrollBar().valueChanged.connect(self._sync_container_frame)
        self.verticalScrollBar().valueChanged.connect(self._sync_container_frame)

    def _sync_container_frame(self, *_unused):
        scene = self.scene()
        updater = getattr(scene, "update_container_interface_frame", None)
        if callable(updater):
            QTimer.singleShot(0, lambda: updater(self))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_container_frame()

    def wheelEvent(self, event):
        """Колесо всегда масштабирует относительно указателя, без Ctrl."""
        delta = event.angleDelta().y() or event.angleDelta().x()
        if not delta:
            event.ignore()
            return
        current = self.transform().m11()
        factor = 1.15 if delta > 0 else 1 / 1.15
        target = current * factor
        if 0.18 <= target <= 5.0:
            self.scale(factor, factor)
            self.zoom_changed.emit(round(self.transform().m11() * 100))
            self._sync_container_frame()
        event.accept()

    def _left_pan_allowed(self, event):
        """ЛКМ двигает фон, но не мешает нодам, портам и контролам."""
        if event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.ShiftModifier
        ):
            return False
        scene = self.scene()
        if getattr(scene, "tool", "select") != "select":
            return False
        item = self.itemAt(event.position().toPoint())
        if item is None:
            return True
        # На пустой поверхности формы тоже можно схватить полотно. Ручка
        # размера окна при этом остаётся доступной.
        root = item
        while root.parentItem() is not None:
            root = root.parentItem()
        # Imported lazily to avoid a module cycle: the form editor uses
        # CanvasView, while CanvasView only needs this type for one hit-test.
        from .form_editor import FormWindowItem
        if isinstance(root, FormWindowItem) and item is root:
            local = root.mapFromScene(self.mapToScene(event.position().toPoint()))
            return not root._near_handle(local)
        return False

    def _begin_pan(self, event):
        self._panning = True
        self._pan_button = event.button()
        self._pan_position = event.position()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._begin_pan(event)
            return
        if (event.button() == Qt.MouseButton.LeftButton
                and self._left_pan_allowed(event)):
            self._begin_pan(event)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_position is not None:
            delta = event.position() - self._pan_position
            self._pan_position = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning and event.button() == self._pan_button:
            self._panning = False
            self._pan_position = None
            self._pan_button = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(
            "application/x-visual-python-component"
        ):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(
            "application/x-visual-python-container"
        ):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(
            "application/x-visual-python-component"
        ):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(
            "application/x-visual-python-container"
        ):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasFormat("application/x-visual-python-component"):
            type_name = bytes(
                mime.data("application/x-visual-python-component")
            ).decode("utf-8")
            position = self.mapToScene(event.position().toPoint())
            self.component_dropped.emit(type_name, position)
            event.acceptProposedAction()
            return
        if mime.hasFormat("application/x-visual-python-container"):
            template_id = bytes(
                mime.data("application/x-visual-python-container")
            ).decode("utf-8")
            position = self.mapToScene(event.position().toPoint())
            self.container_dropped.emit(template_id, position)
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class PortItem(QGraphicsEllipseItem):
    KIND_LABELS = {
        "work_in": "Вход действия",
        "event_out": "Выход события",
        "data_in": "Вход данных",
        "data_out": "Выход данных",
    }

    def __init__(
        self, node: "NodeItem", name: str, caption: str, kind: str,
        description: str, data_type: str, x: float, y: float,
    ):
        super().__init__(-5, -5, 10, 10, node)
        self.node_item = node
        self.name = name
        self.caption = caption
        self.kind = kind
        self.data_type = data_type or "any"
        self.port_id = port_identifier(name, kind)
        self.setPos(x, y)
        self.setBrush(EVENT_COLOR if kind in {"event_out", "work_in"} else DATA_COLOR)
        self.setPen(QPen(QColor("#FFFFFF"), 1.5))
        self.setZValue(4)
        kind_label = self.KIND_LABELS.get(kind, "Точка соединения")
        help_text = description.strip() or "Описание для этой точки пока не заполнено."
        type_line = (
            f"<br>Тип: {data_type_name(self.data_type)}"
            if kind in {"data_in", "data_out"} else ""
        )
        self.setToolTip(
            f"<b>{caption}</b> <span style='color:#777'>({name})</span><br>"
            f"{kind_label}{type_line}<br><span style='color:#555'>{help_text}</span>"
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._dragged = False

    def mousePressEvent(self, event):
        scene = self.scene()
        if (
            isinstance(scene, GraphScene)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene.begin_port_action(self, event.modifiers())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene = self.scene()
        if (
            isinstance(scene, GraphScene)
            and (
                self.kind in {"event_out", "data_out"}
                or scene.pending_port is not None
                or scene.fixed_target is not None
            )
        ):
            self._dragged = True
            scene.update_temporary_connection(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        scene = self.scene()
        if isinstance(scene, GraphScene) and self._dragged:
            self._dragged = False
            scene.finish_temporary_connection(event.scenePos())
            event.accept()
            return
        if (
            isinstance(scene, GraphScene)
            and event.button() == Qt.MouseButton.LeftButton
            and scene.rewire_backup is not None
        ):
            # A simple click must not silently detach an existing wire.
            scene.cancel_temporary_connection(restore=True)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class ConnectionNodePicker(QDialog):
    """Searchable list of nodes that can continue the current wire."""

    def __init__(self, candidates, *, outgoing: bool, parent=None):
        super().__init__(parent)
        self.candidates = list(candidates)
        self.setWindowTitle(
            "Добавить следующую ноду"
            if outgoing else "Добавить предыдущую ноду"
        )
        self.resize(620, 470)
        layout = QVBoxLayout(self)
        direction = (
            "Выберите вход новой ноды. Она будет установлена и соединена автоматически."
            if outgoing else
            "Выберите результат новой ноды. Она будет установлена и соединена автоматически."
        )
        intro = QLabel(direction)
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Поиск по названию, назначению, разделу или точке…"
        )
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)
        self.list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        layout.addWidget(self.list, 1)
        note = QLabel(
            "Показываются только ноды, которые можно соединить напрямую. "
            "Никакие специальные скрытые ноды не создаются."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#666;")
        layout.addWidget(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Добавить")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._ok_button = buttons.button(
            QDialogButtonBox.StandardButton.Ok
        )
        self.search.textChanged.connect(self._fill)
        self.search.returnPressed.connect(
            lambda: self.accept()
            if self.list.currentItem() is not None else None
        )
        self.list.itemDoubleClicked.connect(lambda _item: self.accept())
        self.list.itemSelectionChanged.connect(
            lambda: self._ok_button.setEnabled(
                self.list.currentItem() is not None
            )
        )
        self._fill()
        self.search.setFocus()

    def _fill(self):
        query = self.search.text().strip().lower()
        selected_key = (
            self.list.currentItem().data(Qt.ItemDataRole.UserRole)
            if self.list.currentItem() else None
        )
        self.list.clear()
        for candidate in self.candidates:
            if query and all(
                word not in candidate["search"]
                for word in query.split()
            ):
                continue
            item = QListWidgetItem(
                f'{candidate["caption"]}  ·  {candidate["port_caption"]}\n'
                f'{candidate["category"]}'
            )
            key = (candidate["type_name"], candidate["port_name"])
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setToolTip(candidate["description"])
            self.list.addItem(item)
            if key == selected_key:
                self.list.setCurrentItem(item)
        if self.list.count() and self.list.currentItem() is None:
            self.list.setCurrentRow(0)
        self._ok_button.setEnabled(self.list.currentItem() is not None)

    def selected_candidate(self):
        item = self.list.currentItem()
        if item is None:
            return None
        key = item.data(Qt.ItemDataRole.UserRole)
        return next(
            (
                candidate for candidate in self.candidates
                if (candidate["type_name"], candidate["port_name"]) == key
            ),
            None,
        )


class NodeItem(QGraphicsRectItem):
    def __init__(self, model: dict[str, Any], spec: ComponentSpec):
        self.is_container_proxy = spec.type_name in CONTAINER_PROXY_TYPES
        self.is_container_bridge = self.is_container_proxy
        self.proxy_side = CONTAINER_PROXY_SIDES.get(spec.type_name, "")
        instance_ports = effective_ports(
            spec.type_name, model.get("properties", {})
        )
        enabled = model.setdefault(
            "enabled_ports", default_enabled_ports(spec, instance_ports)
        )
        # Count-driven points are controlled by their numeric properties and
        # are therefore always visible while they exist.
        for port in instance_ports:
            if port.name not in {item.name for item in spec.ports} and port.name not in enabled:
                enabled.append(port.name)
        known = {port.name for port in instance_ports}
        enabled[:] = [name for name in enabled if name in known]
        visible_ports = [port for port in instance_ports if port.name in enabled]
        ports_left = [p for p in visible_ports if p.kind == "work_in"]
        ports_right = [p for p in visible_ports if p.kind == "event_out"]
        ports_top = [p for p in visible_ports if p.kind == "data_in"]
        ports_bottom = [p for p in visible_ports if p.kind == "data_out"]
        if self.is_container_bridge:
            self.width = 26
            self.height = 26
        else:
            self.width = max(72, 22 * max(len(ports_top), len(ports_bottom)) + 24)
            self.height = max(62, 19 * max(len(ports_left), len(ports_right)) + 24)
        super().__init__(0, 0, self.width, self.height)
        self.model = model
        self.spec = spec
        # Connections on disk keep the readable port name.  The editor must
        # also keep the direction because a component may have the same name
        # on an input and an output.
        self.ports: dict[str, PortItem] = {}
        self.setPos(float(model.get("x", 0)), float(model.get("y", 0)))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
        )
        self.setBrush(Qt.BrushStyle.NoBrush)
        self.setPen(Qt.PenStyle.NoPen)
        self.setZValue(2)

        if not self.is_container_bridge:
            icon_path = component_icon_path(spec.type_name)
            if icon_path:
                pixmap = QIcon(str(icon_path)).pixmap(24, 24)
                symbol = QGraphicsPixmapItem(pixmap, self)
                symbol.setPos((self.width - pixmap.width()) / 2, 7)
            else:
                symbol = QGraphicsSimpleTextItem(
                    NODE_SYMBOLS.get(spec.type_name, "◆"), self
                )
                symbol_font = symbol.font()
                symbol_font.setBold(True)
                symbol_font.setPointSize(
                    13 if len(NODE_SYMBOLS.get(spec.type_name, "")) == 1 else 10
                )
                symbol.setFont(symbol_font)
                symbol.setBrush(QColor("#2C2C2B"))
                symbol_rect = symbol.boundingRect()
                symbol.setPos((self.width - symbol_rect.width()) / 2, 9)

            title_font = QGraphicsSimpleTextItem().font()
            title_font.setPointSize(8)
            short_caption = QFontMetrics(title_font).elidedText(
                spec.caption,
                Qt.TextElideMode.ElideRight,
                max(30, int(self.width - 10)),
            )
            title = QGraphicsSimpleTextItem(short_caption, self)
            title.setFont(title_font)
            title.setBrush(QColor("#565451"))
            title_rect = title.boundingRect()
            title.setPos((self.width - title_rect.width()) / 2, self.height - 21)
        else:
            point_name = str(model.get("properties", {}).get("name", "")).strip()
            label = QGraphicsSimpleTextItem(point_name or spec.caption, self)
            label_font = label.font()
            label_font.setPointSize(8)
            label_font.setBold(True)
            label.setFont(label_font)
            label.setBrush(QColor("#4A4742"))
            label_rect = label.boundingRect()
            if self.proxy_side == "left":
                label.setPos(self.width + 8, (self.height - label_rect.height()) / 2)
            elif self.proxy_side == "right":
                label.setPos(-label_rect.width() - 8, (self.height - label_rect.height()) / 2)
            elif self.proxy_side == "top":
                label.setPos((self.width - label_rect.width()) / 2, self.height + 5)
            else:
                label.setPos((self.width - label_rect.width()) / 2, -label_rect.height() - 5)

        for index, port in enumerate(ports_left):
            y = self.height * (index + 1) / (len(ports_left) + 1)
            item = PortItem(
                self, port.name, port.caption, port.kind,
                port.description, port.data_type, 0, y,
            )
            self.ports[item.port_id] = item

        for index, port in enumerate(ports_right):
            y = self.height * (index + 1) / (len(ports_right) + 1)
            item = PortItem(
                self, port.name, port.caption, port.kind,
                port.description, port.data_type, self.width, y,
            )
            self.ports[item.port_id] = item

        for index, port in enumerate(ports_top):
            x = self.width * (index + 1) / (len(ports_top) + 1)
            item = PortItem(
                self, port.name, port.caption, port.kind,
                port.description, port.data_type, x, 0,
            )
            self.ports[item.port_id] = item

        for index, port in enumerate(ports_bottom):
            x = self.width * (index + 1) / (len(ports_bottom) + 1)
            item = PortItem(
                self, port.name, port.caption, port.kind,
                port.description, port.data_type, x, self.height,
            )
            self.ports[item.port_id] = item

        if self.is_container_bridge:
            direction = "вход контейнера" if "Input" in spec.type_name else "выход контейнера"
            self.setToolTip(
                f"<b>{direction}</b><br>"
                "Служебная внешняя точка контейнера. Она не является отдельной нодой."
            )
        else:
            self.setToolTip(
                f"<b>{spec.caption}</b><br>{spec.type_name}<br><span style='color:#777'>"
                "Выберите компонент, чтобы изменить свойства</span>"
            )

    def port_for(self, value: str | None, outgoing: bool | None = None):
        """Resolve a persisted name or a direction-aware port identifier."""
        if value is None:
            return None
        name, kind = split_port_identifier(str(value))
        exact = self.ports.get(str(value))
        if exact is not None:
            return exact
        candidates = [
            port for port in self.ports.values()
            if port.name == name and (kind is None or port.kind == kind)
        ]
        if outgoing is not None:
            output_kinds = {"event_out", "data_out"}
            candidates = [
                port for port in candidates
                if (port.kind in output_kinds) == outgoing
            ]
        return candidates[0] if candidates else None

    def contextMenuEvent(self, event):
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            super().contextMenuEvent(event)
            return

        if not self.isSelected():
            scene.clearSelection()
            self.setSelected(True)

        menu = QMenu()
        title = menu.addAction(f"{self.spec.caption}  ·  {self.spec.type_name}")
        title.setEnabled(False)
        menu.addSeparator()
        properties = menu.addAction("Показать свойства")
        help_action = menu.addAction("Справка об элементе")
        instrument_designer = menu.addAction("Конструктор пользовательского прибора…")
        instrument_designer.setVisible(self.spec.type_name == "CustomInstrument")
        canvas_designer = menu.addAction("Открыть мышиный редактор Canvas…")
        canvas_designer.setVisible(self.spec.type_name == "DashboardCanvas")
        open_container=menu.addAction("Открыть внутреннюю схему"); open_container.setVisible(self.spec.type_name=="UserContainer")
        passport_container=menu.addAction("Паспорт и внешний интерфейс…"); passport_container.setVisible(self.spec.type_name=="UserContainer")
        unpack_container=menu.addAction("Распаковать контейнер"); unpack_container.setVisible(self.spec.type_name=="UserContainer")
        save_container=menu.addAction("Сохранить в библиотеку контейнеров…"); save_container.setVisible(self.spec.type_name=="UserContainer")
        count=len([i for i in scene.selectedItems() if isinstance(i,NodeItem)])
        pack_selected=menu.addAction(f"Создать контейнер из выделенного ({count})"); pack_selected.setEnabled(count>0)
        icon_action = menu.addAction("Выбрать свой значок…")
        reset_icon_action = menu.addAction("Вернуть стандартный значок")
        reset_icon_action.setEnabled(self.spec.type_name in load_icon_assignments())

        points_action = menu.addAction("Точки…")
        points_action.setToolTip(
            "Открыть ту же панель точек, что используется в панели свойств: "
            "с обозначениями, подсказками и расширенной справкой."
        )

        menu.addSeparator()
        select_wires = menu.addAction("Выделить связанные нити")
        select_wires.setEnabled(any(
            connection.source.node_item is self
            or connection.target.node_item is self
            for connection in scene.connections
        ))
        menu.addSeparator()
        copy_action = menu.addAction("Копировать")
        duplicate = menu.addAction("Дублировать")
        delete = menu.addAction("Удалить")

        selected = menu.exec(event.screenPos())
        if selected is None:
            event.accept()
            return
        if selected is points_action:
            self._show_points_dialog(scene)
        else:
            actions = {
                properties: "properties",
                help_action: "help",
                instrument_designer: "instrument_designer",
                canvas_designer: "canvas_designer", open_container:"open_container", passport_container:"container_passport", unpack_container:"unpack_container", save_container:"save_container", pack_selected:"pack_container",
                icon_action: "choose_icon",
                reset_icon_action: "reset_icon",
                select_wires: "select_wires",
                copy_action: "copy",
                duplicate: "duplicate",
                delete: "delete",
            }
            action = actions.get(selected)
            if action:
                scene.node_action_requested.emit(str(self.model["id"]), action)
        event.accept()

    def _show_points_dialog(self, scene: "GraphScene"):
        """Show the canonical property-panel point editor for this node."""
        views = scene.views()
        parent = views[0].window() if views else None
        dialog = QDialog(parent)
        dialog.setWindowTitle(f"Точки — {self.spec.caption}")
        dialog.setMinimumSize(430, 500)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(8, 8, 8, 8)

        # A copy keeps the scene stable while the modal window is open.  The
        # accepted differences are then sent through the normal MainWindow
        # handler, including its connection-removal confirmation.
        edited_model = copy.deepcopy(self.model)
        panel = PropertyPanel()
        panel.set_node(edited_model)
        panel.property_search.hide()
        panel.tabs.setCurrentIndex(1)
        panel.tabs.setTabVisible(0, False)
        panel.tabs.tabBar().hide()
        layout.addWidget(panel, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        desired = set()
        for index in range(panel.points_tree.topLevelItemCount()):
            item = panel.points_tree.topLevelItem(index)
            name = item.data(0, Qt.ItemDataRole.UserRole)
            if name and item.checkState(0) == Qt.CheckState.Checked:
                desired.add(str(name))
        current = set(self.model.get("enabled_ports", []))
        for port in effective_ports(
            self.spec.type_name, self.model.get("properties", {})
        ):
            before = port.name in current
            after = port.name in desired or port.required
            if before != after:
                scene.node_action_requested.emit(
                    str(self.model["id"]),
                    f"port:{port.name}:{'on' if after else 'off'}",
                )

    def mouseDoubleClickEvent(self,event):
        scene=self.scene()
        if self.spec.type_name=="UserContainer" and isinstance(scene,GraphScene):
            scene.node_action_requested.emit(str(self.model["id"]),"open_container"); event.accept(); return
        super().mouseDoubleClickEvent(event)

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.rect().adjusted(1, 1, -1, -1)
        if self.is_container_bridge:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setBrush(
                QColor("#BDBDBD") if self.isSelected() else QColor("#FFF7D6")
            )
            painter.setPen(QPen(QColor("#866B21"), 1.4))
            painter.drawEllipse(rect.adjusted(4, 4, -4, -4))
            painter.setPen(QPen(QColor("#5B4A16"), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "↔")
            return
        # Neutral grey makes multi-selection obvious, independently of the
        # component's normal colour.
        painter.setBrush(
            QColor("#BDBDBD") if self.isSelected() else QColor(self.spec.color)
        )
        if self.spec.type_name == "UserContainer":
            painter.setBrush(
                QColor("#B8C7D8") if self.isSelected()
                else QColor("#DCE6F2")
            )
            painter.setPen(
                QPen(
                    QColor("#0D2744") if self.isSelected()
                    else QColor("#183B63"),
                    2.6 if self.isSelected() else 2.0,
                )
            )
        elif self.isSelected():
            painter.setPen(QPen(QColor("#666666"), 2))
        else:
            painter.setPen(QPen(QColor("#8F8E8B"), 1))
        painter.drawRect(rect)
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawLine(
            QPointF(rect.left() + 4, rect.bottom() - 24),
            QPointF(rect.right() - 4, rect.bottom() - 24),
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.scene()
            if (
                self.is_container_proxy
                and isinstance(scene, GraphScene)
                and scene.interface_frame_rect is not None
            ):
                frame = scene.interface_frame_rect
                scale = max(0.01, scene.interface_view_scale)
                port = next(iter(self.ports.values()), None)
                anchor_x = (port.pos().x() if port is not None else self.width / 2) / scale
                anchor_y = (port.pos().y() if port is not None else self.height / 2) / scale
                point_x = float(value.x()) + anchor_x
                point_y = float(value.y()) + anchor_y
                if self.proxy_side == "left":
                    point_x = frame.left()
                    point_y = min(max(point_y, frame.top()), frame.bottom())
                elif self.proxy_side == "right":
                    point_x = frame.right()
                    point_y = min(max(point_y, frame.top()), frame.bottom())
                elif self.proxy_side == "top":
                    point_x = min(max(point_x, frame.left()), frame.right())
                    point_y = frame.top()
                elif self.proxy_side == "bottom":
                    point_x = min(max(point_x, frame.left()), frame.right())
                    point_y = frame.bottom()
                return QPointF(point_x - anchor_x, point_y - anchor_y)
            if (
                isinstance(scene, GraphScene)
                and scene.in_container
                and scene.interface_frame_rect is not None
            ):
                value = scene._clamp_node_position(self, value)
            if isinstance(scene, GraphScene) and scene.snap_enabled:
                step = scene.snap_size
                snapped = QPointF(
                    round(value.x() / step) * step,
                    round(value.y() / step) * step,
                )
                if scene.in_container and scene.interface_frame_rect is not None:
                    return scene._clamp_node_position(self, snapped)
                return snapped
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()
            if (
                self.is_container_proxy
                and isinstance(scene, GraphScene)
                and scene._positioning_interface_points
            ):
                # The scene refreshes every wire once after all frame points
                # have been positioned.  Refreshing here for every point used
                # to produce transient gaps and quadratic work in containers.
                return super().itemChange(change, value)
            self.model["x"] = round(value.x(), 1)
            self.model["y"] = round(value.y(), 1)
            if isinstance(scene, GraphScene):
                if self.is_container_proxy and scene.interface_frame_rect is not None:
                    frame = scene.interface_frame_rect
                    scale = max(0.01, scene.interface_view_scale)
                    port = next(iter(self.ports.values()), None)
                    anchor_x = (port.pos().x() if port is not None else self.width / 2) / scale
                    anchor_y = (port.pos().y() if port is not None else self.height / 2) / scale
                    if self.proxy_side in {"left", "right"}:
                        offset = (value.y() + anchor_y - frame.top()) / max(1.0, frame.height())
                    else:
                        offset = (value.x() + anchor_x - frame.left()) / max(1.0, frame.width())
                    self.model.setdefault("properties", {})["_frame_offset"] = round(
                        min(max(offset, 0.02), 0.98), 4
                    )
                scene.refresh_connections()
                scene.changed_model.emit()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)


class ConnectionItem(QGraphicsPathItem):
    """Редактируемая нить, перенесённая из NodeFlow 18.0."""

    def __init__(self, model: dict[str, Any], source: PortItem, target: PortItem):
        super().__init__()
        self.model = model
        self.source = source
        self.target = target
        if "bends" not in model and model.get("points"):
            model["bends"] = copy.deepcopy(model["points"])
        model.setdefault("bends", [])
        model.setdefault("line_style", "orthogonal")
        try:
            saved_position = model.get("debug_position")
            if saved_position is None and isinstance(model.get("probe"), dict):
                saved_position = model["probe"].get("position", 0.5)
            model["debug_position"] = min(
                1.0,
                max(
                    0.0,
                    float(saved_position if saved_position is not None else 0.5),
                ),
            )
        except (TypeError, ValueError):
            model["debug_position"] = 0.5
        if model.get("breakpoint") and "breakpoint_position" not in model:
            model["breakpoint_position"] = model["debug_position"]
        if isinstance(model.get("probe"), dict):
            model["probe"].setdefault(
                "position", model.get("debug_position", 0.5)
            )
            probe_position = float(model["probe"]["position"])
            breakpoint_position = float(
                model.get("breakpoint_position", probe_position)
            )
            # Migrate old projects where both markers were persisted at the
            # same fraction. Keep both centres on the wire, but separate them
            # along the wire itself so the square cannot cover the circle.
            if model.get("breakpoint") and abs(
                breakpoint_position - probe_position
            ) < 0.04:
                center = (breakpoint_position + probe_position) / 2
                model["breakpoint_position"] = min(0.96, center + 0.08)
                model["probe"]["position"] = max(0.04, center - 0.08)
        self._hovered = False
        self._hover_screen_pos = None
        self._drag_segment = None
        self._drag_handle = None
        self._drag_start = None
        self._drag_points = None
        self._drag_debug_marker = False
        self._drag_debug_kind = None
        self._right_drag_start = None
        self._delete_on_release = False
        self._suppress_next_context = False
        self._rewire_endpoint = None
        self._pulse_started = 0.0
        self._pulse_duration = 0.0
        self.setZValue(1)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        # The passport is shown with a delay and offset from the cursor.  A
        # permanent QGraphicsItem tooltip would cover nearby port help because
        # the wire intentionally has a wide hit area.
        self.setToolTip("")
        self.update_path()

    def start_debug_pulse(self, duration_ms: int = 700):
        self._pulse_started = time.monotonic()
        self._pulse_duration = max(0, int(duration_ms)) / 1000.0
        self.update()

    def clear_debug_pulse(self):
        self._pulse_started = 0.0
        self._pulse_duration = 0.0
        self.update()

    def debug_pulse_color(self):
        explicit = {
            "request": "#F9A825",
            "response": "#43A047",
            "error": "#E53935",
            "event": "#FB8C00",
            "data": "#1976D2",
        }
        signal_type = str(self.model.get("signal_type", "")).lower()
        if signal_type in explicit:
            return QColor(explicit[signal_type])
        if self.source.kind == "data_out":
            return QColor("#1976D2")  # данные
        port_name = str(self.source.name).lower()
        if any(word in port_name for word in ("request", "query", "запрос")):
            return QColor("#F9A825")  # запрос
        if any(word in port_name for word in ("response", "answer", "result", "ответ")):
            return QColor("#43A047")  # ответ
        if any(word in port_name for word in ("error", "fail", "ошиб")):
            return QColor("#E53935")  # ошибка
        return QColor("#FB8C00")  # рабочее событие

    def advance_debug_pulse(self, now: float) -> bool:
        if not self._pulse_started:
            return False
        if self._pulse_duration <= 0:
            return True
        if now - self._pulse_started >= self._pulse_duration:
            self._pulse_started = 0.0
            self.update()
            return False
        self.update()
        return True

    def _has_frame_endpoint(self):
        return (
            self.source.node_item.is_container_proxy
            or self.target.node_item.is_container_proxy
        )

    @staticmethod
    def _inward_direction(side: str):
        return {
            "left": (1.0, 0.0),
            "right": (-1.0, 0.0),
            "top": (0.0, 1.0),
            "bottom": (0.0, -1.0),
        }.get(side, (0.0, 0.0))

    def _endpoint_direction(self, port: PortItem, is_source: bool):
        node = port.node_item
        if node.is_container_proxy:
            return self._inward_direction(node.proxy_side)
        if is_source:
            return (1.0, 0.0) if port.kind == "event_out" else (0.0, 1.0)
        return (-1.0, 0.0) if port.kind == "work_in" else (0.0, -1.0)

    def _frame_port_point(self, port: PortItem):
        """Return the exact frame anchor for a container interface port."""
        scene = self.scene()
        if (
            not isinstance(scene, GraphScene)
            or not port.node_item.is_container_proxy
            or scene.interface_frame_rect is None
        ):
            return port.scenePos()
        return scene.container_frame_anchor(port)

    def _frame_route_points(self):
        start = self._frame_port_point(self.source)
        end = self._frame_port_point(self.target)
        scene = self.scene()
        scale = max(
            0.01,
            scene.interface_view_scale
            if isinstance(scene, GraphScene) else 1.0,
        )
        start_direction = self._endpoint_direction(self.source, True)
        end_direction = self._endpoint_direction(self.target, False)
        start_stub = 26.0 / scale if self.source.node_item.is_container_proxy else 16.0
        end_stub = 26.0 / scale if self.target.node_item.is_container_proxy else 16.0
        first = QPointF(
            start.x() + start_direction[0] * start_stub,
            start.y() + start_direction[1] * start_stub,
        )
        last = QPointF(
            end.x() + end_direction[0] * end_stub,
            end.y() + end_direction[1] * end_stub,
        )
        start_horizontal = abs(start_direction[0]) > 0.0
        end_horizontal = abs(end_direction[0]) > 0.0
        stored = self.model.get("bends", [])
        middle = []
        if stored:
            middle = [
                self._clamp_to_frame(QPointF(float(point[0]), float(point[1])))
                for point in stored
                if isinstance(point, (list, tuple)) and len(point) >= 2
            ]
            if len(middle) >= 2:
                middle[0], middle[-1] = first, last
            else:
                middle = []
        if not middle:
            if start_horizontal and end_horizontal:
                x = (first.x() + last.x()) / 2
                middle = [first, QPointF(x, first.y()), QPointF(x, last.y()), last]
            elif not start_horizontal and not end_horizontal:
                y = (first.y() + last.y()) / 2
                middle = [first, QPointF(first.x(), y), QPointF(last.x(), y), last]
            elif start_horizontal:
                middle = [first, QPointF(last.x(), first.y()), last]
            else:
                middle = [first, QPointF(first.x(), last.y()), last]
        return normalize_orthogonal_points(
            [start] + middle + [end],
            vertical=not start_horizontal,
            simplify=not bool(stored),
        )

    def _clamp_to_frame(self, point: QPointF):
        scene = self.scene()
        if not isinstance(scene, GraphScene) or scene.interface_frame_rect is None:
            return QPointF(point)
        scale = max(0.01, scene.interface_view_scale)
        margin = 8.0 / scale
        frame = scene.interface_frame_rect.adjusted(
            margin, margin, -margin, -margin
        )
        return QPointF(
            min(max(point.x(), frame.left()), frame.right()),
            min(max(point.y(), frame.top()), frame.bottom()),
        )

    def _vertical(self):
        return self.source.kind == "data_out"

    def _route_points(self):
        if self._has_frame_endpoint():
            return self._frame_route_points()
        points = build_orthogonal_points(
            self.source.scenePos(), self.target.scenePos(),
            vertical=self._vertical(), bends=self.model.get("bends", []))
        scene = self.scene()
        if isinstance(scene, GraphScene) and scene.in_container:
            points = [points[0]] + [
                self._clamp_to_frame(QPointF(point))
                for point in points[1:-1]
            ] + [points[-1]]
            points = normalize_orthogonal_points(
                points,
                vertical=self._vertical(),
                simplify=not bool(self.model.get("bends")),
            )
        return points

    def update_path(self):
        self.prepareGeometryChange()
        start, end = self.source.scenePos(), self.target.scenePos()
        if self._has_frame_endpoint():
            path = rounded_orthogonal_path(self._frame_route_points())
        elif self.model.get("line_style") == "curve":
            path = build_curve_path(start, end, vertical=self._vertical())
        else:
            path = rounded_orthogonal_path(self._route_points())
        self.setPath(path)
        self._apply_pen()

    def _apply_pen(self):
        base = EVENT_COLOR if self.source.kind == "event_out" else DATA_COLOR
        if self.model.get("breakpoint"):
            base = QColor("#D32F2F")
        elif isinstance(self.model.get("probe"), dict):
            base = QColor("#7B1FA2")
        color = (QColor("#FFF200") if self._hovered else
                 QColor("#2783DE") if self.isSelected() else base)
        pen = QPen(color, 3.4 if self._hovered else 2.3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

    def _node_display_name(self, node_item: NodeItem) -> str:
        name = str(
            node_item.model.get("properties", {}).get("name", "")
        ).strip()
        return (
            f"{node_item.spec.caption} ({name})"
            if name and name != node_item.spec.caption
            else node_item.spec.caption
        )

    def passport_text(self) -> str:
        text = connection_passport(
            self._node_display_name(self.source.node_item),
            self.source.caption,
            self.source.kind,
            self.source.data_type,
            self._node_display_name(self.target.node_item),
            self.target.caption,
            self.target.kind,
            self.target.data_type,
        )
        details = [
            "",
            f"Технически: {self.source.node_item.spec.type_name}."
            f"{self.source.name} → "
            f"{self.target.node_item.spec.type_name}.{self.target.name}",
        ]
        if self.model.get("breakpoint"):
            details.append("Отладка: установлена точка останова.")
        probe = self.model.get("probe")
        if isinstance(probe, dict):
            details.append(
                f"Отладка: измерительная точка "
                f"«{probe.get('name', '')}»."
            )
        return text + "\n" + "\n".join(details)

    def _show_hover_passport(self):
        if not self._hovered or self._hover_screen_pos is None:
            return
        body = "<br>".join(
            html.escape(line) for line in self.passport_text().splitlines()
        )
        widget = self.scene().views()[0] if self.scene() and self.scene().views() else None
        QToolTip.showText(
            self._hover_screen_pos + QPoint(18, 18),
            body,
            widget,
        )

    def hoverEnterEvent(self, event):
        self._hovered = True
        self._hover_screen_pos = event.screenPos()
        self.setZValue(4)
        self._apply_pen()
        QTimer.singleShot(550, self._show_hover_passport)
        scene = self.scene()
        if isinstance(scene, GraphScene):
            scene.connection_hint.emit(
                f"{self._node_display_name(self.source.node_item)} · "
                f"{self.source.caption} → "
                f"{self._node_display_name(self.target.node_item)} · "
                f"{self.target.caption}"
            )
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event):
        self._hover_screen_pos = event.screenPos()
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self._hover_screen_pos = None
        QToolTip.hideText()
        self.setZValue(1)
        self._apply_pen()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._apply_pen()
        return super().itemChange(change, value)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(self.path())

    @staticmethod
    def _distance_to_segment(point, first, second):
        if abs(first.x() - second.x()) < 0.01:
            low, high = sorted((first.y(), second.y()))
            return abs(point.x() - first.x()) + max(
                0.0, low - point.y(), point.y() - high)
        low, high = sorted((first.x(), second.x()))
        return abs(point.y() - first.y()) + max(
            0.0, low - point.x(), point.x() - high)

    def _nearest_segment(self, point):
        points = self._route_points()
        choices = list(range(1, max(1, len(points) - 2)))
        found = min(choices, key=lambda i: self._distance_to_segment(
            point, points[i], points[i + 1]), default=None)
        if found is not None and self._distance_to_segment(
                point, points[found], points[found + 1]) > 18.0:
            found = None
        return found, points

    @staticmethod
    def _nearest_handle(point, points):
        choices = range(2, max(2, len(points) - 2))
        found = min(choices, key=lambda i: QLineF(
            point, points[i]).length(), default=None)
        if found is not None and QLineF(
                point, points[found]).length() <= 6.0:
            return found
        return None

    def _has_debug_marker(self):
        return bool(self.model.get("breakpoint")) or (
            isinstance(self.model.get("probe"), dict)
            and self.model["probe"].get("enabled", True)
        )

    def _marker_percent(self, kind=None):
        if kind == "break":
            value = self.model.get(
                "breakpoint_position",
                self.model.get("debug_position", 0.5),
            )
        elif kind == "probe":
            probe = self.model.get("probe")
            value = (
                probe.get("position", self.model.get("debug_position", 0.5))
                if isinstance(probe, dict)
                else self.model.get("debug_position", 0.5)
            )
        else:
            value = self.model.get("debug_position", 0.5)
        return min(1.0, max(0.0, float(value)))

    def _marker_point(self, kind=None):
        return self.path().pointAtPercent(self._marker_percent(kind))

    def _debug_position_at(self, scene_position):
        """Find the nearest point on the rendered wire as a 0..1 fraction."""
        path = self.path()
        if path.isEmpty():
            return 0.5
        best_percent = 0.5
        best_distance = float("inf")
        for index in range(201):
            percent = index / 200.0
            distance = QLineF(
                path.pointAtPercent(percent), scene_position
            ).length()
            if distance < best_distance:
                best_distance = distance
                best_percent = percent
        return best_percent

    def _store_points(self, points, simplify=True):
        if self._has_frame_endpoint():
            points = [points[0]] + [
                self._clamp_to_frame(QPointF(point))
                for point in points[1:-1]
            ] + [points[-1]]
        cleaned = normalize_orthogonal_points(
            points, vertical=self._vertical(), simplify=simplify)
        self.model["bends"] = [
            [point.x(), point.y()] for point in cleaned[1:-1]]
        self.model.pop("points", None)
        self.update_path()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            # Screen coordinates keep the delete gesture stable at any zoom.
            self._right_drag_start = event.screenPos()
            self._delete_on_release = False
            self.setSelected(True)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            position = event.scenePos()
            marker_points = []
            if self.model.get("breakpoint"):
                marker_points.append(self._marker_point("break"))
            if isinstance(self.model.get("probe"), dict):
                marker_points.append(self._marker_point("probe"))
            if marker_points:
                distances = [
                    (QLineF(position, self._marker_point("break")).length(), "break")
                    if self.model.get("breakpoint") else (float("inf"), None),
                    (QLineF(position, self._marker_point("probe")).length(), "probe")
                    if isinstance(self.model.get("probe"), dict)
                    else (float("inf"), None),
                ]
                distance, kind = min(distances, key=lambda item: item[0])
            else:
                distance, kind = float("inf"), None
            if distance <= 14:
                self._drag_debug_marker = True
                self._drag_debug_kind = kind
                self.setSelected(True)
                event.accept()
                return
            near_source = QLineF(position, self.source.scenePos()).length() <= 16
            near_target = QLineF(position, self.target.scenePos()).length() <= 16
            if isinstance(scene, GraphScene) and (near_source or near_target):
                scene.cancel_temporary_connection()
                scene.rewire_backup = copy.deepcopy(self.model)
                if near_target:
                    scene.pending_port = self.source
                    scene._start_temporary_connection(self.source)
                    self._rewire_endpoint = "target"
                else:
                    scene.fixed_target = self.target
                    scene.temporary_connection = QGraphicsPathItem()
                    scene.temporary_connection.setZValue(10)
                    scene.addItem(scene.temporary_connection)
                    scene._highlight_reverse_targets(self.target)
                    scene.update_temporary_connection(position)
                    self._rewire_endpoint = "source"
                pen = QPen(
                    EVENT_COLOR
                    if self.source.kind == "event_out"
                    else DATA_COLOR,
                    2.8,
                    Qt.PenStyle.SolidLine,
                )
                scene.temporary_connection.setPen(pen)
                self.setOpacity(0.12)
                scene.connection_hint.emit(
                    "Тяните конец нити к совместимой точке; "
                    "отпускание на пустом месте удалит связь."
                )
                event.accept()
                return
        if (self.model.get("line_style") == "orthogonal"
                and event.button() == Qt.MouseButton.LeftButton):
            segment, points = self._nearest_segment(event.scenePos())
            handle = self._nearest_handle(event.scenePos(), points)
            if handle is not None:
                if not self.model.get("bends"):
                    self.model["bends"] = [
                        [p.x(), p.y()] for p in points[1:-1]]
                    points = self._route_points()
                self._drag_handle = handle
                self._drag_start = QPointF(event.scenePos())
                self._drag_points = [QPointF(p) for p in points]
                self.setSelected(True)
                event.accept()
                return
            if segment is not None:
                if len(points) <= 4:
                    first, last = points[1], points[-2]
                    points[2:2] = [
                        QLineF(first, last).pointAt(1 / 3),
                        QLineF(first, last).pointAt(2 / 3)]
                if not self.model.get("bends") or len(self._route_points()) <= 4:
                    self.model["bends"] = [
                        [p.x(), p.y()] for p in points[1:-1]]
                    points = self._route_points()
                segment, points = self._nearest_segment(event.scenePos())
                if segment is None:
                    super().mousePressEvent(event)
                    return
                if segment == 1 or segment == len(points) - 3:
                    first = QPointF(points[segment])
                    second = QPointF(points[segment + 1])
                    points[segment + 1:segment + 1] = [first, second]
                    segment += 1
                self._drag_segment = segment
                self._drag_start = QPointF(event.scenePos())
                self._drag_points = [QPointF(p) for p in points]
                self.setSelected(True)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._right_drag_start is not None:
            distance = QLineF(
                self._right_drag_start, event.screenPos()
            ).length()
            if distance >= 70.0:
                self._delete_on_release = True
                self.setOpacity(0.22)
                pen = QPen(QColor("#D84A3A"), 3)
                pen.setStyle(Qt.PenStyle.DashLine)
                self.setPen(pen)
                scene = self.scene()
                if isinstance(scene, GraphScene):
                    scene.connection_hint.emit(
                        "Отпустите правую кнопку — нить будет удалена."
                    )
            event.accept()
            return
        if self._rewire_endpoint is not None:
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.update_temporary_connection(event.scenePos())
            event.accept()
            return
        if self._drag_debug_marker:
            position = self._debug_position_at(event.scenePos())
            self.model["debug_position"] = position
            if self._drag_debug_kind == "break":
                self.model["breakpoint_position"] = position
            if self._drag_debug_kind == "probe" and isinstance(self.model.get("probe"), dict):
                self.model["probe"]["position"] = position
            self.update()
            event.accept()
            return
        if self._drag_handle is not None:
            points = [QPointF(p) for p in self._drag_points]
            index = self._drag_handle
            moved = points[index] + (event.scenePos() - self._drag_start)
            points[index] = moved
            if index - 1 > 1:
                if abs(points[index - 1].y() - self._drag_points[index].y()) < 0.01:
                    points[index - 1].setY(moved.y())
                else:
                    points[index - 1].setX(moved.x())
            if index + 1 < len(points) - 2:
                if abs(points[index + 1].y() - self._drag_points[index].y()) < 0.01:
                    points[index + 1].setY(moved.y())
                else:
                    points[index + 1].setX(moved.x())
            self._store_points(points, simplify=False)
            event.accept()
            return
        if self._drag_segment is not None:
            points = [QPointF(p) for p in self._drag_points]
            delta = event.scenePos() - self._drag_start
            index = self._drag_segment
            first, second = self._drag_points[index:index + 2]
            if abs(first.x() - second.x()) < 0.01:
                x = first.x() + delta.x()
                points[index].setX(x)
                points[index + 1].setX(x)
            else:
                y = first.y() + delta.y()
                points[index].setY(y)
                points[index + 1].setY(y)
            self._store_points(points, simplify=False)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.MouseButton.RightButton
            and self._right_drag_start is not None
        ):
            delete = self._delete_on_release
            self._right_drag_start = None
            self._delete_on_release = False
            self._suppress_next_context = True
            self.setOpacity(1.0)
            scene = self.scene()
            if delete and isinstance(scene, GraphScene):
                scene.remove_connection(self)
            else:
                self._apply_pen()
                self._show_context_menu(event.screenPos(), event.scenePos())
            event.accept()
            return
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._rewire_endpoint is not None
        ):
            scene = self.scene()
            self._rewire_endpoint = None
            self.setOpacity(1.0)
            if isinstance(scene, GraphScene):
                if self in scene.connections:
                    scene.connections.remove(self)
                scene.removeItem(self)
                scene.finish_temporary_connection(event.scenePos())
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._drag_debug_marker:
            self._drag_debug_marker = False
            position = self._debug_position_at(event.scenePos())
            self.model["debug_position"] = position
            if self._drag_debug_kind == "break":
                self.model["breakpoint_position"] = position
            if self._drag_debug_kind == "probe" and isinstance(self.model.get("probe"), dict):
                self.model["probe"]["position"] = position
            self._drag_debug_kind = None
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.changed_model.emit()
            self.update()
            event.accept()
            return
        if self._drag_segment is not None or self._drag_handle is not None:
            points = self._route_points()
            self._drag_segment = None
            self._drag_handle = None
            self._drag_start = None
            self._drag_points = None
            self._store_points(points, simplify=True)
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.changed_model.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.model.get("line_style") != "orthogonal":
            super().mouseDoubleClickEvent(event)
            return
        segment, points = self._nearest_segment(event.scenePos())
        if segment is None:
            return
        first, second = points[segment], points[segment + 1]
        click, offset = event.scenePos(), 40.0
        if abs(first.x() - second.x()) < 0.01:
            y = max(min(click.y(), max(first.y(), second.y())),
                    min(first.y(), second.y()))
            inserted = [QPointF(first.x(), y),
                        QPointF(first.x() + offset, y),
                        QPointF(first.x() + offset, second.y())]
        else:
            x = max(min(click.x(), max(first.x(), second.x())),
                    min(first.x(), second.x()))
            inserted = [QPointF(x, first.y()),
                        QPointF(x, first.y() + offset),
                        QPointF(second.x(), first.y() + offset)]
        points[segment + 1:segment + 1] = inserted
        self._store_points(points)
        scene = self.scene()
        if isinstance(scene, GraphScene):
            scene.changed_model.emit()
        event.accept()

    def _focus_endpoint(self, port: PortItem, label: str):
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return
        scene.clearSelection()
        port.node_item.setSelected(True)
        view = scene.views()[0] if scene.views() else None
        if view is not None:
            view.centerOn(port.node_item)
            view.setFocus()
        scene.connection_hint.emit(
            f"Показана {label}: «{port.node_item.spec.caption}» · "
            f"«{port.caption}»."
        )

    def _show_context_menu(self, screen_position, scene_position=None):
        menu = QMenu()
        heading = menu.addAction(
            f"{self.source.node_item.spec.caption} · {self.source.caption}  →  "
            f"{self.target.node_item.spec.caption} · {self.target.caption}"
        )
        heading.setEnabled(False)
        passport = menu.addAction("Паспорт связи…")
        go_source = menu.addAction("Перейти к началу нити")
        go_target = menu.addAction("Перейти к концу нити")
        menu.addSeparator()
        branch = menu.addAction("Создать ответвление здесь")
        breakpoint = menu.addAction(
            "Снять точку останова"
            if self.model.get("breakpoint")
            else "Поставить точку останова"
        )
        probe = menu.addAction("Добавить или изменить измерительную точку…")
        remove_probe = menu.addAction("Удалить измерительную точку")
        remove_probe.setEnabled(isinstance(self.model.get("probe"), dict))
        split = menu.addAction("Сделать разрыв с флажками")
        auto_route = menu.addAction("Автопроложить эту нить")
        reset = menu.addAction("Сбросить ручной маршрут")
        menu.addSeparator()
        orthogonal = menu.addAction("Ломаная под 90°")
        curve = menu.addAction("Плавная кривая")
        menu.addSeparator()
        delete = menu.addAction("Удалить нить")
        selected = menu.exec(screen_position)
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return
        if selected == passport:
            QMessageBox.information(
                scene.views()[0].window() if scene.views() else None,
                "Паспорт связи",
                self.passport_text(),
            )
        elif selected == go_source:
            self._focus_endpoint(self.source, "начальная точка")
        elif selected == go_target:
            self._focus_endpoint(self.target, "конечная точка")
        elif selected == branch:
            view = scene.views()[0] if scene.views() else None
            point = (
                scene_position
                if scene_position is not None
                else (
                    view.mapToScene(view.mapFromGlobal(screen_position))
                    if view else self.path().pointAtPercent(.5)
                )
            )
            scene.create_branch_on_connection(self, point)
        elif selected == breakpoint:
            self.model["breakpoint"] = not bool(self.model.get("breakpoint"))
            if self.model["breakpoint"] and scene_position is not None:
                position = self._debug_position_at(
                    scene_position
                )
                probe = self.model.get("probe")
                if isinstance(probe, dict):
                    probe_position = float(
                        probe.get("position", position)
                    )
                    if abs(probe_position - position) < 0.04:
                        position = min(0.96, position + 0.08)
                self.model["debug_position"] = position
                self.model["breakpoint_position"] = position
            self._apply_pen()
            scene.changed_model.emit()
            scene.connection_hint.emit(
                "Точка останова " + (
                    "установлена на нити." if self.model["breakpoint"]
                    else "снята с нити."
                )
            )
        elif selected == probe:
            default_name = scene.next_probe_name()
            current = self.model.get("probe")
            if isinstance(current, dict) and str(current.get("name", "")).strip():
                default_name = str(current["name"])
            parent = scene.views()[0] if scene.views() else None
            name, accepted = QInputDialog.getText(
                parent,
                "Измерительная точка",
                "Имя точки (например, 1.2 или result):",
                text=default_name,
            )
            name = name.strip()
            if accepted and name:
                position = (
                    self._debug_position_at(scene_position)
                    if scene_position is not None
                    else float(self.model.get("debug_position", 0.5))
                )
                if self.model.get("breakpoint"):
                    breakpoint_position = float(
                        self.model.get("breakpoint_position", position)
                    )
                    if abs(breakpoint_position - position) < 0.04:
                        position = max(0.04, position - 0.08)
                self.model["debug_position"] = position
                self.model["probe"] = {
                    "enabled": True,
                    "name": name,
                    "position": position,
                }
                self._apply_pen()
                scene.changed_model.emit()
                scene.connection_hint.emit(f"Измерительная точка «{name}» добавлена.")
        elif selected == remove_probe:
            self.model.pop("probe", None)
            self._apply_pen()
            scene.changed_model.emit()
            scene.connection_hint.emit("Измерительная точка удалена.")
        elif selected == split:
            has_probe = isinstance(self.model.get("probe"), dict)
            has_breakpoint = bool(self.model.get("breakpoint"))
            if has_probe or has_breakpoint:
                answer = QMessageBox.warning(
                    scene.views()[0] if scene.views() else None,
                    "На нити есть отладочные точки",
                    "На этой нити уже установлены точки наблюдения.\n\n"
                    "Удалить их и сделать разрыв?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    scene.connection_hint.emit(
                        "Разрыв отменён: отладочные точки оставлены."
                    )
                    return
                self.model.pop("probe", None)
                self.model.pop("breakpoint", None)
            scene.break_connection(self)
        elif selected == auto_route:
            scene.auto_route_connection(self)
        elif selected == reset:
            self.model["bends"] = []
            self.update_path()
            scene.changed_model.emit()
        elif selected == orthogonal:
            self.model["line_style"] = "orthogonal"
            self.update_path()
            scene.changed_model.emit()
        elif selected == curve:
            self.model["line_style"] = "curve"
            self.update_path()
            scene.changed_model.emit()
        elif selected == delete:
            scene.remove_connection(self)

    def contextMenuEvent(self, event):
        if self._suppress_next_context:
            self._suppress_next_context = False
            event.accept()
            return
        self._show_context_menu(event.screenPos(), event.scenePos())
        event.accept()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(self.pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())
        if self.model.get("breakpoint"):
            marker_point = self._marker_point("break")
            painter.setPen(QPen(QColor("#8B0000"), 1.5))
            painter.setBrush(QColor("#F44336"))
            painter.drawRect(QRectF(
                marker_point.x() - 6, marker_point.y() - 6, 12, 12
            ))
        probe = self.model.get("probe")
        if isinstance(probe, dict) and probe.get("enabled", True):
            marker_point = self._marker_point("probe")
            painter.setPen(QPen(QColor("#4A148C"), 1.5))
            painter.setBrush(QColor("#CE93D8"))
            painter.drawEllipse(marker_point, 7, 7)
            label = str(probe.get("name", "")).strip()
            if label:
                painter.setPen(QColor("#4A148C"))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(
                    marker_point + QPointF(10, -8), label
                )
        if self._pulse_started:
            progress = min(
                1.0,
                max(
                    0.0,
                    (
                        (time.monotonic() - self._pulse_started)
                        / self._pulse_duration
                        if self._pulse_duration > 0
                        else 0.0
                    ),
                ),
            )
            pulse_point = self.path().pointAtPercent(progress)
            painter.setPen(QPen(QColor("#FFFFFF"), 2.0))
            painter.setBrush(self.debug_pulse_color())
            painter.drawEllipse(pulse_point, 7, 7)
            painter.setPen(QPen(QColor("#006064"), 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(pulse_point, 8.5, 8.5)


class HelperItem(QGraphicsRectItem):
    """Настраиваемый графический объект схемы без портов."""

    COLORS = {
        "note": ("#FFF2A8", "#B79F31"),
        "title": ("#DCEAF7", "#6B9AC0"),
        "group": ("#E4E4E4", "#888888"),
        "legend": ("#E6F4EA", "#72A77A"),
        "warning": ("#FDE2E2", "#C66A6A"),
        "separator": ("transparent", "#888888"),
    }

    def __init__(self, graph_scene, model):
        self.graph_scene = graph_scene
        self.model = model
        legacy = self.COLORS.get(str(model.get("kind", "note")), self.COLORS["note"])
        model.setdefault("fill_color", legacy[0])
        model.setdefault("border_color", legacy[1])
        model.setdefault("text_color", "#303030")
        model.setdefault("fill_alpha", 100)
        model.setdefault("border_alpha", 100)
        model.setdefault("text_alpha", 100)
        model.setdefault("font_size", 9)
        model.setdefault("title_font_size", model.get("font_size", 9))
        model.setdefault("body_font_size", model.get("font_size", 9))
        model.setdefault("font_bold", False)
        model.setdefault("opacity", 100)
        model.setdefault("text_x", 8)
        model.setdefault("text_y", 6)
        model.setdefault("shape", "rounded")
        model.setdefault("corner_radius", 6)
        model.setdefault("border_width", 1)
        model.setdefault("border_style", "solid")
        model.setdefault("title", "Помощник")
        model.setdefault("text", "Новая заметка")
        super().__init__(
            0, 0,
            max(24.0, float(model.get("width", 220))),
            max(10.0, float(model.get("height", 70))),
        )
        self.setPos(float(model.get("x", 0)), float(model.get("y", 0)))
        self.setOpacity(max(0.05, min(1.0, float(model.get("opacity", 100)) / 100)))
        self.setZValue(0)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
        )
        self.setAcceptHoverEvents(True)
        self._resizing = False
        self._resize_start = None
        self._resize_origin = None
        self._resize_size = None
        self.setToolTip(
            f"{'Текст' if model.get('kind') == 'text' else 'Фигура'}: "
            f"{model.get('title', 'без названия')}\n"
            "ПКМ — оформление. Для фигуры тяните правый нижний угол."
        )

    def _near_resize_handle(self, position):
        if self.model.get("kind") == "text":
            return False
        rect = self.rect()
        return (
            position.x() >= rect.right() - 16
            and position.y() >= rect.bottom() - 16
        )

    def hoverMoveEvent(self, event):
        if self._near_resize_handle(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._near_resize_handle(event.pos())
        ):
            self._resizing = True
            self._resize_start = QPointF(event.pos())
            self._resize_origin = QPointF(self.pos())
            self._resize_size = QSizeF(
                self.rect().width(), self.rect().height()
            )
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            self.setSelected(True)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_start is not None:
            # event.pos() is in the helper's own coordinates.  Using local
            # coordinates keeps resizing correct at every canvas zoom and
            # prevents the normal movable-item handler from winning the drag.
            width = max(24.0, float(event.pos().x()))
            height = max(10.0, float(event.pos().y()))
            self.prepareGeometryChange()
            self.setRect(0, 0, width, height)
            self.model["width"] = round(width, 1)
            self.model["height"] = round(height, 1)
            self.update()
            self.graph_scene.changed_model.emit()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing and event.button() == Qt.MouseButton.LeftButton:
            self._resizing = False
            self._resize_start = None
            self._resize_origin = None
            self._resize_size = None
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            self.unsetCursor()
            self.graph_scene.changed_model.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.model["x"] = round(value.x(), 1)
            self.model["y"] = round(value.y(), 1)
            self.graph_scene.changed_model.emit()
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update()
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit = menu.addAction("Настроить помощник…")
        duplicate = menu.addAction("Дублировать")
        menu.addSeparator()
        delete = menu.addAction("Удалить помощник")
        selected = menu.exec(event.screenPos())
        if selected == edit:
            self.edit_properties()
        elif selected == duplicate:
            model = copy.deepcopy(self.model)
            model["id"] = uuid.uuid4().hex[:10]
            model["x"] = float(model.get("x", 0)) + 30
            model["y"] = float(model.get("y", 0)) + 30
            self.graph_scene.add_helper(model)
        elif selected == delete:
            self.graph_scene.remove_helper(self)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_properties()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    @staticmethod
    def _color_button(color):
        button = QPushButton("Палитра…")
        button.setFixedWidth(112)
        button.setToolTip("Открыть палитру цветов")
        button.setProperty("colorValue", str(color))
        button.setStyleSheet(
            f"background:{color}; color:#202020; border:1px solid #555; "
            "padding:3px 8px;"
        )
        return button

    def edit_properties(self):
        dialog = QDialog()
        dialog.setWindowTitle("Настройка помощника")
        dialog.resize(430, 520)
        form = QFormLayout(dialog)
        title = QLineEdit(str(self.model.get("title", "")))
        text = QPlainTextEdit(str(self.model.get("text", "")))
        text.setMinimumHeight(90)
        width = QSpinBox()
        width.setRange(24, 4000)
        width.setValue(int(self.rect().width()))
        height = QSpinBox()
        height.setRange(10, 3000)
        height.setValue(int(self.rect().height()))
        font_size = QSpinBox()
        font_size.setRange(6, 96)
        font_size.setValue(int(self.model.get("font_size", 9)))
        title_font_size = QSpinBox()
        title_font_size.setRange(6, 96)
        title_font_size.setValue(int(self.model.get("title_font_size", 9)))
        body_font_size = QSpinBox()
        body_font_size.setRange(6, 96)
        body_font_size.setValue(int(self.model.get("body_font_size", 9)))
        border_width = QSpinBox()
        border_width.setRange(0, 30)
        border_width.setValue(int(self.model.get("border_width", 1)))
        opacity = QSpinBox()
        opacity.setRange(5, 100)
        opacity.setSuffix(" %")
        opacity.setValue(int(self.model.get("opacity", 100)))
        fill_alpha = QSpinBox()
        fill_alpha.setRange(0, 100)
        fill_alpha.setSuffix(" %")
        fill_alpha.setValue(int(self.model.get("fill_alpha", 100)))
        border_alpha = QSpinBox()
        border_alpha.setRange(0, 100)
        border_alpha.setSuffix(" %")
        border_alpha.setValue(int(self.model.get("border_alpha", 100)))
        text_alpha = QSpinBox()
        text_alpha.setRange(0, 100)
        text_alpha.setSuffix(" %")
        text_alpha.setValue(int(self.model.get("text_alpha", 100)))
        text_x = QSpinBox()
        text_x.setRange(-2000, 2000)
        text_x.setValue(int(self.model.get("text_x", 8)))
        text_y = QSpinBox()
        text_y.setRange(-2000, 2000)
        text_y.setValue(int(self.model.get("text_y", 6)))
        shape = QComboBox()
        shape.addItem("Без фигуры", "none")
        shape.addItem("Прямоугольник", "rect")
        shape.addItem("Скруглённый прямоугольник", "rounded")
        shape.addItem("Эллипс / круг", "ellipse")
        shape.addItem("Ромб", "diamond")
        shape.setCurrentIndex(max(0, shape.findData(self.model.get("shape", "rounded"))))
        border_style = QComboBox()
        border_style.addItem("Сплошная", "solid")
        border_style.addItem("Штриховая", "dash")
        border_style.setCurrentIndex(max(0, border_style.findData(self.model.get("border_style", "solid"))))
        bold = QCheckBox("Полужирный")
        bold.setChecked(bool(self.model.get("font_bold", False)))
        is_text = self.model.get("kind") == "text"
        is_shape = self.model.get("kind") == "shape"
        title.setEnabled(not is_shape)
        text.setEnabled(not is_shape)
        shape.setEnabled(not is_text)
        corner = QSpinBox()
        corner.setRange(0, 100)
        corner.setValue(int(self.model.get("corner_radius", 6)))
        colors = {}
        color_fields = (
            (("fill_color", "Цвет заливки"), ("border_color", "Цвет рамки"))
            if not is_text else ()
        ) + (("text_color", "Цвет текста"),)
        for key, label in color_fields:
            button = self._color_button(str(self.model.get(key)))
            colors[key] = button
            button.clicked.connect(
                lambda _checked=False, target=button, name=key: self._choose_color(
                    target, name
                )
            )
            form.addRow(label, button)
        if not is_shape:
            form.addRow("Название", title)
            form.addRow("Текст", text)
        form.addRow("Форма", shape)
        form.addRow("Ширина", width)
        form.addRow("Высота", height)
        if not is_shape:
            form.addRow("Размер шрифта", font_size)
            form.addRow("Размер заголовка", title_font_size)
            form.addRow("Размер текста", body_font_size)
            form.addRow("Смещение текста по X", text_x)
            form.addRow("Смещение текста по Y", text_y)
        form.addRow("Скругление", corner)
        form.addRow("Толщина рамки", border_width)
        form.addRow("Стиль рамки", border_style)
        form.addRow("Общая прозрачность", opacity)
        if not is_text:
            form.addRow("Прозрачность заливки", fill_alpha)
            form.addRow("Прозрачность рамки", border_alpha)
        if not is_shape:
            form.addRow("Прозрачность текста", text_alpha)
            form.addRow("", bold)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.model.update(
            {
                "title": title.text(),
                "text": text.toPlainText(),
                "width": width.value(),
                "height": height.value(),
                "font_size": font_size.value(),
                "title_font_size": title_font_size.value(),
                "body_font_size": body_font_size.value(),
                "font_bold": bold.isChecked(),
                "opacity": opacity.value(),
                "fill_alpha": fill_alpha.value(),
                "border_alpha": border_alpha.value(),
                "text_alpha": text_alpha.value(),
                "text_x": text_x.value(),
                "text_y": text_y.value(),
                "shape": shape.currentData(),
                "corner_radius": corner.value(),
                "border_width": border_width.value(),
                "border_style": border_style.currentData(),
                **{
                    key: str(button.property("colorValue"))
                    for key, button in colors.items()
                },
            }
        )
        self.prepareGeometryChange()
        self.setRect(0, 0, width.value(), height.value())
        self.setOpacity(opacity.value() / 100)
        self.setToolTip(
            f"Помощник: {self.model.get('title', '')}\n"
            "ПКМ — оформление, размер, цвет, форма и прозрачность."
        )
        self.update()
        self.graph_scene.changed_model.emit()

    def _choose_color(self, button, key):
        current = QColor(str(self.model.get(key, "#FFFFFF")))
        parent = None
        views = self.graph_scene.views() if self.graph_scene is not None else []
        if views:
            parent = views[0].viewport()
        try:
            color = QColorDialog.getColor(
                current,
                parent,
                "Выберите цвет",
                QColorDialog.ColorDialogOption.ShowAlphaChannel,
            )
        except (AttributeError, TypeError):
            color = QColorDialog.getColor(current, parent, "Выберите цвет")
        if color.isValid():
            name = color.name(QColor.NameFormat.HexArgb)
            button.setProperty("colorValue", name)
            button.setStyleSheet(f"background:{name}; border:1px solid #555;")

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        is_text = self.model.get("kind") == "text"
        is_shape = self.model.get("kind") == "shape"
        fill = QColor(str(self.model.get("fill_color", "#FFF2A8")))
        fill.setAlpha(round(255 * int(self.model.get("fill_alpha", 100)) / 100))
        border = QColor(str(self.model.get("border_color", "#B79F31")))
        border.setAlpha(round(255 * int(self.model.get("border_alpha", 100)) / 100))
        text_color = QColor(str(self.model.get("text_color", "#303030")))
        text_color.setAlpha(round(255 * int(self.model.get("text_alpha", 100)) / 100))
        if not is_text:
            painter.setBrush(QColor("#D0D0D0") if self.isSelected() else fill)
            pen = QPen(
                QColor("#555555") if self.isSelected() else border,
                max(0, int(self.model.get("border_width", 1)))
                + (1 if self.isSelected() else 0),
            )
            if self.model.get("border_style") == "dash":
                pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            shape = str(self.model.get("shape", "rounded"))
            if shape == "ellipse":
                painter.drawEllipse(self.rect())
            elif shape == "diamond":
                rect = self.rect()
                painter.drawPolygon(
                    QPolygonF(
                        [
                            QPointF(rect.center().x(), rect.top()),
                            QPointF(rect.right(), rect.center().y()),
                            QPointF(rect.center().x(), rect.bottom()),
                            QPointF(rect.left(), rect.center().y()),
                        ]
                    )
                )
            elif shape == "rect":
                painter.drawRect(self.rect())
            else:
                painter.drawRoundedRect(
                    self.rect(), float(self.model.get("corner_radius", 6)),
                    float(self.model.get("corner_radius", 6)),
                )
        elif self.isSelected():
            pen = QPen(QColor("#6A6A6A"), 1, Qt.PenStyle.DashLine)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawRect(self.rect())
        painter.setPen(text_color)
        title_font = QFont(
            str(self.model.get("font_family", "Arial")),
            int(self.model.get("title_font_size", self.model.get("font_size", 9))),
        )
        title_font.setBold(bool(self.model.get("font_bold", False)))
        body_font = QFont(title_font)
        body_font.setPointSize(
            int(self.model.get("body_font_size", self.model.get("font_size", 9)))
        )
        x_offset = int(self.model.get("text_x", 8))
        y_offset = int(self.model.get("text_y", 6))
        text_rect = self.rect().adjusted(x_offset, y_offset, -8, -6)
        if not is_shape:
            painter.setFont(title_font)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignHCenter
                | Qt.AlignmentFlag.AlignTop,
                str(self.model.get("title", "")).strip(),
            )
            painter.setFont(body_font)
            body_rect = text_rect.adjusted(0, title_font.pointSize() + 5, 0, 0)
            painter.drawText(
                body_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
                | Qt.TextFlag.TextWordWrap,
                str(self.model.get("text", "")).strip(),
            )
        if is_shape and self.isSelected():
            painter.setPen(QPen(QColor("#404040"), 1))
            painter.setBrush(QColor("#404040"))
            painter.drawRect(
                self.rect().right() - 8,
                self.rect().bottom() - 8,
                7,
                7,
            )


class BreakLinkItem(QGraphicsLineItem):
    """The real wire from a node port to a movable break flag."""

    def __init__(self, graph_scene, flag, port):
        super().__init__()
        self.graph_scene = graph_scene
        self.flag = flag
        self.port = port
        self.setZValue(6)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.update_line()

    def update_line(self):
        self.setLine(QLineF(
            self.port.scenePos(), self.flag.connection_scene_pos()
        ))

    def paint(self, painter, option, widget=None):
        kind = self.port.kind
        color = EVENT_COLOR if kind in {"event_out", "work_in"} else DATA_COLOR
        painter.setPen(QPen(color, 2.2))
        super().paint(painter, option, widget)


class BreakGuideItem(QGraphicsLineItem):
    """Dashed correspondence line shown while a break flag is hovered."""

    def __init__(self):
        super().__init__()
        self.setZValue(7)
        self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        pen = QPen(QColor("#777777"), 1.2, Qt.PenStyle.DashLine)
        self.setPen(pen)
        self.setVisible(False)


class BreakFlagItem(QGraphicsRectItem):
    """Fixed-orientation OUT/IN-shaped flag with a point on its outline."""

    # The visible shape never rotates.  Only its position changes.  The node
    # connection point is on the outline, just like a normal node port.
    OUT_CONNECTION = QPointF(-22, 0)
    IN_CONNECTION = QPointF(22, 0)

    def __init__(self, graph_scene, model, port, side: str):
        super().__init__(-28, -11, 56, 22)
        self.graph_scene = graph_scene
        self.model = model
        self.port = port
        self.side = side
        self._hovered = False
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(8)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        key = f"{side}_flag_pos"
        saved = model.get(key)
        if isinstance(saved, (list, tuple)) and len(saved) == 2:
            self.setPos(float(saved[0]), float(saved[1]))
        else:
            node_center = port.node_item.sceneBoundingRect().center()
            vector = port.scenePos() - node_center
            # Initial placement is away from the node, but the flag remains
            # horizontal when the user later drags it anywhere on the canvas.
            if abs(vector.x()) >= abs(vector.y()):
                offset = QPointF(42 if vector.x() >= 0 else -42, 0)
            else:
                offset = QPointF(0, 42 if vector.y() >= 0 else -42)
            self.setPos(port.scenePos() + offset)
            model[key] = [round(self.x(), 1), round(self.y(), 1)]
        self.setToolTip(
            f"Флажок разрыва {model.get('break_name', 'B?')}\n"
            f"{port.node_item.spec.caption}: {port.caption}\n"
            "Перетащите флажок. Наведите курсор для пунктирной связи."
        )

    def connection_scene_pos(self):
        local = self.OUT_CONNECTION if self.side == "out" else self.IN_CONNECTION
        return self.mapToScene(local)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.model[f"{self.side}_flag_pos"] = [
                round(value.x(), 1), round(value.y(), 1)
            ]
            self.graph_scene.refresh_break_links()
            self.graph_scene.changed_model.emit()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.graph_scene.set_break_hover(self.model, True)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.graph_scene.set_break_hover(self.model, False)
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu()
            restore = menu.addAction("Восстановить нить")
            if menu.exec(event.screenPos()) == restore:
                self.graph_scene.restore_broken_connection(self.model)
            event.accept()
            return
        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        signal_color = (
            EVENT_COLOR
            if self.port.kind in {"event_out", "work_in"}
            else DATA_COLOR
        )
        outline = QPen(
            QColor("#1E88E5") if self._hovered else QColor("#555555"),
            1.4,
        )
        painter.setPen(outline)
        painter.setBrush(
            QColor("#DDEBFA") if self._hovered else QColor("#FFFFFF")
        )
        if self.side == "out":
            # Point faces away from the OUT connection point on the left.
            shape = QPolygonF([
                QPointF(-22, -9), QPointF(16, -9), QPointF(27, 0),
                QPointF(16, 9), QPointF(-22, 9),
            ])
        else:
            # Notch faces away from the IN connection point on the right.
            shape = QPolygonF([
                QPointF(22, -9), QPointF(-16, -9), QPointF(-7, 0),
                QPointF(-16, 9), QPointF(22, 9),
            ])
        painter.drawPolygon(shape)
        painter.setPen(QPen(signal_color.darker(140), 1))
        painter.setBrush(signal_color)
        connection = (
            self.OUT_CONNECTION if self.side == "out" else self.IN_CONNECTION
        )
        painter.drawEllipse(connection, 3.7, 3.7)
        painter.setPen(QColor("#303030"))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(
            QRectF(-15, -8, 30, 16),
            Qt.AlignmentFlag.AlignCenter,
            str(self.model.get("break_name", "B?")),
        )


class GraphScene(QGraphicsScene):
    node_selected = Signal(object)
    changed_model = Signal()
    project_loaded = Signal()
    connection_hint = Signal(str)
    component_dropped = Signal(str, QPointF)
    helper_dropped = Signal(str, QPointF)
    container_dropped = Signal(str, QPointF)
    node_action_requested = Signal(str, str)
    canvas_action_requested = Signal(str, QPointF)

    def __init__(self):
        super().__init__()
        settings = QSettings(
            "VisualPythonBuilder", "VisualPythonBuilder"
        )
        self.line_style = str(
            settings.value("lineStyle", "orthogonal")
        )
        if self.line_style not in {"curve", "orthogonal"}:
            self.line_style = "orthogonal"
        self.setSceneRect(-6000, -6000, 12000, 12000)
        self.nodes: dict[str, NodeItem] = {}
        self.connections: list[ConnectionItem] = []
        self.helpers: list[HelperItem] = []
        self.broken_connections: list[dict[str, Any]] = []
        self.break_flags: dict[str, tuple[BreakFlagItem, BreakFlagItem]] = {}
        self.break_links: dict[str, tuple[BreakLinkItem, BreakLinkItem]] = {}
        self.break_guides: dict[str, BreakGuideItem] = {}
        self.pending_port: PortItem | None = None
        self.fixed_target: PortItem | None = None
        self.temporary_connection: QGraphicsPathItem | None = None
        self.rewire_backup: dict[str, Any] | None = None
        self.debug_pulse_duration = 700
        self._debug_animation_timer = QTimer(self)
        self._debug_animation_timer.setInterval(30)
        self._debug_animation_timer.timeout.connect(
            self._advance_debug_animation
        )
        self.snap_enabled = True
        self.snap_size = 10
        self.in_container = False
        self.interface_frame: QGraphicsRectItem | None = None
        self.interface_frame_inner: QGraphicsRectItem | None = None
        self.interface_frame_rect: QRectF | None = None
        self.interface_view_scale = 1.0
        self._positioning_interface_points = False
        self.selectionChanged.connect(self._selection_changed)

    def trigger_debug_flow(self, node_id: str, port: str) -> bool:
        for item in self.connections:
            item.clear_debug_pulse()
        matched = False
        for item in self.connections:
            if (
                str(item.model.get("from_node")) == str(node_id)
                and str(item.model.get("from_port")) == str(port)
            ):
                item.start_debug_pulse(self.debug_pulse_duration)
                matched = True
        if matched and not self._debug_animation_timer.isActive():
            self._debug_animation_timer.start()
        return matched

    def clear_debug_animation(self):
        for item in self.connections:
            item.clear_debug_pulse()
        self._debug_animation_timer.stop()

    def _advance_debug_animation(self):
        now = time.monotonic()
        active = False
        for item in self.connections:
            active = item.advance_debug_pulse(now) or active
        if not active:
            self._debug_animation_timer.stop()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor("#E3E8ED"))
        minor = QPen(QColor("#D2D9E0"), 1)
        major = QPen(QColor("#B8C3CE"), 1)
        left = int(rect.left()) - (int(rect.left()) % 20)
        top = int(rect.top()) - (int(rect.top()) % 20)
        painter.setPen(minor)
        x = left
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += 20
        y = top
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += 20
        painter.setPen(major)
        x = left - (left % 100)
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += 100
        y = top - (top % 100)
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += 100

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(
            "application/x-visual-python-component"
        ):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(
            "application/x-visual-python-helper"
        ):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(
            "application/x-visual-python-container"
        ):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(
            "application/x-visual-python-component"
        ):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(
            "application/x-visual-python-helper"
        ):
            event.acceptProposedAction()
            return
        if event.mimeData().hasFormat(
            "application/x-visual-python-container"
        ):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasFormat("application/x-visual-python-component"):
            type_name = bytes(
                mime.data("application/x-visual-python-component")
            ).decode("utf-8")
            self.component_dropped.emit(
                type_name, event.scenePos()
            )
            event.acceptProposedAction()
            return
        if mime.hasFormat("application/x-visual-python-helper"):
            helper_type = bytes(
                mime.data("application/x-visual-python-helper")
            ).decode("utf-8")
            self.helper_dropped.emit(helper_type, event.scenePos())
            event.acceptProposedAction()
            return
        if mime.hasFormat("application/x-visual-python-container"):
            template_id = bytes(
                mime.data("application/x-visual-python-container")
            ).decode("utf-8")
            self.container_dropped.emit(template_id, event.scenePos())
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.RightButton
            and (
                self.pending_port is not None
                or self.fixed_target is not None
            )
        ):
            self.cancel_temporary_connection()
            self.connection_hint.emit("Создание связи отменено.")
            event.accept()
            return
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        item = (
            self.itemAt(
                event.scenePos(), self.views()[0].transform()
            )
            if self.views()
            else None
        )
        if isinstance(item, HelperItem):
            item.contextMenuEvent(event)
            return
        if isinstance(item, (ConnectionItem, NodeItem, PortItem)):
            super().contextMenuEvent(event)
            return

        menu = QMenu()
        paste = menu.addAction("Вставить")
        paste.setEnabled(bool(self.views()))
        select_all = menu.addAction("Выделить все элементы")
        select_all.setEnabled(bool(self.nodes))
        clear_selection = menu.addAction("Снять выделение")
        clear_selection.setEnabled(bool(self.selectedItems()))
        menu.addSeparator()

        view_menu = menu.addMenu("Вид")
        fit = view_menu.addAction("Показать всю схему")
        reset_zoom = view_menu.addAction("Масштаб 100%")
        snap = view_menu.addAction("Привязка к сетке")
        snap.setCheckable(True)
        snap.setChecked(self.snap_enabled)

        wires_menu = menu.addMenu("Нити")
        auto_all = wires_menu.addAction("Автопроложить все нити")
        smart_layout = wires_menu.addAction(
            "Умная расстановка нод и нитей"
        )
        smart_layout.setToolTip(
            "Разложить ноды по слоям, уменьшить переплетения и "
            "проложить короткие маршруты"
        )
        wires_menu.addSeparator()
        orthogonal = wires_menu.addAction("Ломаные под 90°")
        orthogonal.setCheckable(True)
        orthogonal.setChecked(self.line_style == "orthogonal")
        curve = wires_menu.addAction("Плавные кривые")
        curve.setCheckable(True)
        curve.setChecked(self.line_style == "curve")

        menu.addSeparator()
        selected_count=len([i for i in self.selectedItems() if isinstance(i,NodeItem)])
        create_container=menu.addAction("Создать пустой контейнер")
        pack_container=menu.addAction(f"Создать контейнер из выделенного ({selected_count})"); pack_container.setEnabled(selected_count>0)
        return_container=menu.addAction("Вернуться из контейнера"); return_container.setEnabled(self.in_container)
        menu.addSeparator()
        validate = menu.addAction("Проверить проект")
        selected = menu.exec(event.screenPos())
        position = event.scenePos()
        actions = {
            paste: "paste",
            select_all: "select_all",
            clear_selection: "clear_selection",
            fit: "fit",
            reset_zoom: "reset_zoom",
            snap: "toggle_snap",
            auto_all: "auto_route_all",
            smart_layout: "smart_layout",
            orthogonal: "orthogonal",
            curve: "curve", create_container:"create_container", pack_container:"pack_container", return_container:"return_container",
            validate: "validate",
        }
        action = actions.get(selected)
        if action:
            self.canvas_action_requested.emit(action, position)
        event.accept()

    def add_node(self, model: dict[str, Any]):
        normalize_node_model(model)
        item = NodeItem(model, COMPONENTS[model["type"]])
        self.nodes[model["id"]] = item
        self.addItem(item)
        if (
            self.in_container
            and item.is_container_proxy
            and self.interface_frame_rect is not None
        ):
            self._layout_container_interface_points()
        self.changed_model.emit()
        return item

    def _build_container_interface_frame(self):
        fallback = QRectF(-450.0, -300.0, 900.0, 600.0)
        self.interface_frame_rect = fallback
        self.interface_frame = QGraphicsRectItem(fallback)
        outer_pen = QPen(QColor("#183B63"), 3)
        outer_pen.setCosmetic(True)
        self.interface_frame.setPen(outer_pen)
        self.interface_frame.setBrush(Qt.BrushStyle.NoBrush)
        self.interface_frame.setZValue(-5)
        self.addItem(self.interface_frame)
        self.interface_frame_inner = QGraphicsRectItem(
            fallback.adjusted(6, 6, -6, -6)
        )
        inner_pen = QPen(QColor("#6F91B5"), 1)
        inner_pen.setCosmetic(True)
        self.interface_frame_inner.setPen(inner_pen)
        self.interface_frame_inner.setBrush(Qt.BrushStyle.NoBrush)
        self.interface_frame_inner.setZValue(-5)
        self.addItem(self.interface_frame_inner)
        view = self.views()[0] if self.views() else None
        if view is not None:
            self.update_container_interface_frame(view)
        else:
            self._layout_container_interface_points()

    def update_container_interface_frame(self, view=None):
        if not self.in_container or self.interface_frame is None:
            return
        if view is None:
            view = self.views()[0] if self.views() else None
        if view is None or not view.viewport().width() or not view.viewport().height():
            return
        visible = view.mapToScene(view.viewport().rect()).boundingRect()
        scale_x = max(0.01, abs(view.transform().m11()))
        scale_y = max(0.01, abs(view.transform().m22()))
        frame = visible.adjusted(
            18.0 / scale_x, 18.0 / scale_y,
            -18.0 / scale_x, -18.0 / scale_y,
        )
        self.interface_view_scale = scale_x
        self.interface_frame_rect = frame
        self.interface_frame.setRect(frame)
        if self.interface_frame_inner is not None:
            inset_x = 6.0 / scale_x
            inset_y = 6.0 / scale_y
            self.interface_frame_inner.setRect(
                frame.adjusted(inset_x, inset_y, -inset_x, -inset_y)
            )
        self._layout_container_interface_points()
        self._constrain_nodes_to_frame()
        self.refresh_connections()
        self.update()

    def _clamp_node_position(self, node, position):
        """Keep ordinary nodes inside the visible container work area."""
        frame = self.interface_frame_rect
        if frame is None or node.is_container_proxy:
            return QPointF(position)
        scale = max(0.01, self.interface_view_scale)
        margin = 10.0 / scale
        left = frame.left() + margin
        top = frame.top() + margin
        right = frame.right() - margin - node.width
        bottom = frame.bottom() - margin - node.height
        return QPointF(
            min(max(float(position.x()), left), max(left, right)),
            min(max(float(position.y()), top), max(top, bottom)),
        )

    def _constrain_nodes_to_frame(self):
        if self.interface_frame_rect is None:
            return
        for node in self.nodes.values():
            if node.is_container_proxy:
                continue
            bounded = self._clamp_node_position(node, node.pos())
            if QLineF(node.pos(), bounded).length() > 0.01:
                node.setPos(bounded)

    def _point_on_container_frame(self, side: str, offset: float) -> QPointF:
        """Return a point that lies exactly on the current container frame."""
        frame = self.interface_frame_rect
        if frame is None:
            return QPointF()
        offset = min(max(float(offset), 0.02), 0.98)
        if side == "left":
            return QPointF(frame.left(), frame.top() + offset * frame.height())
        if side == "right":
            return QPointF(frame.right(), frame.top() + offset * frame.height())
        if side == "top":
            return QPointF(frame.left() + offset * frame.width(), frame.top())
        return QPointF(frame.left() + offset * frame.width(), frame.bottom())

    def container_frame_anchor(self, port: PortItem) -> QPointF:
        """Project a proxy port onto the border so a wire cannot drift away."""
        frame = self.interface_frame_rect
        node = port.node_item
        if frame is None or not node.is_container_proxy:
            return port.scenePos()
        raw = port.scenePos()
        if node.proxy_side in {"left", "right"}:
            offset = (raw.y() - frame.top()) / max(1.0, frame.height())
        else:
            offset = (raw.x() - frame.left()) / max(1.0, frame.width())
        return self._point_on_container_frame(node.proxy_side, offset)

    def _layout_container_interface_points(self):
        frame = self.interface_frame_rect
        if frame is None:
            return
        scale = max(0.01, self.interface_view_scale)
        self._positioning_interface_points = True
        try:
            for side in ("left", "right", "top", "bottom"):
                points = sorted(
                    (
                        node for node in self.nodes.values()
                        if node.is_container_proxy and node.proxy_side == side
                    ),
                    key=lambda node: (
                        float(node.model.get("y", 0))
                        if side in {"left", "right"}
                        else float(node.model.get("x", 0)),
                        str(node.model.get("id", "")),
                    ),
                )
                for index, node in enumerate(points):
                    raw_offset = node.model.get("properties", {}).get(
                        "_frame_offset"
                    )
                    try:
                        offset = min(max(float(raw_offset), 0.05), 0.95)
                    except (TypeError, ValueError):
                        offset = (index + 1) / (len(points) + 1)
                    node.model.setdefault("properties", {})["_frame_offset"] = round(
                        offset, 4
                    )
                    node.setScale(1.0 / scale)
                    port = next(iter(node.ports.values()), None)
                    anchor_x = (
                        port.pos().x() if port is not None else node.width / 2
                    ) / scale
                    anchor_y = (
                        port.pos().y() if port is not None else node.height / 2
                    ) / scale
                    point = self._point_on_container_frame(side, offset)
                    node.setPos(point - QPointF(anchor_x, anchor_y))
                    # Do not rely on a hand-derived transform alone: after
                    # scaling, force the visible port centre onto the border.
                    if port is not None:
                        correction = point - port.scenePos()
                        if QLineF(QPointF(), correction).length() > 0.01:
                            node.setPos(node.pos() + correction)
        finally:
            self._positioning_interface_points = False

    def add_helper(self, model: dict[str, Any]):
        model.setdefault("id", uuid.uuid4().hex[:10])
        model.setdefault("kind", "note")
        item = HelperItem(self, model)
        self.helpers.append(item)
        self.addItem(item)
        self.clearSelection()
        item.setSelected(True)
        self.changed_model.emit()
        return item

    def remove_helper(self, item: HelperItem):
        if item in self.helpers:
            self.helpers.remove(item)
            self.removeItem(item)
            self.changed_model.emit()
            self.connection_hint.emit("Помощник удалён.")

    def add_connection(self, model: dict[str, Any]):
        if model.get("broken"):
            self._add_broken_connection(model)
            return
        source_node = self.nodes.get(model["from_node"])
        target_node = self.nodes.get(model["to_node"])
        if not source_node or not target_node:
            return
        source = source_node.port_for(model["from_port"], outgoing=True)
        target = target_node.port_for(model["to_port"], outgoing=False)
        if not source or not target:
            return
        model.setdefault("line_style", self.line_style)
        model.setdefault("bends", model.pop("points", []))
        model.setdefault("breakpoint", False)
        if "probe" in model and not isinstance(model.get("probe"), dict):
            model.pop("probe", None)
        item = ConnectionItem(model, source, target)
        self.connections.append(item)
        self.addItem(item)

    def _add_broken_connection(self, model):
        source_node = self.nodes.get(model.get("from_node"))
        target_node = self.nodes.get(model.get("to_node"))
        if not source_node or not target_node:
            return
        source = source_node.port_for(model.get("from_port"), outgoing=True)
        target = target_node.port_for(model.get("to_port"), outgoing=False)
        if not source or not target:
            return
        break_id = str(model.setdefault("break_id", uuid.uuid4().hex[:10]))
        model.setdefault("break_name", self._next_break_name())
        if model not in self.broken_connections:
            self.broken_connections.append(model)
        out_flag = BreakFlagItem(self, model, source, "out")
        in_flag = BreakFlagItem(self, model, target, "in")
        self.break_flags[break_id] = (out_flag, in_flag)
        out_link = BreakLinkItem(self, out_flag, source)
        in_link = BreakLinkItem(self, in_flag, target)
        guide = BreakGuideItem()
        self.break_links[break_id] = (out_link, in_link)
        self.break_guides[break_id] = guide
        self.addItem(out_link)
        self.addItem(in_link)
        self.addItem(out_flag)
        self.addItem(in_flag)
        self.addItem(guide)

    def refresh_break_links(self):
        for links in self.break_links.values():
            for link in links:
                link.update_line()
        for break_id, guide in self.break_guides.items():
            pair = self.break_flags.get(break_id)
            if pair:
                guide.setLine(QLineF(
                    pair[0].connection_scene_pos(),
                    pair[1].connection_scene_pos(),
                ))

    def set_break_hover(self, model, hovered: bool):
        guide = self.break_guides.get(str(model.get("break_id", "")))
        pair = self.break_flags.get(str(model.get("break_id", "")))
        if guide and pair:
            guide.setLine(QLineF(
                pair[0].connection_scene_pos(),
                pair[1].connection_scene_pos(),
            ))
            guide.setVisible(hovered)
            guide.update()

    def _next_break_name(self):
        used = {
            str(model.get("break_name", ""))
            for model in self.broken_connections
        }
        index = 1
        while f"B{index}" in used:
            index += 1
        return f"B{index}"

    def break_connection(self, item: ConnectionItem):
        if item not in self.connections:
            return
        model = copy.deepcopy(item.model)
        model["broken"] = True
        model["break_id"] = uuid.uuid4().hex[:10]
        model["break_name"] = self._next_break_name()
        self.removeItem(item)
        self.connections.remove(item)
        self._add_broken_connection(model)
        self.changed_model.emit()
        self.connection_hint.emit(
            f"Нить разорвана: {model['break_name']} OUT ↔ IN."
        )

    def restore_broken_connection(self, model):
        break_id = str(model.get("break_id", ""))
        pair = self.break_flags.pop(break_id, None)
        if pair:
            for flag in pair:
                self.removeItem(flag)
        links = self.break_links.pop(break_id, None)
        if links:
            for link in links:
                self.removeItem(link)
        guide = self.break_guides.pop(break_id, None)
        if guide:
            self.removeItem(guide)
        if model in self.broken_connections:
            self.broken_connections.remove(model)
        restored = copy.deepcopy(model)
        restored.pop("broken", None)
        restored.pop("break_id", None)
        restored.pop("break_name", None)
        restored.pop("out_flag_pos", None)
        restored.pop("in_flag_pos", None)
        self.add_connection(restored)
        self.changed_model.emit()
        self.connection_hint.emit("Разрыв удалён: исходная нить восстановлена.")

    def next_probe_name(self) -> str:
        numbers = []
        for item in self.connections:
            probe = item.model.get("probe")
            if isinstance(probe, dict):
                value = str(probe.get("name", "")).strip()
                if value.isdigit():
                    numbers.append(int(value))
        return str(max(numbers, default=0) + 1)

    def refresh_connections(self):
        for item in self.connections:
            item.update_path()
        for pair in self.break_flags.values():
            for flag in pair:
                if f"{flag.side}_flag_pos" not in flag.model:
                    flag.setPos(flag.port.scenePos())
        self.refresh_break_links()

    def set_line_style(self, style: str):
        if style not in {"curve", "orthogonal"}:
            return
        self.line_style = style
        QSettings(
            "VisualPythonBuilder", "VisualPythonBuilder"
        ).setValue("lineStyle", style)
        for connection in self.connections:
            connection.model["line_style"] = style
            if style == "curve":
                connection.model["bends"] = []
            connection.update_path()
        self.changed_model.emit()
        title = (
            "плавные кривые"
            if style == "curve"
            else "ломаные под 90°"
        )
        self.connection_hint.emit(
            f"Для всех нитей выбран вид: {title}."
        )

    def begin_port_action(self, port: PortItem, modifiers=None):
        if (
            self.fixed_target is not None
            and port.kind in {"event_out", "data_out"}
        ):
            target = self.fixed_target
            self.fixed_target = None
            self.pending_port = port
            self._complete_connection(target)
            return
        if self.pending_port is not None and port.kind in {"work_in", "data_in"}:
            self._complete_connection(port)
            return
        if port.kind in {"work_in", "data_in"}:
            existing = next(
                (
                    item
                    for item in self.connections
                    if item.target is port
                ),
                None,
            )
            if existing is None:
                self.cancel_temporary_connection()
                self.fixed_target = port
                self.temporary_connection = QGraphicsPathItem()
                self.temporary_connection.setPen(
                    QPen(
                        EVENT_COLOR
                        if port.kind == "work_in"
                        else DATA_COLOR,
                        2,
                        Qt.PenStyle.DashLine,
                    )
                )
                self.temporary_connection.setZValue(10)
                self.addItem(self.temporary_connection)
                self._highlight_reverse_targets(port)
                self.connection_hint.emit(
                    "Протяните свободный вход к совместимому выходу."
                )
                return
            self.rewire_backup = copy.deepcopy(existing.model)
            source = existing.source
            self.removeItem(existing)
            self.connections.remove(existing)
            self.pending_port = source
            source.setPen(QPen(QColor("#202020"), 2.5))
            self._start_temporary_connection(source)
            pen = self.temporary_connection.pen()
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setWidthF(2.6)
            self.temporary_connection.setPen(pen)
            self.connection_hint.emit(
                "Переподключение: тяните нить к новому входу; "
                "отпускание на пустом месте удалит её."
            )
            return
        if port.kind not in {"event_out", "data_out"}:
            self.connection_hint.emit(
                "Связь начинается с выходной точки: событие справа или данные снизу."
            )
            return
        self.cancel_temporary_connection()
        shift = bool(
            modifiers
            and modifiers & Qt.KeyboardModifier.ShiftModifier
        )
        if shift:
            existing = next(
                (
                    item
                    for item in self.connections
                    if item.source is port
                ),
                None,
            )
            if existing is not None:
                self.rewire_backup = copy.deepcopy(
                    existing.model
                )
                self.removeItem(existing)
                self.connections.remove(existing)
        self.pending_port = port
        port.setPen(QPen(QColor("#202020"), 2.5))
        self._start_temporary_connection(port)
        self.connection_hint.emit(
            f"Точка «{port.caption}»: протяните линию "
            "к совместимой входной точке."
        )

    def _start_temporary_connection(self, port: PortItem):
        self.temporary_connection = QGraphicsPathItem()
        self.temporary_connection.setPen(
            QPen(
                EVENT_COLOR if port.kind == "event_out" else DATA_COLOR,
                2,
                Qt.PenStyle.DashLine,
            )
        )
        self.temporary_connection.setZValue(10)
        self.addItem(self.temporary_connection)
        self.update_temporary_connection(port.scenePos())
        self._highlight_connection_targets(port)

    def update_temporary_connection(self, end: QPointF):
        if not self.temporary_connection:
            return
        if self.pending_port is not None:
            start = self.pending_port.scenePos()
            frame_anchor = self._container_drop_anchor(
                end, self.pending_port.kind, outgoing=True
            )
            target = frame_anchor if frame_anchor is not None else end
            vertical = self.pending_port.kind == "data_out"
        elif self.fixed_target is not None:
            frame_anchor = self._container_drop_anchor(
                end, self.fixed_target.kind, outgoing=False
            )
            start = frame_anchor if frame_anchor is not None else end
            target = self.fixed_target.scenePos()
            vertical = self.fixed_target.kind == "data_in"
        else:
            return
        path = (
            rounded_orthogonal_path(
                build_orthogonal_points(
                    start, target, vertical=vertical
                )
            )
            if self.line_style == "orthogonal"
            else build_curve_path(
                start, target, vertical=vertical
            )
        )
        self.temporary_connection.setPath(path)

    def finish_temporary_connection(self, scene_position: QPointF):
        if self.fixed_target is not None:
            source = next(
                (
                    item
                    for item in self.items(scene_position)
                    if isinstance(item, PortItem)
                    and item.kind in {"event_out", "data_out"}
                ),
                None,
            )
            target = self.fixed_target
            if source is None:
                if self._create_container_point_from_wire(
                    scene_position, target=target
                ):
                    return
                if self.rewire_backup is None:
                    self.cancel_temporary_connection(restore=False)
                    self._pick_and_connect_node(
                        scene_position, target=target
                    )
                    return
                rewiring = self.rewire_backup is not None
                self.cancel_temporary_connection(restore=not rewiring)
                if rewiring:
                    self.rewire_backup = None
                    self.changed_model.emit()
                    self.connection_hint.emit(
                        "Нить удалена: конец отпущен на пустом месте."
                    )
                else:
                    self.connection_hint.emit(
                        "Создание связи отменено."
                    )
                return
            self.fixed_target = None
            self.pending_port = source
            self._complete_connection(target)
            return
        target = next(
            (
                item
                for item in self.items(scene_position)
                if isinstance(item, PortItem)
                and item is not self.pending_port
            ),
            None,
        )
        if target is not None:
            self._complete_connection(target)
        else:
            source = self.pending_port
            if source is not None and self._create_container_point_from_wire(
                scene_position, source=source
            ):
                return
            body = next(
                (
                    item for item in self.items(scene_position)
                    if isinstance(item, NodeItem)
                    and source is not None
                    and item is not source.node_item
                ),
                None,
            )
            needed_kind = (
                "work_in" if source and source.kind == "event_out"
                else "data_in" if source and source.kind == "data_out"
                else ""
            )
            if body is not None and needed_kind:
                grown = grow_dynamic_group(
                    body.spec.hiasm_sub,
                    body.model.setdefault("properties", {}),
                    needed_kind,
                )
                if grown is not None:
                    _property_name, number, target_name = grown
                    connection = {
                        "from_node": source.node_item.model["id"],
                        "from_port": source.name,
                        "to_node": body.model["id"],
                        "to_port": target_name,
                        "line_style": self.line_style,
                        "bends": [],
                    }
                    selected_id = body.model["id"]
                    self.cancel_temporary_connection(restore=False)
                    self.rebuild_nodes(selected_id)
                    self.add_connection(connection)
                    self.rewire_backup = None
                    self.changed_model.emit()
                    self.connection_hint.emit(
                        f"Создан динамический вход №{number}."
                    )
                    return
            rewiring = self.rewire_backup is not None
            if source is not None and not rewiring:
                self.cancel_temporary_connection(restore=False)
                self._pick_and_connect_node(
                    scene_position, source=source
                )
                return
            self.cancel_temporary_connection(restore=not rewiring)
            if rewiring:
                self.rewire_backup = None
                self.changed_model.emit()
                self.connection_hint.emit(
                    "Нить удалена: конец отпущен на пустом месте."
                )
            else:
                self.connection_hint.emit("Создание связи отменено.")

    def _connection_node_candidates(
        self, *, source: PortItem | None = None,
        target: PortItem | None = None,
    ):
        candidates = []
        excluded = CONTAINER_PROXY_TYPES | {"UserContainer"}
        for spec in COMPONENTS.values():
            if spec.type_name in excluded:
                continue
            props = default_properties(spec.type_name)
            for port in effective_ports(spec.type_name, props):
                if source is not None:
                    advice = advise_connection(
                        source.kind, port.kind,
                        source.data_type, port.data_type,
                    )
                else:
                    advice = advise_connection(
                        port.kind, target.kind,
                        port.data_type, target.data_type,
                    )
                if not advice.allowed:
                    continue
                description = (
                    port.description.strip()
                    or spec.description.strip()
                    or "Универсальная нода."
                )
                known_type = (
                    normalize_data_type(source.data_type)
                    if source is not None else
                    normalize_data_type(target.data_type)
                )
                candidate_type = normalize_data_type(port.data_type)
                type_rank = (
                    0 if candidate_type == known_type and known_type != "any"
                    else 1 if "any" in {candidate_type, known_type}
                    else 2
                )
                category_rank = {
                    "Логика": 0,
                    "Данные": 1,
                    "Интерфейс": 2,
                    "События": 3,
                }.get(spec.category, 10)
                candidates.append({
                    "type_name": spec.type_name,
                    "caption": spec.caption,
                    "category": spec.category,
                    "port_name": port.name,
                    "port_caption": port.caption,
                    "description": description,
                    "type_rank": type_rank,
                    "category_rank": category_rank,
                    "search": " ".join((
                        component_search_text(spec),
                        port.name,
                        port.caption,
                        port.description,
                        data_type_name(port.data_type),
                    )).lower(),
                })
        return sorted(
            candidates,
            key=lambda item: (
                item["type_rank"],
                item["category_rank"],
                item["category"].lower(),
                item["caption"].lower(),
                item["port_caption"].lower(),
            ),
        )

    def _pick_and_connect_node(
        self, position: QPointF, *,
        source: PortItem | None = None,
        target: PortItem | None = None,
    ):
        """Create and wire a user-selected directly compatible general node."""
        candidates = self._connection_node_candidates(
            source=source, target=target
        )
        if not candidates:
            self.connection_hint.emit(
                "Совместимых нод для продолжения этой связи не найдено."
            )
            return
        parent = self.views()[0].window() if self.views() else None
        dialog = ConnectionNodePicker(
            candidates, outgoing=source is not None, parent=parent
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.connection_hint.emit("Добавление ноды отменено.")
            return
        choice = dialog.selected_candidate()
        if choice is None:
            self.connection_hint.emit("Нода не выбрана.")
            return
        spec = COMPONENTS[choice["type_name"]]
        props = default_properties(spec.type_name)
        enabled = default_enabled_ports(
            spec, effective_ports(spec.type_name, props)
        )
        if choice["port_name"] not in enabled:
            enabled.append(choice["port_name"])
        node_id = uuid.uuid4().hex[:10]
        model = {
            "id": node_id,
            "type": spec.type_name,
            "x": round(position.x() - 40, 1),
            "y": round(position.y() - 35, 1),
            "properties": props,
            "enabled_ports": enabled,
        }
        node = self.add_node(model)
        chosen_port = node.port_for(
            choice["port_name"], outgoing=target is not None
        )
        if chosen_port is None:
            self.removeItem(node)
            self.nodes.pop(node_id, None)
            self.connection_hint.emit(
                "Выбранная точка не создалась. Проект не изменён."
            )
            return
        if source is not None:
            link = {
                "from_node": source.node_item.model["id"],
                "from_port": source.name,
                "to_node": node_id,
                "to_port": chosen_port.name,
                "line_style": self.line_style,
                "bends": [],
            }
        else:
            link = {
                "from_node": node_id,
                "from_port": chosen_port.name,
                "to_node": target.node_item.model["id"],
                "to_port": target.name,
                "line_style": self.line_style,
                "bends": [],
            }
        self.add_connection(link)
        self.clearSelection()
        node.setSelected(True)
        self.rewire_backup = None
        self.changed_model.emit()
        self.connection_hint.emit(
            f"Добавлена нода «{spec.caption}» и соединена через точку "
            f"«{choice['port_caption']}»."
        )

    def _near_container_frame(self, position: QPointF) -> bool:
        """Accept a drop on either side of the visible container border."""
        if not self.in_container or self.interface_frame_rect is None:
            return False
        frame = self.interface_frame_rect
        tolerance = 18.0 / max(0.01, self.interface_view_scale)
        if not frame.adjusted(
            -tolerance, -tolerance, tolerance, tolerance
        ).contains(position):
            return False
        return min(
            abs(position.x() - frame.left()),
            abs(position.x() - frame.right()),
            abs(position.y() - frame.top()),
            abs(position.y() - frame.bottom()),
        ) <= tolerance

    @staticmethod
    def _container_proxy_definition(
        port_kind: str, outgoing: bool
    ) -> tuple[str, str, str] | None:
        """Return proxy type, inner port name and fixed frame side."""
        definitions = {
            (True, "event_out"): (
                "ContainerEventOutput", "doEvent", "right"
            ),
            (True, "data_out"): (
                "ContainerDataOutput", "Data", "bottom"
            ),
            (False, "work_in"): (
                "ContainerEventInput", "onEvent", "left"
            ),
            (False, "data_in"): (
                "ContainerDataInput", "Data", "top"
            ),
        }
        return definitions.get((outgoing, port_kind))

    def _container_drop_anchor(
        self, position: QPointF, port_kind: str, outgoing: bool
    ) -> QPointF | None:
        """Preview the exact interface point that will be made on release."""
        if not self._near_container_frame(position):
            return None
        definition = self._container_proxy_definition(port_kind, outgoing)
        frame = self.interface_frame_rect
        if definition is None or frame is None:
            return None
        _proxy_type, _proxy_port, side = definition
        if side in {"left", "right"}:
            offset = (position.y() - frame.top()) / max(1.0, frame.height())
        else:
            offset = (position.x() - frame.left()) / max(1.0, frame.width())
        return self._point_on_container_frame(side, offset)

    def _unique_container_point_name(self, base: str) -> str:
        base = str(base or "").strip() or "Точка"
        used = {
            str(node.model.get("properties", {}).get("name", "")).strip()
            for node in self.nodes.values()
            if node.is_container_proxy
        }
        if base not in used:
            return base
        number = 2
        while f"{base} {number}" in used:
            number += 1
        return f"{base} {number}"

    def _create_container_point_from_wire(
        self,
        position: QPointF,
        *,
        source: PortItem | None = None,
        target: PortItem | None = None,
    ) -> bool:
        """Create a typed interface point by dropping an inner wire on frame."""
        outgoing = source is not None
        inner_port = source if outgoing else target
        if inner_port is None or not self._near_container_frame(position):
            return False
        definition = self._container_proxy_definition(
            inner_port.kind, outgoing
        )
        frame = self.interface_frame_rect
        if definition is None or frame is None:
            return False
        proxy_type, proxy_port_name, side = definition
        anchor = self._container_drop_anchor(
            position, inner_port.kind, outgoing
        )
        if anchor is None:
            return False
        if side in {"left", "right"}:
            offset = (anchor.y() - frame.top()) / max(1.0, frame.height())
        else:
            offset = (anchor.x() - frame.left()) / max(1.0, frame.width())

        props = default_properties(proxy_type)
        props["name"] = self._unique_container_point_name(
            inner_port.caption or inner_port.name
        )
        if inner_port.kind in {"data_in", "data_out"}:
            props["data_type"] = normalize_data_type(
                inner_port.data_type
            )
            props["data_type_source"] = (
                f"{inner_port.node_item.spec.caption} · "
                f"{inner_port.caption}"
            )
        props["_frame_offset"] = round(
            min(max(float(offset), 0.02), 0.98), 4
        )
        proxy_id = "port_" + uuid.uuid4().hex[:8]
        proxy_model = {
            "id": proxy_id,
            "type": proxy_type,
            "x": round(anchor.x(), 1),
            "y": round(anchor.y(), 1),
            "properties": props,
            "enabled_ports": [proxy_port_name],
        }

        inner_node_id = str(inner_port.node_item.model["id"])
        inner_port_name = inner_port.name
        self.cancel_temporary_connection(restore=False)
        proxy_item = self.add_node(proxy_model)
        proxy_port = proxy_item.port_for(
            proxy_port_name, outgoing=not outgoing
        )
        if proxy_port is None:
            self.removeItem(proxy_item)
            self.nodes.pop(proxy_id, None)
            self.connection_hint.emit(
                "Не удалось создать интерфейсную точку контейнера."
            )
            return False

        if outgoing:
            connection = {
                "from_node": inner_node_id,
                "from_port": inner_port_name,
                "to_node": proxy_id,
                "to_port": proxy_port_name,
                "line_style": self.line_style,
                "bends": [],
            }
        else:
            connection = {
                "from_node": proxy_id,
                "from_port": proxy_port_name,
                "to_node": inner_node_id,
                "to_port": inner_port_name,
                "line_style": self.line_style,
                "bends": [],
            }
        self.add_connection(connection)
        self.rewire_backup = None
        self.refresh_connections()
        self.changed_model.emit()
        self.connection_hint.emit(
            f"На рамке создана точка «{props['name']}»."
        )
        return True

    def cancel_temporary_connection(self, restore=True):
        if self.pending_port is not None:
            self.pending_port.setPen(QPen(QColor("#FFFFFF"), 1.5))
        if self.temporary_connection is not None:
            self.removeItem(self.temporary_connection)
        self.pending_port = None
        self.fixed_target = None
        self.temporary_connection = None
        self._reset_port_highlighting()
        if restore and self.rewire_backup is not None:
            backup = self.rewire_backup
            self.rewire_backup = None
            self.add_connection(backup)

    def _highlight_connection_targets(self, source: PortItem):
        for node in self.nodes.values():
            for port in node.ports.values():
                if port is source:
                    continue
                advice = advise_connection(
                    source.kind, port.kind,
                    source.data_type, port.data_type,
                    same_node=port.node_item is source.node_item,
                )
                if advice.allowed:
                    port.setOpacity(1.0)
                    port.setPen(QPen(QColor("#2E8B57"), 2.5))
                elif advice.needs_adapter:
                    port.setOpacity(1.0)
                    port.setPen(QPen(QColor("#D18A00"), 2.5))
                else:
                    port.setOpacity(0.3)

    def _highlight_reverse_targets(self, target: PortItem):
        for node in self.nodes.values():
            for port in node.ports.values():
                advice = advise_connection(
                    port.kind, target.kind,
                    port.data_type, target.data_type,
                    same_node=port.node_item is target.node_item,
                )
                if advice.allowed:
                    port.setOpacity(1.0)
                    port.setPen(
                        QPen(QColor("#2E8B57"), 2.5)
                    )
                elif advice.needs_adapter:
                    port.setOpacity(1.0)
                    port.setPen(QPen(QColor("#D18A00"), 2.5))
                else:
                    port.setOpacity(0.3)

    def _reset_port_highlighting(self):
        for node in self.nodes.values():
            for port in node.ports.values():
                port.setOpacity(1.0)
                port.setPen(QPen(QColor("#FFFFFF"), 1.5))

    def _complete_connection(self, port: PortItem):
        source = self.pending_port
        if source is None:
            return
        advice = advise_connection(
            source.kind, port.kind,
            source.data_type, port.data_type,
            same_node=source.node_item is port.node_item,
        )
        if advice.needs_adapter:
            self.cancel_temporary_connection(restore=False)
            parent = self.views()[0].window() if self.views() else None
            answer = QMessageBox.question(
                parent,
                "Нужно преобразовать данные",
                f"{advice.message}\n\n"
                f"Вставить между нодами универсальный преобразователь "
                f"«{advice.adapter_caption}»?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._insert_connection_adapter(
                    source, port, advice.adapter_type,
                    advice.adapter_caption,
                )
            else:
                self.cancel_temporary_connection(restore=True)
                self.connection_hint.emit(
                    "Связь не создана: преобразователь не был добавлен."
                )
            return
        if not advice.allowed:
            self.connection_hint.emit(advice.message)
            return
        self.cancel_temporary_connection(restore=False)
        model = {
            "from_node": source.node_item.model["id"],
            "from_port": source.name,
            "to_node": port.node_item.model["id"],
            "to_port": port.name,
            "line_style": self.line_style,
            "bends": [],
        }
        for existing in list(self.connections):
            if (
                existing.model["to_node"] == model["to_node"]
                and existing.model["to_port"] == model["to_port"]
            ):
                self.removeItem(existing)
                self.connections.remove(existing)
        self.add_connection(model)
        self.rewire_backup = None
        self.changed_model.emit()
        self.connection_hint.emit(
            f"Создана связь: {source.caption} → {port.caption}."
        )

    def _insert_connection_adapter(
        self, source: PortItem, target: PortItem,
        adapter_type: str, adapter_caption: str,
    ):
        """Insert one visible general-purpose converter after confirmation."""
        if adapter_type not in COMPONENTS:
            self.cancel_temporary_connection(restore=True)
            self.connection_hint.emit(
                "Преобразователь недоступен. Проект не изменён."
            )
            return
        midpoint = (source.scenePos() + target.scenePos()) / 2
        adapter_id = uuid.uuid4().hex[:10]
        props = default_properties(adapter_type)
        model = {
            "id": adapter_id,
            "type": adapter_type,
            "x": round(midpoint.x() - 40, 1),
            "y": round(midpoint.y() - 35, 1),
            "properties": props,
            "enabled_ports": [
                item.name for item in effective_ports(adapter_type, props)
            ],
        }
        adapter = self.add_node(model)
        adapter_in = next(
            (item for item in adapter.ports.values() if item.kind == "data_in"),
            None,
        )
        adapter_out = next(
            (item for item in adapter.ports.values() if item.kind == "data_out"),
            None,
        )
        if adapter_in is None or adapter_out is None:
            self.removeItem(adapter)
            self.nodes.pop(adapter_id, None)
            self.cancel_temporary_connection(restore=True)
            self.connection_hint.emit(
                "У преобразователя нет нужных точек. Проект не изменён."
            )
            return
        for existing in list(self.connections):
            if (
                existing.model["to_node"] == target.node_item.model["id"]
                and existing.model["to_port"] == target.name
            ):
                self.removeItem(existing)
                self.connections.remove(existing)
        links = (
            {
                "from_node": source.node_item.model["id"],
                "from_port": source.name,
                "to_node": adapter_id,
                "to_port": adapter_in.name,
                "line_style": self.line_style,
                "bends": [],
            },
            {
                "from_node": adapter_id,
                "from_port": adapter_out.name,
                "to_node": target.node_item.model["id"],
                "to_port": target.name,
                "line_style": self.line_style,
                "bends": [],
            },
        )
        for link in links:
            self.add_connection(link)
        self.clearSelection()
        adapter.setSelected(True)
        self.rewire_backup = None
        self.changed_model.emit()
        self.connection_hint.emit(
            f"Вставлен преобразователь «{adapter_caption}». "
            "Он остаётся обычной видимой нодой."
        )

    def create_branch_on_connection(self, item: ConnectionItem, position: QPointF):
        """Splice a typed hub into a wire and leave spare outputs for branches."""
        if item not in self.connections:
            return
        event_wire = item.source.kind == "event_out"
        hub_type = "EventHub" if event_wire else "DataHub"
        source_model = item.source.node_item.model
        target_model = item.target.node_item.model
        old = copy.deepcopy(item.model)
        hub_id = uuid.uuid4().hex[:10]
        props = default_properties(hub_type)
        # A branch needs the original input plus one continuation and one
        # spare output. Four outputs by default made the generated hub look
        # like a component with unrelated, empty points.
        props["input_count"] = 1
        props["output_count"] = 2
        model = {
            "id": hub_id, "type": hub_type,
            "x": round(position.x() - 45, 1),
            "y": round(position.y() - 35, 1),
            "properties": props,
            "enabled_ports": [
                port.name
                for port in effective_ports(hub_type, props)
            ],
        }
        self.removeItem(item)
        self.connections.remove(item)
        self.add_node(model)
        incoming = {
            "from_node": source_model["id"], "from_port": old["from_port"],
            "to_node": hub_id, "to_port": "doInput1" if event_wire else "DataIn1",
            "line_style": "orthogonal", "bends": [],
        }
        outgoing = {
            "from_node": hub_id, "from_port": "onOutput1" if event_wire else "DataOut1",
            "to_node": target_model["id"], "to_port": old["to_port"],
            "line_style": "orthogonal", "bends": [],
        }
        self.add_connection(incoming)
        self.add_connection(outgoing)
        # Do not run the global obstacle-avoiding router here. It explores a
        # large grid and was the source of the visible 20–30 second pause.
        for connection in self.connections[-2:]:
            route = build_orthogonal_points(
                connection.source.scenePos(),
                connection.target.scenePos(),
                vertical=connection._vertical(),
            )
            connection.model["bends"] = [
                [point.x(), point.y()] for point in route[1:-1]
            ]
            connection.update_path()
        self.clearSelection()
        self.nodes[hub_id].setSelected(True)
        self.changed_model.emit()
        self.connection_hint.emit(
            "В нить вставлен хаб. Свободные выходы готовы для новых ответвлений."
        )

    def remove_connection(self, item: ConnectionItem):
        if item in self.connections:
            self.removeItem(item)
            self.connections.remove(item)
            self.changed_model.emit()
            self.connection_hint.emit("Нить удалена.")

    @staticmethod
    def _point_inside_rect(point: QPointF, rect: QRectF):
        return (
            rect.left() + 0.1 < point.x() < rect.right() - 0.1
            and rect.top() + 0.1 < point.y() < rect.bottom() - 0.1
        )

    @staticmethod
    def _segment_blocked(first, second, obstacles):
        if abs(first.x() - second.x()) < 0.01:
            x = first.x()
            low, high = sorted((first.y(), second.y()))
            return any(
                rect.left() + 0.1 < x < rect.right() - 0.1
                and high > rect.top() + 0.1
                and low < rect.bottom() - 0.1
                for rect in obstacles
            )
        y = first.y()
        low, high = sorted((first.x(), second.x()))
        return any(
            rect.top() + 0.1 < y < rect.bottom() - 0.1
            and high > rect.left() + 0.1
            and low < rect.right() - 0.1
            for rect in obstacles
        )

    @staticmethod
    def _wire_penalty(first, second, occupied):
        vertical = abs(first.x() - second.x()) < 0.01
        penalty = 0.0
        for other_first, other_second in occupied:
            other_vertical = (
                abs(other_first.x() - other_second.x()) < 0.01
            )
            if vertical == other_vertical:
                if (
                    vertical
                    and abs(first.x() - other_first.x()) < 1.0
                ):
                    overlap = min(
                        max(first.y(), second.y()),
                        max(other_first.y(), other_second.y()),
                    ) - max(
                        min(first.y(), second.y()),
                        min(other_first.y(), other_second.y()),
                    )
                elif (
                    not vertical
                    and abs(first.y() - other_first.y()) < 1.0
                ):
                    overlap = min(
                        max(first.x(), second.x()),
                        max(other_first.x(), other_second.x()),
                    ) - max(
                        min(first.x(), second.x()),
                        min(other_first.x(), other_second.x()),
                    )
                else:
                    overlap = 0.0
                if overlap > 0:
                    penalty += 900.0 + overlap * 4.0
            else:
                vertical_first, vertical_second = (
                    (first, second)
                    if vertical
                    else (other_first, other_second)
                )
                horizontal_first, horizontal_second = (
                    (other_first, other_second)
                    if vertical
                    else (first, second)
                )
                if (
                    min(
                        vertical_first.y(), vertical_second.y()
                    )
                    < horizontal_first.y()
                    < max(
                        vertical_first.y(), vertical_second.y()
                    )
                    and min(
                        horizontal_first.x(),
                        horizontal_second.x(),
                    )
                    < vertical_first.x()
                    < max(
                        horizontal_first.x(),
                        horizontal_second.x(),
                    )
                ):
                    penalty += 140.0
        return penalty

    def _occupied_wire_segments(self, excluded=None):
        occupied = []
        for connection in self.connections:
            if (
                connection is excluded
                or connection.model.get("line_style")
                != "orthogonal"
            ):
                continue
            points = connection._route_points()
            occupied.extend(zip(points, points[1:]))
        return occupied

    def _find_orthogonal_route(
        self, start, target, obstacles, occupied
    ):
        clearance = 8.0
        xs = {float(start.x()), float(target.x())}
        ys = {float(start.y()), float(target.y())}
        for rect in obstacles:
            xs.update(
                (
                    rect.left() - clearance,
                    rect.right() + clearance,
                )
            )
            ys.update(
                (
                    rect.top() - clearance,
                    rect.bottom() + clearance,
                )
            )
        for first, second in occupied:
            if abs(first.x() - second.x()) < 0.01:
                xs.update((first.x() - 8.0, first.x() + 8.0))
            else:
                ys.update((first.y() - 8.0, first.y() + 8.0))
        points = {}
        for x, y in itertools.product(sorted(xs), sorted(ys)):
            point = QPointF(x, y)
            if not any(
                self._point_inside_rect(point, rect)
                for rect in obstacles
            ):
                points[(x, y)] = point
        start_key = (float(start.x()), float(start.y()))
        target_key = (float(target.x()), float(target.y()))
        points[start_key] = QPointF(start)
        points[target_key] = QPointF(target)
        neighbours = {key: [] for key in points}
        by_x: dict[float, list[tuple[float, float]]] = {}
        by_y: dict[float, list[tuple[float, float]]] = {}
        for key in points:
            by_x.setdefault(key[0], []).append(key)
            by_y.setdefault(key[1], []).append(key)
        for lines, direction in (
            (by_y.values(), 0),
            (by_x.values(), 1),
        ):
            for line in lines:
                line.sort(
                    key=lambda key: key[
                        0 if direction == 0 else 1
                    ]
                )
                for first_key, second_key in zip(
                    line, line[1:]
                ):
                    first = points[first_key]
                    second = points[second_key]
                    if self._segment_blocked(
                        first, second, obstacles
                    ):
                        continue
                    cost = (
                        QLineF(first, second).length()
                        + self._wire_penalty(
                            first, second, occupied
                        )
                    )
                    neighbours[first_key].append(
                        (second_key, direction, cost)
                    )
                    neighbours[second_key].append(
                        (first_key, direction, cost)
                    )
        queue = [(0.0, 0, start_key, -1)]
        serial = itertools.count(1)
        distance = {(start_key, -1): 0.0}
        previous = {}
        end_state = None
        while queue:
            cost, _unused, key, old_direction = heapq.heappop(
                queue
            )
            state = (key, old_direction)
            if cost != distance.get(state):
                continue
            if key == target_key:
                end_state = state
                break
            for next_key, direction, edge_cost in neighbours.get(
                key, ()
            ):
                bend_cost = (
                    0.0
                    if old_direction in (-1, direction)
                    else 32.0
                )
                next_state = (next_key, direction)
                next_cost = cost + edge_cost + bend_cost
                if next_cost >= distance.get(
                    next_state, float("inf")
                ):
                    continue
                distance[next_state] = next_cost
                previous[next_state] = state
                heapq.heappush(
                    queue,
                    (
                        next_cost,
                        next(serial),
                        next_key,
                        direction,
                    ),
                )
        if end_state is None:
            return None
        route = []
        state = end_state
        while True:
            route.append(points[state[0]])
            if state == (start_key, -1):
                break
            state = previous[state]
        route.reverse()
        return route

    def auto_route_connection(
        self, item: ConnectionItem,
        occupied=None, notify=True
    ):
        # The obstacle router builds a Cartesian grid from every node.  A
        # container adds boundary/proxy points and can make that grid
        # needlessly enormous.  In this case use the deterministic
        # orthogonal route; container endpoints still use their perpendicular
        # frame route.
        if self.in_container or any(
            node.model.get("type") == "UserContainer"
            for node in self.nodes.values()
        ):
            item.model["line_style"] = "orthogonal"
            item.model["bends"] = []
            points = item._route_points()
            item.model["bends"] = [
                [point.x(), point.y()] for point in points[1:-1]
            ]
            item.update_path()
            if notify:
                self.changed_model.emit()
                self.connection_hint.emit(
                    "Нить автоматически проложена быстрым маршрутом: "
                    "схема содержит контейнер."
                )
            return True
        item.model["line_style"] = "orthogonal"
        default = build_orthogonal_points(
            item.source.scenePos(),
            item.target.scenePos(),
            vertical=item._vertical(),
        )
        source_out, target_out = default[1], default[-2]
        obstacles = [
            node.sceneBoundingRect().adjusted(
                -10, -10, 10, 10
            )
            for node in self.nodes.values()
        ]
        if occupied is None:
            occupied = self._occupied_wire_segments(item)
        middle = self._find_orthogonal_route(
            source_out, target_out, obstacles, occupied
        )
        points = (
            [item.source.scenePos()]
            + middle
            + [item.target.scenePos()]
            if middle
            else default
        )
        points = normalize_orthogonal_points(
            points, vertical=item._vertical()
        )
        item.model["bends"] = [
            [point.x(), point.y()]
            for point in points[1:-1]
        ]
        item.update_path()
        if notify:
            self.changed_model.emit()
            self.connection_hint.emit(
                "Нить автоматически проложена."
            )
        return middle is not None

    def auto_route_all_connections(self):
        occupied = []
        routed = 0
        self.line_style = "orthogonal"
        for item in self.connections:
            if self.auto_route_connection(
                item, occupied=occupied, notify=False
            ):
                routed += 1
            points = item._route_points()
            occupied.extend(zip(points, points[1:]))
        QSettings(
            "VisualPythonBuilder", "VisualPythonBuilder"
        ).setValue("lineStyle", "orthogonal")
        self.changed_model.emit()
        self.connection_hint.emit(
            f"Автопроложено нитей: {routed}."
        )

    def _wire_layout_score(self) -> float:
        """Оценка схемы: длина плюс очень дорогие пересечения/наложения."""
        segments = []
        length = 0.0
        for item in self.connections:
            points = item._route_points()
            for first, second in zip(points, points[1:]):
                if QLineF(first, second).length() < 0.1:
                    continue
                segments.append((first, second))
                length += QLineF(first, second).length()
        penalty = 0.0
        for index, (first, second) in enumerate(segments):
            first_vertical = abs(first.x() - second.x()) < 0.01
            for other_first, other_second in segments[index + 1:]:
                other_vertical = abs(
                    other_first.x() - other_second.x()
                ) < 0.01
                if first_vertical == other_vertical:
                    if first_vertical and abs(first.x() - other_first.x()) < 1:
                        overlap = min(max(first.y(), second.y()), max(other_first.y(), other_second.y())) - max(min(first.y(), second.y()), min(other_first.y(), other_second.y()))
                        if overlap > 1:
                            penalty += 5000 + overlap * 10
                    elif not first_vertical and abs(first.y() - other_first.y()) < 1:
                        overlap = min(max(first.x(), second.x()), max(other_first.x(), other_second.x())) - max(min(first.x(), second.x()), min(other_first.x(), other_second.x()))
                        if overlap > 1:
                            penalty += 5000 + overlap * 10
                    continue
                vertical_first, vertical_second = (
                    (first, second) if first_vertical
                    else (other_first, other_second)
                )
                horizontal_first, horizontal_second = (
                    (other_first, other_second) if first_vertical
                    else (first, second)
                )
                if (
                    min(vertical_first.y(), vertical_second.y())
                    < horizontal_first.y()
                    < max(vertical_first.y(), vertical_second.y())
                    and min(horizontal_first.x(), horizontal_second.x())
                    < vertical_first.x()
                    < max(horizontal_first.x(), horizontal_second.x())
                ):
                    penalty += 2500
        return length + penalty

    def smart_layout_and_route(self):
        """Разложить схему по слоям и перепроложить нити с обходом."""
        if not self.nodes:
            self.connection_hint.emit("Схема пуста: расставлять нечего.")
            return

        original_positions = {
            node_id: (item.pos().x(), item.pos().y())
            for node_id, item in self.nodes.items()
        }
        original_bends = {
            id(item): copy.deepcopy(item.model.get("bends", []))
            for item in self.connections
        }
        original_styles = {
            id(item): item.model.get("line_style", self.line_style)
            for item in self.connections
        }
        baseline_score = self._wire_layout_score()

        node_ids = list(self.nodes)
        outgoing = {node_id: [] for node_id in node_ids}
        incoming = {node_id: [] for node_id in node_ids}
        for connection in self.connections:
            source_id = str(connection.model.get("from_node"))
            target_id = str(connection.model.get("to_node"))
            if source_id not in outgoing or target_id not in incoming:
                continue
            outgoing[source_id].append(target_id)
            incoming[target_id].append(source_id)

        indegree = {node_id: len(incoming[node_id]) for node_id in node_ids}
        queue = collections.deque(
            node_id for node_id in node_ids if indegree[node_id] == 0
        )
        layers = {node_id: 0 for node_id in node_ids}
        processed = set()
        while queue:
            node_id = queue.popleft()
            processed.add(node_id)
            for target_id in outgoing[node_id]:
                layers[target_id] = max(
                    layers[target_id], layers[node_id] + 1
                )
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    queue.append(target_id)

        # Циклы нельзя полностью топологически отсортировать. Размещаем
        # оставшиеся узлы следующим стабильным слоем, не складывая их в одну
        # точку.
        for node_id in node_ids:
            if node_id not in processed:
                layers[node_id] = max(layers.values(), default=0) + 1

        by_layer = {}
        for node_id in node_ids:
            by_layer.setdefault(layers[node_id], []).append(node_id)
        for members in by_layer.values():
            members.sort(
                key=lambda node_id: (
                    self.nodes[node_id].model.get("y", 0),
                    self.nodes[node_id].model.get("x", 0),
                    node_id,
                )
            )

        def position_in_layer(layer, node_id):
            members = by_layer.get(layer, [])
            return members.index(node_id) if node_id in members else 0

        # Два направления прохода по слоям уменьшают число пересечений
        # ещё до запуска маршрутизатора.
        for _ in range(4):
            for layer in sorted(by_layer):
                if layer == min(by_layer):
                    continue
                members = by_layer[layer]
                members.sort(
                    key=lambda node_id: (
                        sum(
                            position_in_layer(layer - 1, source_id)
                            for source_id in incoming[node_id]
                            if source_id in by_layer.get(layer - 1, [])
                        )
                        / max(
                            1,
                            sum(
                                source_id in by_layer.get(layer - 1, [])
                                for source_id in incoming[node_id]
                            ),
                        ),
                        self.nodes[node_id].model.get("y", 0),
                        node_id,
                    )
                )
            for layer in sorted(by_layer, reverse=True):
                if layer == max(by_layer):
                    continue
                members = by_layer[layer]
                members.sort(
                    key=lambda node_id: (
                        sum(
                            position_in_layer(layer + 1, target_id)
                            for target_id in outgoing[node_id]
                            if target_id in by_layer.get(layer + 1, [])
                        )
                        / max(
                            1,
                            sum(
                                target_id in by_layer.get(layer + 1, [])
                                for target_id in outgoing[node_id]
                            ),
                        ),
                        self.nodes[node_id].model.get("y", 0),
                        node_id,
                    )
                )

        max_width = max(
            (item.width for item in self.nodes.values()), default=72
        )
        horizontal_gap = max(120, max_width + 54)
        vertical_gap = 46
        for layer, members in by_layer.items():
            x = 40 + layer * horizontal_gap
            total_height = sum(
                self.nodes[node_id].height for node_id in members
            )
            total_height += max(0, len(members) - 1) * vertical_gap
            y = -total_height / 2
            for node_id in members:
                item = self.nodes[node_id]
                item.setPos(x, y)
                y += item.height + vertical_gap

        self.refresh_connections()
        self.auto_route_all_connections()
        candidate_score = self._wire_layout_score()
        if candidate_score > baseline_score:
            for node_id, (x, y) in original_positions.items():
                self.nodes[node_id].setPos(x, y)
            for item in self.connections:
                item.model["bends"] = original_bends.get(id(item), [])
                item.model["line_style"] = original_styles.get(
                    id(item), self.line_style
                )
                item.update_path()
            self.line_style = next(
                iter(original_styles.values()), self.line_style
            )
            self.refresh_connections()
            self.changed_model.emit()
            self.connection_hint.emit(
                "Исходная расстановка сохранена: автоматический вариант "
                "создавал больше пересечений."
            )
            return
        self.changed_model.emit()
        self.connection_hint.emit(
            "Умная расстановка завершена: ноды разложены по слоям, "
            "нити перепроложены с обходом препятствий."
        )

    def delete_selected(self):
        selected = self.selectedItems()
        for item in selected:
            if isinstance(item, ConnectionItem):
                self.removeItem(item)
                self.connections.remove(item)
            elif isinstance(item, HelperItem):
                self.remove_helper(item)
            elif isinstance(item, BreakFlagItem):
                self.restore_broken_connection(item.model)
            elif isinstance(item, NodeItem):
                for connection in list(self.connections):
                    if connection.source.node_item is item or connection.target.node_item is item:
                        self.removeItem(connection)
                        self.connections.remove(connection)
                for model in list(self.broken_connections):
                    if (
                        model.get("from_node") == item.model.get("id")
                        or model.get("to_node") == item.model.get("id")
                    ):
                        self.restore_broken_connection(model)
                self.removeItem(item)
                self.nodes.pop(item.model["id"], None)
        if selected:
            self.changed_model.emit()

    def _selection_changed(self):
        selected = [item for item in self.selectedItems() if isinstance(item, NodeItem)]
        self.node_selected.emit(selected[0].model if selected else None)

    def to_project(self, name: str) -> dict[str, Any]:
        return {
            "format": 1,
            "name": name,
            "nodes": [item.model for item in self.nodes.values()],
            "connections": [
                item.model for item in self.connections
            ] + list(self.broken_connections),
            "helpers": [item.model for item in self.helpers],
        }

    def load_project(self, project: dict[str, Any]):
        repair_mdi_parentage(project)
        self.blockSignals(True)
        self.clear()
        self.nodes.clear()
        self.connections.clear()
        self.helpers.clear()
        self.broken_connections.clear()
        self.break_flags.clear()
        self.break_links.clear()
        self.break_guides.clear()
        self.interface_frame = None
        self.interface_frame_inner = None
        self.interface_frame_rect = None
        self.interface_view_scale = 1.0
        self._positioning_interface_points = False
        self.pending_port = None
        self.fixed_target = None
        self.rewire_backup = None
        self.temporary_connection = None
        for model in project.get("nodes", []):
            if model.get("type") in COMPONENTS:
                self.add_node(model)
        if self.in_container:
            self._build_container_interface_frame()
        for model in project.get("connections", []):
            self.add_connection(model)
        for model in project.get("helpers", []):
            if isinstance(model, dict):
                self.add_helper(model)
        self.blockSignals(False)
        self.project_loaded.emit()

    def rebuild_nodes(self, selected_id: str | None = None):
        project = self.to_project("")
        self.load_project(project)
        if selected_id and selected_id in self.nodes:
            self.nodes[selected_id].setSelected(True)
