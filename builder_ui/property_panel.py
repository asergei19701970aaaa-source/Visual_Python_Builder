from __future__ import annotations

from .common import *
from model_contract import (
    component_passport,
    diagnose_node_model,
    normalize_node_model,
    property_group_name,
)
from point_help import point_help


class PropertyPanel(QWidget):
    changed = Signal()
    port_toggle_requested = Signal(object, str, bool)

    def __init__(self):
        super().__init__()
        self.model: dict[str, Any] | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.property_search = QLineEdit()
        self.property_search.setPlaceholderText(
            "Поиск: свойство, имя, тип, значение…"
        )
        self.property_search.setClearButtonEnabled(True)
        self.property_search.setToolTip(
            "Ищет по подписи, техническому имени, типу, текущему значению "
            "и предметному описанию."
        )
        layout.addWidget(self.property_search)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.property_tree = QTreeWidget()
        self.property_tree.setColumnCount(2)
        self.property_tree.setHeaderLabels(["Свойство", "Значение"])
        self.property_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.property_tree.header().setStretchLastSection(True)
        self.property_tree.setAlternatingRowColors(True)
        properties_page = QWidget()
        properties_layout = QVBoxLayout(properties_page)
        properties_layout.setContentsMargins(0, 0, 0, 0)
        self.property_status = QLabel()
        self.property_status.setWordWrap(True)
        self.property_status.setMinimumHeight(26)
        self.property_status.setStyleSheet(
            "QLabel { padding:4px 6px; border:1px solid #D5D5D5;"
            " background:#F4F4F4; color:#5C5C5C; }"
        )
        properties_layout.addWidget(self.property_status)
        properties_layout.addWidget(self.property_tree, 1)
        property_help_title = QLabel("Описание выбранного свойства")
        property_help_title.setStyleSheet(
            "font-weight:600; color:#3E3B37; padding:4px 5px 2px;"
        )
        properties_layout.addWidget(property_help_title)
        self.property_help = QPlainTextEdit()
        self.property_help.setReadOnly(True)
        self.property_help.setMinimumHeight(86)
        self.property_help.setMaximumHeight(135)
        self.property_help.setStyleSheet(
            "QPlainTextEdit { background:#F7F7F7; color:#303030;"
            " border:1px solid #C8C8C8; padding:5px; }"
        )
        properties_layout.addWidget(self.property_help)
        self.property_tree.currentItemChanged.connect(
            self._property_selection_changed
        )
        self.tabs.addTab(properties_page, "Свойства")

        self.points_tree = QTreeWidget()
        self.points_tree.setColumnCount(1)
        self.points_tree.setHeaderHidden(True)
        self.points_tree.setRootIsDecorated(False)
        self.points_tree.setAlternatingRowColors(True)
        self.points_tree.setIndentation(0)
        self.points_tree.setUniformRowHeights(True)
        self.points_tree.itemChanged.connect(self._point_state_changed)
        self.points_tree.currentItemChanged.connect(
            self._point_selection_changed
        )
        points_page = QWidget()
        points_layout = QVBoxLayout(points_page)
        points_layout.setContentsMargins(0, 0, 0, 0)
        points_layout.addWidget(self.points_tree, 1)
        help_title = QLabel("Расширенная справка по выбранной точке")
        help_title.setStyleSheet(
            "font-weight:600; color:#3E3B37; padding:4px 5px 2px;"
        )
        points_layout.addWidget(help_title)
        self.points_help = QPlainTextEdit()
        self.points_help.setReadOnly(True)
        self.points_help.setMinimumHeight(112)
        self.points_help.setMaximumHeight(155)
        self.points_help.setStyleSheet(
            "QPlainTextEdit { background:#F7F7F7; color:#303030;"
            " border:1px solid #C8C8C8; padding:5px; }"
        )
        points_layout.addWidget(self.points_help)
        self.tabs.addTab(points_page, "Точки")
        self.property_search.textChanged.connect(self._filter_property_rows)
        self._show_empty()

    def _show_empty(self):
        self.property_tree.clear()
        self.points_tree.clear()
        self.points_help.setPlainText(
            "Выберите компонент и точку. Здесь появится расширенная справка "
            "о назначении, направлении и подключении."
        )
        self.property_help.setPlainText(
            "Выберите свойство. Здесь появится его назначение, тип и текущее "
            "значение."
        )
        self.property_status.setText(
            "Выберите компонент — здесь появится состояние проверки."
        )
        self.property_status.setStyleSheet(
            "QLabel { padding:4px 6px; border:1px solid #D5D5D5;"
            " background:#F4F4F4; color:#5C5C5C; }"
        )
        empty = QTreeWidgetItem(["Выберите компонент", ""])
        empty.setForeground(0, QColor("#7D7A75"))
        self.property_tree.addTopLevelItem(empty)

    def set_node(self, model: dict[str, Any] | None):
        self.points_tree.blockSignals(True)
        self.property_tree.clear()
        self.points_tree.clear()
        self.model = model
        if not model:
            self._show_empty()
            self.points_tree.blockSignals(False)
            return
        diagnostic_errors = diagnose_node_model(model)
        normalize_node_model(model)
        spec = COMPONENTS[model["type"]]
        passport = component_passport(model["type"], model.get("properties", {}))
        instance_ports = effective_ports(
            model["type"], model.get("properties", {})
        )

        component_row = QTreeWidgetItem(["Компонент", spec.caption])
        component_row.setToolTip(
            1,
            (
                f"{spec.type_name}\n"
                f"{passport['description'] or 'Описание компонента пока не заполнено.'}"
            ),
        )
        component_row.setData(0, Qt.ItemDataRole.UserRole + 2, passport["description"])
        self.property_tree.addTopLevelItem(component_row)
        support_row = QTreeWidgetItem(
            [
                "Поддержка",
                (
                    "Python-генератор · "
                    f"{len(passport['properties'])} свойств · "
                    f"{len(passport['ports'])} точек · "
                    f"{passport['support_status']}"
                    if spec.implemented
                    else f"{passport['source']} · {passport['support_status']}"
                ),
            ]
        )
        support_row.setToolTip(
            1,
            spec.description
            or (
                "Компонент полностью поддерживается."
                if spec.implemented
                else (
                    "Работает и проверен специализированными тестами."
                    if passport["support_status"] == "работает"
                    else "Реализована только часть поведения оригинального HiAsm."
                    if passport["support_status"] == "частично"
                    else "Точки и свойства импортированы, но поведение пока является заглушкой."
                )
            ),
        )
        hiasm = passport.get("hiasm", {})
        hiasm_lines = [
            f"{key}: {value}" for key, value in (
                ("Класс HiAsm", hiasm.get("class", "")),
                ("Наследование", hiasm.get("inherit", "")),
                ("Интерфейсы", hiasm.get("interfaces", "")),
                ("Редактор", hiasm.get("edit_class", "")),
            ) if str(value).strip()
        ]
        if hiasm_lines:
            support_row.setToolTip(
                1,
                support_row.toolTip(1) + "\n\n" + "\n".join(hiasm_lines),
            )
        self.property_tree.addTopLevelItem(support_row)

        group_order = (
            "Основные",
            "Положение и размер",
            "Значения",
            "Внешний вид",
            "Настройки",
        )
        groups: dict[str, QTreeWidgetItem] = {}
        for group_name in group_order:
            group = QTreeWidgetItem([group_name, ""])
            group.setExpanded(group_name in {"Основные", "Положение и размер"})
            groups[group_name] = group
            self.property_tree.addTopLevelItem(group)

        props = model.setdefault("properties", {})
        for prop in spec.properties:
            if ((spec.type_name=="DashboardCanvas" and prop.name=="scene") or (spec.type_name=="UserContainer" and prop.name in {"subgraph","interface"})):
                continue  # internal persistence; edit visually by double-click
            parent = groups[property_group_name(prop)]
            row = QTreeWidgetItem([prop.caption, ""])
            row.setData(0, Qt.ItemDataRole.UserRole, prop.name)
            row.setData(0, Qt.ItemDataRole.UserRole + 1, prop.kind)
            row.setData(0, Qt.ItemDataRole.UserRole + 2, prop.description)
            row.setData(0, Qt.ItemDataRole.UserRole + 4, props.get(prop.name, prop.default))
            row.setToolTip(
                0,
                (
                    f"{prop.name}\n"
                    f"{prop.description or 'Значение свойства компонента.'}"
                ).strip(),
            )
            property_errors = [
                error for error in diagnostic_errors
                if prop.name in error or prop.caption in error
            ]
            if property_errors:
                row.setForeground(0, QColor("#B3261E"))
                row.setForeground(1, QColor("#B3261E"))
                row.setToolTip(
                    0,
                    row.toolTip(0) + "\n\n" + "\n".join(property_errors),
                )
            parent.addChild(row)
            if prop.kind == "int":
                widget = QSpinBox()
                widget.setRange(prop.minimum or -999999, prop.maximum or 999999)
                try:
                    safe_value = int(props.get(prop.name, prop.default))
                except (TypeError, ValueError):
                    safe_value = int(prop.default or 0)
                widget.setValue(safe_value)
                widget.valueChanged.connect(
                    lambda value, key=prop.name: self._set_value(key, value)
                )
            elif prop.kind == "bool":
                widget = QCheckBox()
                widget.setChecked(bool(props.get(prop.name, prop.default)))
                widget.toggled.connect(
                    lambda value, key=prop.name: self._set_value(key, value)
                )
            elif prop.kind == "real":
                widget = QDoubleSpinBox()
                widget.setDecimals(6)
                widget.setRange(
                    float(prop.minimum if prop.minimum is not None else -1e12),
                    float(prop.maximum if prop.maximum is not None else 1e12),
                )
                try:
                    safe_value = float(props.get(prop.name, prop.default))
                except (TypeError, ValueError):
                    safe_value = float(prop.default or 0.0)
                widget.setValue(safe_value)
                widget.valueChanged.connect(
                    lambda value, key=prop.name: self._set_value(key, value)
                )
            elif prop.kind in {"enum", "choice"}:
                widget = QComboBox()
                widget.addItems(list(prop.options))
                current = str(props.get(prop.name, prop.default))
                index = widget.findText(current)
                widget.setCurrentIndex(max(0, index))
                widget.currentTextChanged.connect(
                    lambda value, key=prop.name: self._set_value(key, value)
                )
            elif prop.kind in {"multiline", "code", "table"}:
                widget = QPlainTextEdit(str(props.get(prop.name, prop.default)))
                widget.setMaximumHeight(130 if prop.kind == "table" else 90)
                if prop.kind == "table":
                    widget.setPlaceholderText(
                        "Введите данные строками или в формате JSON…"
                    )
                widget.setStyleSheet("background:#FFFFFF; color:#202020; padding:2px;")
                widget.textChanged.connect(
                    lambda key=prop.name, editor=widget: self._set_value(key, editor.toPlainText())
                )
            elif prop.kind == "color":
                current = props.get(prop.name, prop.default)
                widget = QPushButton()
                widget.setProperty("colorValue", str(current))
                self._update_color_button(widget, current)
                widget.clicked.connect(
                    lambda _checked=False, key=prop.name, button=widget:
                    self._choose_color(key, button)
                )
            elif prop.kind == "font":
                current = props.get(prop.name, prop.default)
                widget = QPushButton()
                widget.setProperty("fontValue", str(current))
                self._update_font_button(widget, current)
                widget.clicked.connect(
                    lambda _checked=False, key=prop.name, button=widget:
                    self._choose_font(key, button)
                )
            else:
                widget = QLineEdit(str(props.get(prop.name, prop.default)))
                widget.textChanged.connect(
                    lambda value, key=prop.name: self._set_value(key, value)
                )
            self.property_tree.setItemWidget(row, 1, widget)

        for group in groups.values():
            if group.childCount() == 0:
                self.property_tree.takeTopLevelItem(
                    self.property_tree.indexOfTopLevelItem(group)
                )

        enabled_ports = model.setdefault(
            "enabled_ports", default_enabled_ports(spec, instance_ports)
        )
        port_order = {
            "work_in": 0,
            "event_out": 1,
            "data_in": 2,
            "data_out": 3,
        }
        ordered_ports = sorted(
            enumerate(instance_ports),
            key=lambda pair: (
                port_order.get(pair[1].kind, 99),
                pair[0],
            ),
        )
        for _original_index, port in ordered_ports:
            row = QTreeWidgetItem([
                port.caption if port.caption != port.name
                else port.name
            ])
            row.setIcon(0, self._point_icon(port.kind))
            help_text = point_help(
                spec.type_name,
                port.name,
                port.caption,
                port.kind,
                port.description,
            )
            row.setToolTip(
                0,
                (
                    f"{port.name}\n"
                    f"Название: {port.caption}\n"
                    f"Тип: {self._point_kind_label(port.kind)}\n"
                    f"Назначение: {help_text}"
                ),
            )
            row.setData(0, Qt.ItemDataRole.UserRole, port.name)
            row.setData(0, Qt.ItemDataRole.UserRole + 1, port.kind)
            row.setData(
                0,
                Qt.ItemDataRole.UserRole + 3,
                f"{port.kind}:{port.name}",
            )
            row.setData(0, Qt.ItemDataRole.UserRole + 2, help_text)
            if port.required:
                row.setFlags(row.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                row.setToolTip(
                    0,
                    row.toolTip(0) + "\nОбязательная точка.",
                )
            else:
                row.setFlags(row.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            row.setCheckState(
                0,
                Qt.CheckState.Checked
                if port.name in enabled_ports
                else Qt.CheckState.Unchecked,
            )
            self.points_tree.addTopLevelItem(row)
        self.points_tree.blockSignals(False)
        self._set_diagnostic_status(diagnostic_errors)
        self.points_help.setPlainText(
            "Выберите точку. Здесь появится расширенная справка о её "
            "назначении, направлении и способе подключения."
        )
        self.property_help.setPlainText(
            "Выберите свойство. Внизу будет показано его назначение, тип, "
            "диапазон и текущее значение."
        )
        self._expand_primary_categories()
        QTimer.singleShot(0, self._expand_primary_categories)

    def _expand_primary_categories(self):
        """Keep the everyday property groups open after dynamic rebuilds."""
        for index in range(self.property_tree.topLevelItemCount()):
            item = self.property_tree.topLevelItem(index)
            if item.text(0) in {"Основные", "Положение и размер"}:
                item.setExpanded(True)

    def _filter_property_rows(self, text: str):
        query = text.strip().lower()
        for i in range(self.property_tree.topLevelItemCount()):
            top = self.property_tree.topLevelItem(i)
            if top.childCount() == 0:
                searchable = " ".join(
                    (
                        top.text(0),
                        top.text(1),
                        top.toolTip(0),
                        str(top.data(0, Qt.ItemDataRole.UserRole) or ""),
                        str(top.data(0, Qt.ItemDataRole.UserRole + 1) or ""),
                    )
                ).lower()
                top.setHidden(bool(query) and query not in searchable)
                continue
            visible = 0
            for j in range(top.childCount()):
                child = top.child(j)
                searchable = " ".join(
                    (
                        child.text(0),
                        child.text(1),
                        child.toolTip(0),
                        str(child.data(0, Qt.ItemDataRole.UserRole) or ""),
                        str(child.data(0, Qt.ItemDataRole.UserRole + 1) or ""),
                        str(child.data(0, Qt.ItemDataRole.UserRole + 4) or ""),
                    )
                ).lower()
                show = not query or query in searchable
                child.setHidden(not show)
                visible += int(show)
            top.setHidden(visible == 0)
            if (query and visible) or top.text(0) in {
                "Основные", "Положение и размер"
            }:
                top.setExpanded(True)

    def _set_value(self, key: str, value: Any):
        if self.model is not None:
            self.model.setdefault("properties", {})[key] = value
            self._set_diagnostic_status(diagnose_node_model(self.model))
            self.changed.emit()

    def _set_diagnostic_status(self, errors: list[str]):
        """Show the current contract state without hiding the editable tree."""
        if not errors:
            self.property_status.setText("✓ Проверка ноды: ошибок не найдено.")
            self.property_status.setStyleSheet(
                "QLabel { padding:4px 6px; border:1px solid #B7D7BE;"
                " background:#EEF8F0; color:#216E39; }"
            )
            return
        first = errors[0]
        suffix = f"  Ещё ошибок: {len(errors) - 1}." if len(errors) > 1 else ""
        self.property_status.setText(f"⚠ Проверка ноды: {first}{suffix}")
        self.property_status.setToolTip("\n".join(errors))
        self.property_status.setStyleSheet(
            "QLabel { padding:4px 6px; border:1px solid #E6B8B5;"
            " background:#FFF1F0; color:#B3261E; }"
        )

    def _property_selection_changed(self, current, previous):
        if current is None or self.model is None:
            self.property_help.setPlainText(
                "Выберите свойство. Здесь появится его описание."
            )
            return
        name = current.data(0, Qt.ItemDataRole.UserRole)
        if not name:
            self.property_help.setPlainText(
                current.toolTip(0) or "Группа свойств компонента."
            )
            return
        spec = COMPONENTS.get(self.model.get("type"))
        prop = next(
            (item for item in (spec.properties if spec else ()) if item.name == name),
            None,
        )
        if prop is None:
            self.property_help.setPlainText("Свойство больше не существует.")
            return
        value = self.model.get("properties", {}).get(prop.name, prop.default)
        lines = [
            f"{prop.caption}  ·  {prop.name}",
            f"Тип: {prop.kind}",
            f"Текущее значение: {value}",
        ]
        if prop.minimum is not None or prop.maximum is not None:
            lines.append(
                f"Диапазон: {prop.minimum if prop.minimum is not None else '—'}"
                f" … {prop.maximum if prop.maximum is not None else '—'}"
            )
        if prop.options:
            lines.append("Варианты: " + ", ".join(prop.options))
        lines.extend([
            "",
            prop.description or "Предметное описание для этого свойства пока не задано.",
        ])
        self.property_help.setPlainText("\n".join(lines))

    @staticmethod
    def _update_color_button(button: QPushButton, value: Any):
        color = to_qcolor(value)
        foreground = "#FFFFFF" if color.lightness() < 125 else "#202020"
        button.setText("  Выбрать цвет…")
        button.setToolTip(str(value))
        button.setStyleSheet(
            "QPushButton { text-align:left; padding:3px 7px;"
            f" background:{color.name()}; color:{foreground};"
            " border:1px solid #777; }"
        )

    def _choose_color(self, key: str, button: QPushButton):
        initial = to_qcolor(button.property("colorValue"))
        color = QColorDialog.getColor(
            initial, self, f"Цвет — {key}",
            QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if not color.isValid():
            return
        value = color.name(
            QColor.NameFormat.HexArgb
            if color.alpha() < 255
            else QColor.NameFormat.HexRgb
        ).upper()
        button.setProperty("colorValue", value)
        self._update_color_button(button, value)
        self._set_value(key, value)

    @staticmethod
    def _update_font_button(button: QPushButton, value: Any):
        font = to_qfont(value)
        styles = []
        if font.bold():
            styles.append("жирный")
        if font.italic():
            styles.append("курсив")
        suffix = f" · {', '.join(styles)}" if styles else ""
        button.setText(
            f"  {font.family()}, {font.pointSize()} pt{suffix}…"
        )
        button.setFont(font)
        button.setToolTip(str(value))
        button.setStyleSheet(
            "QPushButton { text-align:left; padding:3px 7px;"
            " background:#FFFFFF; color:#202020; border:1px solid #888; }"
        )

    def _choose_font(self, key: str, button: QPushButton):
        initial = to_qfont(button.property("fontValue"))
        # Use an explicit dialog instead of the static getFont() helper.
        # Different PySide6 Windows builds have returned that helper's tuple
        # differently, which made an accepted selection silently disappear.
        dialog = QFontDialog(initial, self)
        dialog.setWindowTitle(f"Шрифт — {key}")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        font = dialog.selectedFont()
        value = qfont_to_value(font, button.property("fontValue"))
        button.setProperty("fontValue", value)
        self._update_font_button(button, value)
        self._set_value(key, value)

    @staticmethod
    def _point_kind_label(kind: str) -> str:
        return {
            "event_out": "выход события",
            "work_in": "вход действия",
            "data_out": "выход данных",
            "data_in": "вход данных",
        }.get(kind, kind)

    @staticmethod
    def _point_role(kind: str) -> str:
        return {
            "event_out": "Сообщает, что событие произошло.",
            "work_in": "Запускает действие компонента.",
            "data_out": "Выдаёт значение для другой ноды.",
            "data_in": "Принимает значение от другой ноды.",
        }.get(kind, "Назначение точки определяется её типом.")

    @staticmethod
    def _point_icon(kind: str) -> QIcon:
        pixmap = QPixmap(13, 13)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = {
            "work_in": "#8E44AD",
            "event_out": "#D9A400",
            "data_in": "#1976D2",
            "data_out": "#00A6A6",
        }
        color = QColor(colors.get(kind, "#777777"))
        painter.setPen(QPen(color.darker(140), 1))
        painter.setBrush(color)
        if kind == "work_in":
            painter.drawPolygon(
                QPolygonF(
                    [
                        QPointF(6, 0.8),
                        QPointF(12, 6.5),
                        QPointF(6, 12),
                        QPointF(0.8, 6.5),
                    ]
                )
            )
        elif kind == "event_out":
            painter.drawPolygon(
                QPolygonF(
                    [
                        QPointF(7, 0.5),
                        QPointF(2, 7),
                        QPointF(6, 7),
                        QPointF(4.5, 12.5),
                        QPointF(11, 5),
                        QPointF(7, 5),
                    ]
                )
            )
        elif kind == "data_out":
            painter.drawEllipse(QRectF(2, 2, 9, 9))
        else:
            painter.drawRect(QRectF(2, 2, 9, 9))
        painter.end()
        return QIcon(pixmap)

    def _point_selection_changed(self, current, previous):
        if current is None:
            self.points_help.setPlainText(
                "Выберите точку. Здесь появится расширенная справка."
            )
            return
        port_name = current.data(0, Qt.ItemDataRole.UserRole)
        port_kind = current.data(0, Qt.ItemDataRole.UserRole + 1)
        if not self.model or not port_name:
            return
        ports = effective_ports(
            self.model["type"], self.model.get("properties", {})
        )
        port = next(
            (
                item for item in ports
                if item.name == port_name and (
                    not port_kind or item.kind == port_kind
                )
            ),
            None,
        )
        if port is None:
            return
        enabled = port.name in self.model.get("enabled_ports", [])
        status = "включена" if enabled else "отключена"
        description = current.data(0, Qt.ItemDataRole.UserRole + 2)
        if not description:
            description = point_help(
                self.model["type"],
                port.name,
                port.caption,
                port.kind,
                port.description,
            )
        connection_rule = {
            "event_out": "Соединять с входом действия.",
            "work_in": "Принимать от выхода события.",
            "data_out": "Соединять с входом данных.",
            "data_in": "Принимать от выхода данных.",
        }.get(port.kind, "")
        self.points_help.setPlainText(
            f"{port.name} — {port.caption}\n"
            f"Тип: {self._point_kind_label(port.kind)}\n"
            f"Состояние: {status}\n\n"
            f"{description}\n\n"
            f"Подключение: {connection_rule}"
        )

    def _point_state_changed(self, item: QTreeWidgetItem, column: int):
        if self.model is None or column != 0:
            return
        port_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not port_name:
            return
        model = self.model
        enable = item.checkState(0) == Qt.CheckState.Checked
        QTimer.singleShot(
            0,
            lambda current_model=model, name=port_name, state=enable:
                self.port_toggle_requested.emit(current_model, name, state),
        )
