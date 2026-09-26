from __future__ import annotations

from .common import *

from .canvas import (
    CanvasView,
    CollapsibleSection,
    CONTAINER_PROXY_TYPES,
    ContainerPaletteListWidget,
    ConnectionItem,
    DockTitleBar,
    GraphScene,
    HelperPaletteListWidget,
    NodeItem,
    PaletteListWidget,
    PortItem,
)
from .form_editor import (DashboardDesignerDialog, DashboardDesignerScene, FormControlItem, FormScene, FormWindowItem)
from .property_panel import PropertyPanel
from .debugging import (
    DEBUG_STREAM_PREFIX,
    format_diagnostic,
    runtime_diagnostics,
    write_debug_log,
)
from model_contract import diagnose_event_flow, diagnose_node_model
from connection_advisor import advise_connection
from version import APP_NAME, APP_VERSION
from user_help import (
    BEGINNER_GUIDE,
    DYNAMIC_GAME_GUIDE,
    component_search_text,
    format_component_help,
    node_instance_label,
    node_instance_search_text,
    project_node_records,
)
from container_library import (
    INTERFACE_DATA_TYPES,
    INTERFACE_KINDS,
    apply_container_interface,
    delete_user_template,
    discover_container_library,
    ensure_user_category,
    instantiate_container_template,
    save_container_template,
    validate_container_model,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_path: Path | None = None
        self.project_name = "Новый проект"
        self.modified = False
        self._container_stack: list[tuple[dict[str, Any], str, str]] = []
        self._history: list[dict[str, Any]] = []
        self._history_index = -1
        self._restoring_history = False
        self._history_timer = QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.setInterval(250)
        self._history_timer.timeout.connect(self._push_history)
        self._clipboard: dict[str, Any] | None = None
        self._preview_source = ""
        self._preview_path: Path | None = None
        self._runtime_stdout = ""
        self._runtime_stderr = ""
        self._runtime_stdout_buffer = ""
        self._debug_log_path: Path | None = None
        self._debug_rows: dict[str, int] = {}
        self._debug_mode_active = False
        self._debug_animation_armed = True
        self._debug_waiting_flow = False
        self._debug_original_geometry = None
        self._debug_original_maximized = False
        self._debug_preview_geometry = None
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1380, 820)
        self.setMinimumSize(980, 620)

        self.scene = GraphScene()
        self.view = CanvasView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.scheme_page = QWidget()
        scheme_layout = QVBoxLayout(self.scheme_page)
        scheme_layout.setContentsMargins(0, 0, 0, 0)
        scheme_layout.setSpacing(0)
        self.container_path_bar = QFrame()
        self.container_path_bar.setObjectName("containerPathBar")
        self.container_path_bar.setStyleSheet(
            "#containerPathBar {"
            "background:#F3F6F8; border-bottom:1px solid #CDD5DC;"
            "}"
        )
        self.container_path_layout = QHBoxLayout(
            self.container_path_bar
        )
        self.container_path_layout.setContentsMargins(6, 3, 6, 3)
        self.container_path_layout.setSpacing(3)
        self.container_back_button = QPushButton("← На уровень выше")
        self.container_back_button.setToolTip(
            "Сохранить текущую внутреннюю схему и вернуться"
        )
        self.container_back_button.clicked.connect(
            self._return_from_container
        )
        self.container_path_layout.addWidget(
            self.container_back_button
        )
        self.container_path_layout.addSpacing(8)
        scheme_layout.addWidget(self.container_path_bar)
        scheme_layout.addWidget(self.view, 1)

        self.form_scene = FormScene()
        self.form_view = CanvasView(self.form_scene)
        self.form_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.form_view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.view.zoom_changed.connect(self._show_zoom)
        self.form_view.zoom_changed.connect(self._show_zoom)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.scheme_page, "Схема")
        self.tabs.addTab(self.form_view, "Форма")
        self.code_preview = QPlainTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.code_preview.setPlaceholderText("Здесь появится созданный Python-код.")
        self.tabs.addTab(self.code_preview, "Код")
        self.setCentralWidget(self.tabs)

        self.preview_process = QProcess(self)
        self.preview_process.setProcessChannelMode(
            QProcess.ProcessChannelMode.SeparateChannels
        )
        self.preview_process.readyReadStandardOutput.connect(
            self._read_process_output
        )
        self.preview_process.readyReadStandardError.connect(
            self._read_process_error
        )
        self.preview_process.finished.connect(self._process_finished)

        self._create_palette()
        self._create_properties()
        self._create_navigator()
        self._create_console()
        self._create_problems()
        self._create_debugger()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._apply_style()
        workspace = QSettings("VisualPythonBuilder", "VisualPythonBuilder")
        geometry = workspace.value("workspace/geometry")
        state = workspace.value("workspace/state")
        if geometry is not None:
            self.restoreGeometry(geometry)
        if state is not None:
            self.restoreState(state)

        self.scene.node_selected.connect(self.properties.set_node)
        self.scene.node_selected.connect(self._sync_navigator_selection)
        self.scene.project_loaded.connect(self._refresh_navigator)
        self.scene.project_loaded.connect(
            self._update_container_breadcrumb
        )
        self.scene.helper_dropped.connect(self._helper_dropped)
        self.scene.container_dropped.connect(self._container_template_dropped)
        self.scene.node_action_requested.connect(self._graph_node_action)
        self.scene.canvas_action_requested.connect(self._graph_canvas_action)
        self.view.component_dropped.connect(self.add_component)
        self.view.container_dropped.connect(
            self._container_template_dropped
        )
        self.scene.component_dropped.connect(self.add_component)
        self.form_view.component_dropped.connect(
            self.add_component_to_form
        )
        self.form_scene.node_selected.connect(self.properties.set_node)
        self.form_scene.node_action_requested.connect(
            self._form_node_action
        )
        self.form_scene.form_action_requested.connect(
            self._form_scene_action
        )
        self.scene.changed_model.connect(self._scene_changed)
        self.scene.connection_hint.connect(
            lambda text: self.statusBar().showMessage(text, 6000)
        )
        self.form_scene.changed_model.connect(self._form_model_changed)
        self.properties.changed.connect(self._property_changed)
        self.properties.port_toggle_requested.connect(
            self._port_toggle_requested
        )
        self.tabs.currentChanged.connect(self._tab_changed)
        self.statusBar().showMessage(
            f"Готово · Python-нод: {len(COMPONENTS)} · "
            "колесико: масштаб · ЛКМ по фону: перемещение полотна"
        )
        # Редактор всегда открывается чистым. Примеры доступны из меню
        # «Примеры» и не должны неожиданно перекрывать рабочую схему.
        self.new_project()
        # The diagnostics dock is part of the permanent workspace.  Old
        # saved layouts could contain a hidden problemsDock, so restore its
        # visibility after the initial clean project is created.
        self.problems_dock.show()

    def _create_palette(self):
        dock = QDockWidget("Элементы", self)
        dock.setObjectName("paletteDock")
        dock.setMinimumWidth(245)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        search = QLineEdit()
        search.setPlaceholderText("Поиск элемента...")
        layout.addWidget(search)
        sections_widget = QWidget()
        sections_layout = QVBoxLayout(sections_widget)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(1)
        layout.addWidget(sections_widget)
        layout.addStretch(1)

        grouped: dict[str, dict[str, list[ComponentSpec]]] = {}
        for spec in COMPONENTS.values():
            subgroup = spec.subgroup.strip()
            grouped.setdefault(spec.category, {}).setdefault(
                subgroup, []
            ).append(spec)

        self.palette_lists: list[PaletteListWidget] = []
        self.palette_sections: list[CollapsibleSection] = []
        self.palette_subsections: list[CollapsibleSection] = []

        def create_palette(specs: list[ComponentSpec]) -> PaletteListWidget:
            palette = PaletteListWidget()
            palette.setViewMode(QListWidget.ViewMode.IconMode)
            palette.setMovement(QListWidget.Movement.Static)
            palette.setResizeMode(QListWidget.ResizeMode.Adjust)
            palette.setIconSize(QPixmap(32, 32).size())
            palette.setGridSize(QPixmap(68, 62).size())
            palette.setSpacing(1)
            palette.setWordWrap(True)
            palette.setSelectionMode(
                QAbstractItemView.SelectionMode.SingleSelection
            )
            palette.itemDoubleClicked.connect(
                self._palette_double_clicked
            )
            palette.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            palette.customContextMenuRequested.connect(
                lambda pos, current=palette: self._palette_context_menu(current, pos)
            )
            for spec in specs:
                icon_path = component_icon_path(spec.type_name)
                if icon_path:
                    icon = QIcon(str(icon_path))
                else:
                    pixmap = QPixmap(32, 32)
                    pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(pixmap)
                    painter.setRenderHint(
                        QPainter.RenderHint.Antialiasing
                    )
                    painter.setBrush(QColor(spec.color))
                    painter.setPen(QPen(QColor("#BDBCB9"), 1))
                    painter.drawRect(1, 1, 30, 30)
                    painter.setPen(QColor("#2C2C2B"))
                    font = painter.font()
                    font.setBold(True)
                    font.setPointSize(9)
                    painter.setFont(font)
                    painter.drawText(
                        pixmap.rect(),
                        Qt.AlignmentFlag.AlignCenter,
                        NODE_SYMBOLS.get(spec.type_name, "◆"),
                    )
                    painter.end()
                    icon = QIcon(pixmap)
                item = QListWidgetItem(icon, spec.caption)
                item.setData(
                    Qt.ItemDataRole.UserRole, spec.type_name
                )
                item.setData(
                    Qt.ItemDataRole.UserRole + 1,
                    component_search_text(spec),
                )
                status = (
                    "Генератор Python реализован"
                    if spec.implemented
                    else {
                        "работает": "Статус: работает и проверен",
                        "частично": "Статус: реализовано частично",
                        "заглушка": "Статус: заглушка — поведение ещё не перенесено",
                    }.get(spec.support_status, f"Статус: {spec.support_status}")
                )
                details = (
                    f"\n{spec.description}"
                    if spec.description
                    else ""
                )
                item.setToolTip(
                    f"{spec.caption}\n{spec.type_name}\n"
                    f"{status}{details}"
                )
                palette.addItem(item)
            palette.height_changed.connect(
                lambda: QTimer.singleShot(
                    0, self._refresh_palette_layout
                )
            )
            self.palette_lists.append(palette)
            return palette

        for category_index, (category, subgroups) in enumerate(
            grouped.items()
        ):
            section = CollapsibleSection(
                category, expanded=category_index == 1
            )
            self.palette_sections.append(section)
            sections_layout.addWidget(section)
            section.expansion_changed.connect(
                lambda expanded, current=section:
                self._palette_section_toggled(current, expanded)
            )
            has_named_subgroups = any(subgroups)
            if has_named_subgroups:
                ordered_subgroups = []
                if "" in subgroups:
                    ordered_subgroups.append(
                        ("Основные", subgroups[""])
                    )
                ordered_subgroups.extend(
                    (name, specs)
                    for name, specs in subgroups.items()
                    if name
                )
                for subgroup_index, (name, specs) in enumerate(
                    ordered_subgroups
                ):
                    subsection = CollapsibleSection(
                        name,
                        expanded=subgroup_index == 0,
                        nested=True,
                    )
                    self.palette_subsections.append(subsection)
                    section.content_layout.addWidget(subsection)
                    subsection.content_layout.addWidget(
                        create_palette(specs)
                    )
                    subsection.expansion_changed.connect(
                        lambda _expanded: QTimer.singleShot(
                            0, self._refresh_palette_layout
                        )
                    )
            else:
                specs = next(iter(subgroups.values()), [])
                section.content_layout.addWidget(
                    create_palette(specs)
                )

        sections_layout.addStretch(1)
        self.palette_container = container
        self.palette_scroll = scroll
        for palette in self.palette_lists:
            palette.refresh_height()
        search.textChanged.connect(self._filter_palette)
        scroll.setWidget(container)
        helpers_page = QWidget()
        helpers_layout = QVBoxLayout(helpers_page)
        helpers_layout.setContentsMargins(4, 4, 4, 4)
        helpers_intro = QLabel(
            "Вспомогательные элементы для пояснения схемы. "
            "Двойной щелчок добавляет выбранный объект на холст."
        )
        helpers_intro.setWordWrap(True)
        helpers_intro.setStyleSheet("color:#555; padding:3px;")
        helpers_layout.addWidget(helpers_intro)
        self.helpers_list = HelperPaletteListWidget()
        self.helpers_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.helpers_list.setMovement(QListWidget.Movement.Static)
        self.helpers_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.helpers_list.setIconSize(QSize(32, 32))
        self.helpers_list.setGridSize(QSize(86, 70))
        self.helpers_list.setWordWrap(True)
        self.helpers_list.itemDoubleClicked.connect(
            self._helper_double_clicked
        )
        helper_items = (
            (
                "helper:text",
                "Текст",
                "Отдельная надпись без фигуры. Настройте текст, шрифт, цвет, "
                "прозрачность и положение.",
                "#FFFFFF",
                "A",
            ),
            (
                "helper:shape",
                "Фигура",
                "Отдельная фигура. Форма, цвет, рамка, прозрачность и размер. "
                "Размер можно менять мышью за правый нижний угол.",
                "#DCEAF7",
                "□",
            ),
        )
        for helper_id, title, tooltip, color, symbol in helper_items:
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(color))
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor("#777777"), 1))
            painter.drawRect(1, 1, 30, 30)
            painter.setPen(QColor("#333333"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(15)
            painter.setFont(font)
            painter.drawText(
                pixmap.rect(), Qt.AlignmentFlag.AlignCenter, symbol
            )
            painter.end()
            item = QListWidgetItem(QIcon(pixmap), title)
            item.setData(Qt.ItemDataRole.UserRole, helper_id)
            item.setToolTip(f"{title}\n{tooltip}")
            self.helpers_list.addItem(item)
        helpers_layout.addWidget(self.helpers_list, 1)
        helpers_help = QPlainTextEdit()
        helpers_help.setReadOnly(True)
        helpers_help.setPlainText(
            "Перетащите «Текст» или «Фигура» на холст. "
            "ПКМ или двойной щелчок открывает настройку. Размер фигуры можно "
            "менять мышью за правый нижний угол. Помощники не участвуют "
            "в генерации программы."
        )
        helpers_help.setMaximumHeight(92)
        helpers_layout.addWidget(helpers_help)
        palette_tabs = QTabWidget()
        palette_tabs.addTab(scroll, "Элементы")
        palette_tabs.addTab(helpers_page, "Помощники")
        palette_tabs.addTab(
            self._build_container_palette_page(), "Контейнеры"
        )
        self.palette_tabs = palette_tabs
        dock.setWidget(palette_tabs)
        dock.setTitleBarWidget(
            DockTitleBar(dock, "Элементы", "left")
        )
        self.palette_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        QTimer.singleShot(0, self._refresh_palette_layout)

    def _filter_palette(self, text: str):
        query = text.strip().lower()
        for palette in self.palette_lists:
            for index in range(palette.count()):
                item = palette.item(index)
                type_name = str(item.data(Qt.ItemDataRole.UserRole))
                search_text = str(
                    item.data(Qt.ItemDataRole.UserRole + 1) or ""
                )
                item.setHidden(
                    bool(query)
                    and not all(
                        word in search_text
                        for word in query.split()
                        if word
                    )
                )
            palette.refresh_height()
        self._refresh_palette_layout()

    def _palette_section_toggled(
        self, current: CollapsibleSection, expanded: bool
    ):
        if expanded:
            for section in self.palette_sections:
                if section is not current and section.button.isChecked():
                    section.set_expanded(False)
        QTimer.singleShot(0, self._refresh_palette_layout)

    def _refresh_palette_layout(self):
        for palette in self.palette_lists:
            if palette.isVisible():
                palette.refresh_height()
        self.palette_container.adjustSize()
        self.palette_container.updateGeometry()

    def _build_container_palette_page(self):
        templates, declared_categories = discover_container_library()
        self.container_templates = {
            str(item.get("id")): item for item in templates
        }
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(4, 4, 4, 4)
        intro = QLabel(
            "Готовые решения собраны только из обычных нод. "
            "Перетащите контейнер на схему, затем откройте его двойным "
            "щелчком, чтобы изучить или изменить внутренности."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#555; padding:3px;")
        page_layout.addWidget(intro)
        controls = QHBoxLayout()
        create_category = QPushButton("Новый раздел…")
        create_category.setToolTip(
            "Создать свою категорию и необязательную подкатегорию"
        )
        create_category.clicked.connect(self._create_container_category)
        save_selected = QPushButton("Сохранить контейнер…")
        save_selected.setToolTip(
            "Сохранить выделенный пользовательский контейнер в палитру"
        )
        save_selected.clicked.connect(
            lambda: self._save_selected_container_to_library()
        )
        controls.addWidget(create_category)
        controls.addWidget(save_selected)
        page_layout.addLayout(controls)
        search = QLineEdit()
        search.setPlaceholderText("Поиск готового контейнера…")
        search.setClearButtonEnabled(True)
        page_layout.addWidget(search)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(1)
        grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for item in templates:
            category = str(item.get("category") or "Готовые")
            subgroup = str(item.get("subgroup") or "")
            grouped.setdefault(category, {}).setdefault(subgroup, []).append(item)
        for category in declared_categories:
            name = str(category.get("name") or "").strip()
            if not name:
                continue
            group = grouped.setdefault(name, {})
            for subgroup in category.get("subgroups", []):
                group.setdefault(str(subgroup), [])

        self.container_palette_lists = []
        for category_index, (category, subgroups) in enumerate(
            sorted(grouped.items(), key=lambda pair: pair[0].lower())
        ):
            section = CollapsibleSection(
                category, expanded=category_index == 0
            )
            content_layout.addWidget(section)
            ordered = sorted(
                subgroups.items(),
                key=lambda pair: (not bool(pair[0]), pair[0].lower()),
            )
            for subgroup, items in ordered:
                target_layout = section.content_layout
                if subgroup:
                    subsection = CollapsibleSection(
                        subgroup, expanded=True, nested=True
                    )
                    section.content_layout.addWidget(subsection)
                    target_layout = subsection.content_layout
                if not items:
                    empty = QLabel("Пока нет контейнеров")
                    empty.setStyleSheet("color:#888; padding:5px 9px;")
                    target_layout.addWidget(empty)
                    continue
                palette = ContainerPaletteListWidget()
                palette.setViewMode(QListWidget.ViewMode.IconMode)
                palette.setMovement(QListWidget.Movement.Static)
                palette.setResizeMode(QListWidget.ResizeMode.Adjust)
                palette.setIconSize(QSize(32, 32))
                palette.setGridSize(QSize(96, 72))
                palette.setWordWrap(True)
                palette.itemDoubleClicked.connect(
                    self._container_palette_double_clicked
                )
                palette.setContextMenuPolicy(
                    Qt.ContextMenuPolicy.CustomContextMenu
                )
                palette.customContextMenuRequested.connect(
                    lambda pos, current=palette:
                    self._container_palette_context_menu(current, pos)
                )
                for template in sorted(
                    items, key=lambda value: str(value.get("title", "")).lower()
                ):
                    pixmap = QPixmap(32, 32)
                    pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setBrush(QColor("#E9E1F8"))
                    painter.setPen(QPen(QColor("#534080"), 2))
                    painter.drawRoundedRect(2, 2, 28, 28, 5, 5)
                    painter.setPen(QColor("#3D2B66"))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                    painter.drawText(
                        pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "К"
                    )
                    painter.end()
                    item = QListWidgetItem(
                        QIcon(pixmap), str(template.get("title"))
                    )
                    item.setData(
                        Qt.ItemDataRole.UserRole, str(template.get("id"))
                    )
                    search_text = " ".join(
                        str(template.get(key, ""))
                        for key in (
                            "title", "category", "subgroup", "description"
                        )
                    ).lower()
                    item.setData(
                        Qt.ItemDataRole.UserRole + 1, search_text
                    )
                    source = (
                        "Пользовательский"
                        if template.get("source") == "user"
                        else "Встроенный"
                    )
                    item.setToolTip(
                        f"{template.get('title')}\n{source} контейнер\n"
                        f"{template.get('description', '')}\n"
                        "Двойной щелчок — добавить; после добавления "
                        "двойной щелчок по ноде — открыть внутреннюю схему."
                    )
                    palette.addItem(item)
                target_layout.addWidget(palette)
                self.container_palette_lists.append(palette)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)
        search.textChanged.connect(self._filter_container_palette)
        return page

    def _refresh_container_palette(self):
        if not hasattr(self, "palette_tabs"):
            return
        index = next(
            (
                i for i in range(self.palette_tabs.count())
                if self.palette_tabs.tabText(i) == "Контейнеры"
            ),
            -1,
        )
        page = self._build_container_palette_page()
        if index >= 0:
            old = self.palette_tabs.widget(index)
            self.palette_tabs.removeTab(index)
            old.deleteLater()
            self.palette_tabs.insertTab(index, page, "Контейнеры")
            self.palette_tabs.setCurrentIndex(index)
        else:
            self.palette_tabs.addTab(page, "Контейнеры")

    def _filter_container_palette(self, text: str):
        words = [word for word in text.strip().lower().split() if word]
        for palette in getattr(self, "container_palette_lists", []):
            visible = 0
            for index in range(palette.count()):
                item = palette.item(index)
                search_text = str(
                    item.data(Qt.ItemDataRole.UserRole + 1) or ""
                )
                hidden = bool(words) and not all(
                    word in search_text for word in words
                )
                item.setHidden(hidden)
                visible += not hidden
            palette.setVisible(bool(visible) or not words)
            palette.refresh_height()

    def _container_palette_double_clicked(self, item: QListWidgetItem):
        template_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not template_id:
            return
        self.tabs.setCurrentIndex(0)
        center = self.view.mapToScene(self.view.viewport().rect().center())
        self._add_container_template(template_id, center)

    def _container_palette_context_menu(
        self, palette: ContainerPaletteListWidget, position
    ):
        item = palette.itemAt(position)
        if item is None:
            return
        template_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        template = self.container_templates.get(template_id)
        if template is None:
            return
        menu = QMenu(palette)
        add = menu.addAction("Добавить на схему")
        inspect = menu.addAction("Описание и состав…")
        delete = menu.addAction("Удалить из моей библиотеки")
        delete.setVisible(template.get("source") == "user")
        selected = menu.exec(palette.mapToGlobal(position))
        if selected == add:
            self._container_palette_double_clicked(item)
        elif selected == inspect:
            model = template.get("model", {})
            subgraph = model.get("properties", {}).get("subgraph", {})
            nodes = subgraph.get("nodes", []) if isinstance(subgraph, dict) else []
            lines = [
                str(template.get("title")),
                "=" * len(str(template.get("title"))),
                "",
                str(template.get("description") or "Описание не заполнено."),
                "",
                f"Категория: {template.get('category')}",
                f"Подкатегория: {template.get('subgroup') or 'Основные'}",
                f"Внутри нод: {len(nodes)}",
                "",
                "СОСТАВ",
            ]
            for node in nodes:
                spec = COMPONENTS.get(str(node.get("type")))
                lines.append(
                    "• " + (spec.caption if spec else str(node.get("type")))
                )
            lines.extend([
                "",
                "После добавления дважды щёлкните по контейнеру на схеме, "
                "чтобы открыть и изменить его внутренности.",
            ])
            self._show_text_help(
                f"Контейнер: {template.get('title')}", "\n".join(lines)
            )
        elif selected == delete:
            answer = QMessageBox.question(
                self,
                "Удалить контейнер",
                f"Удалить «{template.get('title')}» из пользовательской библиотеки?",
            )
            if answer == QMessageBox.StandardButton.Yes:
                delete_user_template(template_id)
                self._refresh_container_palette()

    def _add_container_template(
        self, template_id: str, position: QPointF
    ):
        template = getattr(self, "container_templates", {}).get(template_id)
        if template is None:
            QMessageBox.warning(
                self, "Контейнер", "Шаблон контейнера больше не найден."
            )
            return
        position = self._free_graph_position(position)
        model = instantiate_container_template(
            template, position.x(), position.y()
        )
        self.scene.clearSelection()
        item = self.scene.add_node(model)
        item.setSelected(True)
        self._refresh_form()
        self._mark_modified()
        self._schedule_history()
        self.statusBar().showMessage(
            f"Добавлен контейнер «{template.get('title')}». "
            "Двойной щелчок открывает внутреннюю схему.",
            6000,
        )

    def _container_template_dropped(
        self, template_id: str, position: QPointF
    ):
        self._add_container_template(template_id, position)

    def _create_container_category(self):
        category, accepted = QInputDialog.getText(
            self, "Новая категория", "Название категории:"
        )
        if not accepted or not category.strip():
            return
        subgroup, accepted = QInputDialog.getText(
            self,
            "Новая подкатегория",
            "Подкатегория (можно оставить пустой):",
        )
        if not accepted:
            return
        try:
            ensure_user_category(category, subgroup)
        except OSError as exc:
            QMessageBox.warning(self, "Библиотека контейнеров", str(exc))
            return
        self._refresh_container_palette()

    def _save_selected_container_to_library(
        self, model: dict[str, Any] | None = None
    ):
        if model is None:
            selected = [
                item.model for item in self.scene.selectedItems()
                if isinstance(item, NodeItem)
                and item.model.get("type") == "UserContainer"
            ]
            if len(selected) != 1:
                QMessageBox.information(
                    self,
                    "Сохранить контейнер",
                    "Выделите один пользовательский контейнер на схеме.",
                )
                return
            model = selected[0]
        templates, categories = discover_container_library()
        dialog = QDialog(self)
        dialog.setWindowTitle("Сохранить контейнер в библиотеку")
        dialog.resize(470, 300)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        title = QLineEdit(
            str(model.get("properties", {}).get("name", "Новый контейнер"))
        )
        model_props = model.setdefault("properties", {})
        category = QComboBox()
        category.setEditable(True)
        known_categories = sorted({
            str(item.get("category")) for item in templates
            if str(item.get("category", "")).strip()
        } | {
            str(item.get("name")) for item in categories
            if str(item.get("name", "")).strip()
        })
        category.addItems(known_categories or ["Мои контейнеры"])
        category.setCurrentText(
            str(model_props.get("category", "Мои контейнеры"))
        )
        subgroup = QLineEdit(str(model_props.get("subgroup", "Основные")))
        description = QPlainTextEdit()
        description.setPlainText(str(model_props.get("description", "")))
        description.setPlaceholderText(
            "Что делает контейнер и какие данные принимает…"
        )
        description.setMaximumHeight(90)
        form.addRow("Название", title)
        form.addRow("Категория", category)
        form.addRow("Подкатегория", subgroup)
        form.addRow("Описание", description)
        layout.addLayout(form)
        hint = QLabel(
            "Сохраняется внутренняя схема из обычных нод. "
            "После добавления из палитры её можно открыть и изменить."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        model_props["name"] = title.text().strip() or "Новый контейнер"
        model_props["category"] = (
            category.currentText().strip() or "Мои контейнеры"
        )
        model_props["subgroup"] = subgroup.text().strip() or "Основные"
        model_props["description"] = description.toPlainText().strip()
        try:
            save_container_template(
                model,
                model_props["name"],
                model_props["category"],
                model_props["subgroup"],
                model_props["description"],
            )
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Сохранить контейнер", str(exc))
            return
        self._refresh_container_palette()
        self.statusBar().showMessage(
            "Контейнер сохранён в пользовательскую библиотеку.", 5000
        )

    def _create_properties(self):
        dock = QDockWidget("Свойства", self)
        dock.setObjectName("propertiesDock")
        dock.setMinimumWidth(280)
        self.properties = PropertyPanel()
        dock.setWidget(self.properties)
        dock.setTitleBarWidget(
            DockTitleBar(dock, "Свойства", "right")
        )
        self.properties_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_navigator(self):
        dock = QDockWidget("Навигатор схемы", self)
        dock.setObjectName("navigatorDock")
        dock.setMinimumWidth(300)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)
        self.navigator_path = QLabel("Текущий уровень: Главная схема")
        self.navigator_path.setWordWrap(True)
        self.navigator_path.setStyleSheet(
            "color:#455A64; font-weight:600;"
        )
        layout.addWidget(self.navigator_path)
        self.navigator_search = QLineEdit()
        self.navigator_search.setPlaceholderText(
            "Найти установленную ноду…"
        )
        layout.addWidget(self.navigator_search)
        self.navigator_all_levels = QCheckBox(
            "Искать внутри вложенных контейнеров"
        )
        self.navigator_all_levels.setChecked(True)
        layout.addWidget(self.navigator_all_levels)
        self.navigator_results = QTreeWidget()
        self.navigator_results.setColumnCount(2)
        self.navigator_results.setHeaderLabels(["Нода", "Путь"])
        self.navigator_results.setRootIsDecorated(False)
        self.navigator_results.setAlternatingRowColors(True)
        self.navigator_results.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.navigator_results.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.navigator_results, 1)
        self.navigator_count = QLabel("Нод: 0")
        self.navigator_count.setStyleSheet("color:#666;")
        layout.addWidget(self.navigator_count)
        dock.setWidget(container)
        dock.setTitleBarWidget(
            DockTitleBar(dock, "Навигатор схемы", "right")
        )
        self.navigator_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.tabifyDockWidget(self.properties_dock, dock)
        dock.hide()
        self.navigator_search.textChanged.connect(
            self._refresh_navigator
        )
        self.navigator_all_levels.toggled.connect(
            self._refresh_navigator
        )
        self.navigator_results.itemActivated.connect(
            self._navigator_item_activated
        )
        self._navigator_timer = QTimer(self)
        self._navigator_timer.setSingleShot(True)
        self._navigator_timer.setInterval(160)
        self._navigator_timer.timeout.connect(self._refresh_navigator)

    def _current_container_path(self):
        return (
            tuple(item[1] for item in self._container_stack),
            tuple(item[2] for item in self._container_stack),
        )

    def _update_container_breadcrumb(self):
        if not hasattr(self, "container_path_layout"):
            return
        old_stretch = getattr(self, "_breadcrumb_stretch", None)
        if old_stretch is not None:
            self.container_path_layout.removeItem(old_stretch)
        for widget in getattr(self, "_breadcrumb_widgets", []):
            self.container_path_layout.removeWidget(widget)
            widget.deleteLater()
        self._breadcrumb_widgets = []
        depth = len(self._container_stack)
        self.container_back_button.setEnabled(depth > 0)

        def add_path_button(text: str, target_depth: int, current=False):
            button = QPushButton(text)
            button.setFlat(True)
            button.setEnabled(not current)
            button.setStyleSheet(
                "QPushButton { padding:2px 6px; text-align:left; }"
                + (
                    "QPushButton:disabled { color:#183B63; "
                    "font-weight:700; }"
                    if current else ""
                )
            )
            button.setToolTip(
                "Текущий уровень"
                if current else
                "Сохранить изменения и перейти к этому уровню"
            )
            if not current:
                button.clicked.connect(
                    lambda _checked=False, level=target_depth:
                    self._navigate_container_depth(level)
                )
            self.container_path_layout.addWidget(button)
            self._breadcrumb_widgets.append(button)

        add_path_button("Главная схема", 0, current=depth == 0)
        for index, (_parent, _container_id, title) in enumerate(
            self._container_stack, 1
        ):
            separator = QLabel("›")
            separator.setStyleSheet("color:#78909C;")
            self.container_path_layout.addWidget(separator)
            self._breadcrumb_widgets.append(separator)
            add_path_button(
                title or "Контейнер",
                index,
                current=index == depth,
            )
        self.container_path_layout.addStretch(1)
        self._breadcrumb_stretch = self.container_path_layout.itemAt(
            self.container_path_layout.count() - 1
        )

    def _navigate_container_depth(self, target_depth: int):
        target_depth = max(
            0, min(int(target_depth), len(self._container_stack))
        )
        while len(self._container_stack) > target_depth:
            self._return_from_container()
        self.tabs.setCurrentWidget(self.scheme_page)
        self._update_container_breadcrumb()

    def _reset_container_navigation(self):
        self._container_stack.clear()
        self.scene.in_container = False
        self._update_container_breadcrumb()

    def _navigator_root_project(self):
        project = copy.deepcopy(
            self.scene.to_project(self.project_name)
        )
        for parent, container_id, _title in reversed(
            self._container_stack
        ):
            outer = copy.deepcopy(parent)
            container = next(
                (
                    node for node in outer.get("nodes", [])
                    if str(node.get("id")) == str(container_id)
                ),
                None,
            )
            if container is not None:
                container.setdefault("properties", {})["subgraph"] = project
            project = outer
        return project

    def _refresh_navigator(self):
        if not hasattr(self, "navigator_results"):
            return
        current = self.navigator_results.currentItem()
        current_key = (
            (
                tuple(current.data(0, Qt.ItemDataRole.UserRole + 1) or ()),
                str(current.data(0, Qt.ItemDataRole.UserRole)),
            )
            if current is not None else ""
        )
        query = self.navigator_search.text().strip().lower()
        words = query.split()
        current_ids, current_names = self._current_container_path()
        breadcrumb = "Главная схема"
        if current_names:
            breadcrumb += " → " + " → ".join(current_names)
        self.navigator_path.setText(
            "Текущий уровень: " + breadcrumb
        )
        if self.navigator_all_levels.isChecked():
            records = project_node_records(
                self._navigator_root_project()
            )
        else:
            records = [
                {
                    "model": node.model,
                    "path_ids": current_ids,
                    "path_names": current_names,
                }
                for node in self.scene.nodes.values()
            ]
        rows = []
        for record in records:
            model = record["model"]
            if str(model.get("type")) in CONTAINER_PROXY_TYPES:
                continue
            search = node_instance_search_text(model)
            if words and not all(word in search for word in words):
                continue
            rows.append((
                node_instance_label(model).lower(),
                model,
                tuple(record["path_ids"]),
                tuple(record["path_names"]),
            ))
        rows.sort(key=lambda pair: pair[0])
        self.navigator_results.clear()
        selected_item = None
        for _label, model, path_ids, path_names in rows:
            spec = COMPONENTS.get(str(model.get("type", "")))
            if spec is None:
                continue
            path_text = (
                "Главная схема"
                + (
                    " → " + " → ".join(path_names)
                    if path_names else ""
                )
            )
            item = QTreeWidgetItem([
                node_instance_label(model),
                path_text,
            ])
            node_id = str(model.get("id", ""))
            item.setData(0, Qt.ItemDataRole.UserRole, node_id)
            item.setData(
                0, Qt.ItemDataRole.UserRole + 1, list(path_ids)
            )
            item.setToolTip(
                0,
                f"{spec.description or 'Описание пока не заполнено.'}\n"
                f"Тип: {spec.type_name}\n"
                f"ID: {node_id}\n"
                f"Путь: {path_text}\n"
                f"Положение: {round(float(model.get('x', 0)))}, "
                f"{round(float(model.get('y', 0)))}",
            )
            self.navigator_results.addTopLevelItem(item)
            key = (path_ids, node_id)
            live_node = (
                self.scene.nodes.get(node_id)
                if path_ids == current_ids else None
            )
            if (
                key == current_key
                or (live_node is not None and live_node.isSelected())
            ):
                selected_item = item
        if selected_item is not None:
            self.navigator_results.setCurrentItem(selected_item)
        self.navigator_count.setText(
            f"Найдено: {len(rows)}"
            + (
                " во всём проекте"
                if self.navigator_all_levels.isChecked()
                else " на текущем уровне"
            )
        )

    def _schedule_navigator_refresh(self):
        if hasattr(self, "_navigator_timer"):
            self._navigator_timer.start()

    def _sync_navigator_selection(self, model):
        if not hasattr(self, "navigator_results") or model is None:
            return
        node_id = str(model.get("id", ""))
        current_ids, _current_names = self._current_container_path()
        for index in range(self.navigator_results.topLevelItemCount()):
            item = self.navigator_results.topLevelItem(index)
            item_path = tuple(
                item.data(0, Qt.ItemDataRole.UserRole + 1) or ()
            )
            if (
                str(item.data(0, Qt.ItemDataRole.UserRole)) == node_id
                and item_path == current_ids
            ):
                self.navigator_results.setCurrentItem(item)
                break

    def _navigator_item_activated(self, item, _column=0):
        node_id = str(item.data(0, Qt.ItemDataRole.UserRole) or "")
        path_ids = tuple(
            item.data(0, Qt.ItemDataRole.UserRole + 1) or ()
        )
        current_ids, _current_names = self._current_container_path()
        if path_ids != current_ids:
            self._commit_all_containers()
            for container_id in path_ids:
                container = self.scene.nodes.get(str(container_id))
                if (
                    container is None
                    or container.spec.type_name != "UserContainer"
                ):
                    QMessageBox.warning(
                        self,
                        "Навигатор схемы",
                        "Путь к ноде изменился. Обновите поиск и "
                        "выберите результат ещё раз.",
                    )
                    self._refresh_navigator()
                    return
                self._open_user_container(container.model)
        node = self.scene.nodes.get(node_id)
        if node is None:
            self._refresh_navigator()
            return
        self.tabs.setCurrentWidget(self.scheme_page)
        self.scene.clearSelection()
        node.setSelected(True)
        self.view.centerOn(node)
        self.view.setFocus()
        self.statusBar().showMessage(
            f"Найдена нода «{node_instance_label(node.model)}».", 4000
        )

    def _show_navigator(self):
        self.navigator_dock.show()
        self.navigator_dock.raise_()
        self.navigator_search.setFocus()
        self.navigator_search.selectAll()
        self._refresh_navigator()

    def _create_console(self):
        dock = QDockWidget("Консоль", self)
        dock.setObjectName("consoleDock")
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(5000)
        self.console.setPlaceholderText(
            "Здесь появится вывод запущенной программы."
        )
        dock.setWidget(self.console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        dock.hide()
        self.console_dock = dock

    def _create_problems(self):
        dock = QDockWidget("Проверка схемы", self)
        dock.setObjectName("problemsDock")
        self.problems = QTreeWidget()
        self.problems.setColumnCount(2)
        self.problems.setHeaderLabels(["Сообщение", "Компонент"])
        self.problems.header().setStretchLastSection(False)
        self.problems.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.problems.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.problems.itemDoubleClicked.connect(self._problem_activated)
        dock.setWidget(self.problems)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        self.problems_dock = dock

    def _create_debugger(self):
        dock = QDockWidget("Отладка", self)
        dock.setObjectName("debuggerDock")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        controls = QHBoxLayout()
        def debug_icon_button(icon, tooltip, handler):
            button = QPushButton()
            button.setIcon(self.style().standardIcon(icon))
            button.setToolTip(tooltip)
            button.setAccessibleName(tooltip)
            button.setFixedSize(32, 28)
            button.clicked.connect(handler)
            return button

        self.debug_run_button = debug_icon_button(
            QStyle.StandardPixmap.SP_MediaPlay,
            "Запустить отладку",
            lambda: self.run_project(debug_mode=True),
        )
        self.debug_start_button = debug_icon_button(
            QStyle.StandardPixmap.SP_DialogApplyButton,
            "Начать поток",
            lambda: self._send_debug_command("debug_start"),
        )
        self.debug_start_button.setEnabled(False)
        self.debug_continue_button = debug_icon_button(
            QStyle.StandardPixmap.SP_ArrowForward,
            "Продолжить выполнение",
            lambda: self._send_debug_command("continue"),
        )
        self.debug_continue_button.setEnabled(False)
        self.debug_step_button = debug_icon_button(
            QStyle.StandardPixmap.SP_MediaSkipForward,
            "Следующий сигнал",
            lambda: self._send_debug_command("flow_ack"),
        )
        self.debug_step_button.setEnabled(False)
        self.debug_stop_button = debug_icon_button(
            QStyle.StandardPixmap.SP_MediaStop,
            "Остановить отладку",
            self.stop_debug_project,
        )
        self.debug_stop_button.setEnabled(False)
        clear = debug_icon_button(
            QStyle.StandardPixmap.SP_DialogResetButton,
            "Очистить панель отладки",
            self._clear_debug_values,
        )
        controls.addWidget(self.debug_run_button)
        controls.addWidget(self.debug_start_button)
        controls.addWidget(self.debug_continue_button)
        controls.addWidget(self.debug_step_button)
        controls.addWidget(self.debug_stop_button)
        controls.addWidget(clear)
        self.debug_animation_checkbox = QCheckBox("Анимация потока")
        self.debug_animation_checkbox.setChecked(True)
        controls.addWidget(self.debug_animation_checkbox)
        controls.addWidget(QLabel("Скорость 0–100:"))
        self.debug_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.debug_speed_slider.setRange(0, 100)
        self.debug_speed_slider.setValue(15)
        self.debug_speed_slider.setFixedWidth(150)
        self.debug_speed_slider.valueChanged.connect(
            self._set_debug_speed
        )
        controls.addWidget(self.debug_speed_slider)
        self.debug_speed_label = QLabel("15%")
        controls.addWidget(self.debug_speed_label)
        controls.addWidget(QLabel("Старт:"))
        self.debug_start_combo = QComboBox()
        self.debug_start_combo.addItem("С начала потока", "all")
        self.debug_start_combo.addItem(
            "С первой точки останова", "breakpoint"
        )
        controls.addWidget(self.debug_start_combo)
        controls.addStretch(1)
        layout.addLayout(controls)
        legend = QLabel(
            "Цвет потока: синий — данные · оранжевый — событие · "
            "жёлтый — запрос · зелёный — ответ · красный — ошибка"
        )
        legend.setStyleSheet("color:#555555; padding:2px;")
        layout.addWidget(legend)
        self.debug_table = QTableWidget(0, 5)
        self.debug_table.setHorizontalHeaderLabels(
            ["Точка", "Значение", "Тип", "Время", "Состояние"]
        )
        self.debug_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.debug_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.debug_table.horizontalHeader().setStretchLastSection(True)
        self.debug_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.debug_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.debug_table)
        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        dock.hide()
        self.debugger_dock = dock
        self._set_debug_speed(self.debug_speed_slider.value())

    def _set_debug_speed(self, value: int):
        value = max(0, min(100, int(value)))
        self.debug_speed_label.setText(f"{value}%")
        if value == 0:
            self.scene.debug_pulse_duration = 0
            self.debug_step_button.setEnabled(self._debug_mode_active)
            return
        # 1% is deliberately very slow; 100% remains readable rather than
        # turning into an instant flash.
        self.scene.debug_pulse_duration = max(
            80, int(3000 - (value - 1) * (2920 / 99))
        )
        self.debug_step_button.setEnabled(False)
        if self._debug_waiting_flow and self._debug_mode_active:
            QTimer.singleShot(
                self.scene.debug_pulse_duration,
                lambda: self._send_debug_command("flow_ack"),
            )

    def stop_debug_project(self):
        self._debug_mode_active = False
        self._debug_waiting_flow = False
        self._debug_animation_armed = True
        self.debug_continue_button.setEnabled(False)
        self.debug_step_button.setEnabled(False)
        self.debug_start_button.setEnabled(False)
        self.debug_run_button.setEnabled(True)
        self.debug_stop_button.setEnabled(False)
        self.scene.clear_debug_animation()
        self.stop_project()
        self._restore_debug_layout()

    def _prepare_debug_layout(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self._debug_original_geometry = self.geometry()
        self._debug_original_maximized = self.isMaximized()
        if self._debug_original_maximized:
            self.showNormal()
        margin = 8
        gap = 8
        builder_width = max(760, int(screen.width() * 0.60))
        preview_x = screen.x() + builder_width + gap
        preview_width = max(
            420,
            screen.width() - builder_width - gap - margin,
        )
        usable_height = max(480, screen.height() - 2 * margin)
        self.setGeometry(
            screen.x() + margin,
            screen.y() + margin,
            builder_width - margin,
            usable_height,
        )
        self._debug_preview_geometry = (
            preview_x,
            screen.y() + margin,
            preview_width,
            usable_height,
        )
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _restore_debug_layout(self):
        if self._debug_original_geometry is None:
            return
        geometry = self._debug_original_geometry
        was_maximized = self._debug_original_maximized
        self._debug_original_geometry = None
        if was_maximized:
            self.showMaximized()
        else:
            self.setGeometry(geometry)

    def _create_actions(self):
        self.new_action = QAction("Новый", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_project)
        self.open_action = QAction("Открыть", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_project)
        self.import_ui_action = QAction("Импортировать Qt Designer .ui…", self)
        self.import_ui_action.setShortcut("Ctrl+Alt+I")
        self.import_ui_action.triggered.connect(self.import_ui_file)
        self.save_action = QAction("Сохранить", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_project)
        self.save_debug_log_action = QAction("Сохранить отладочный лог…", self)
        self.save_debug_log_action.triggered.connect(self.save_debug_log)
        self.generate_action = QAction("Сгенерировать .py", self)
        self.generate_action.setShortcut("F9")
        self.generate_action.triggered.connect(self.generate_file)
        self.run_action = QAction("Запустить", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(
            lambda: self.run_project(debug_mode=False)
        )
        self.debug_run_action = QAction("Запустить отладку", self)
        self.debug_run_action.setShortcut("F6")
        self.debug_run_action.triggered.connect(
            lambda: self.run_project(debug_mode=True)
        )
        self.addAction(self.debug_run_action)
        self.stop_action = QAction("Остановить", self)
        self.stop_action.setShortcut("Shift+F5")
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self.stop_project)
        self.delete_action = QAction("Удалить", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self.delete_selected)
        self.addAction(self.delete_action)
        self.undo_action = QAction("Отменить", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        self.addAction(self.undo_action)
        self.redo_action = QAction("Повторить", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)
        self.addAction(self.redo_action)
        self.copy_action = QAction("Копировать", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.copy_selected)
        self.addAction(self.copy_action)
        self.paste_action = QAction("Вставить", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.paste)
        self.addAction(self.paste_action)
        self.duplicate_action = QAction("Дублировать", self)
        self.duplicate_action.setShortcut("Ctrl+D")
        self.duplicate_action.triggered.connect(self.duplicate_selected)
        self.addAction(self.duplicate_action)
        self.find_node_action = QAction("Найти ноду на схеме…", self)
        self.find_node_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_node_action.triggered.connect(self._show_navigator)
        self.addAction(self.find_node_action)
        self.reset_zoom_action = QAction("Масштаб 100%", self)
        self.reset_zoom_action.setShortcut("Ctrl+0")
        self.reset_zoom_action.triggered.connect(self.reset_zoom)
        self.addAction(self.reset_zoom_action)
        self.validate_action = QAction("Проверить проект", self)
        self.validate_action.setShortcut("F7")
        self.validate_action.triggered.connect(self.validate_project)
        self.addAction(self.validate_action)
        self.fit_action = QAction("Показать всё", self)
        self.fit_action.setShortcut("Home")
        self.fit_action.triggered.connect(self.fit_canvas)
        self.addAction(self.fit_action)
        self.form_settings_action = QAction(
            "Настройки редактора формы…", self
        )
        self.form_settings_action.triggered.connect(
            self.configure_form_grid
        )
        self.wire_curve_action = QAction(
            "Плавные кривые", self, checkable=True
        )
        self.wire_orthogonal_action = QAction(
            "Ломаные под 90°", self, checkable=True
        )
        wire_group = QActionGroup(self)
        wire_group.setExclusive(True)
        wire_group.addAction(self.wire_curve_action)
        wire_group.addAction(self.wire_orthogonal_action)
        self.wire_curve_action.setChecked(
            self.scene.line_style == "curve"
        )
        self.wire_orthogonal_action.setChecked(
            self.scene.line_style == "orthogonal"
        )
        self.wire_curve_action.triggered.connect(
            lambda: self.scene.set_line_style("curve")
        )
        self.wire_orthogonal_action.triggered.connect(
            lambda: self.scene.set_line_style("orthogonal")
        )
        self.auto_route_wires_action = QAction(
            "Автопроложить все нити", self
        )
        self.auto_route_wires_action.triggered.connect(
            self.scene.auto_route_all_connections
        )
        self.smart_layout_action = QAction(
            "Умная расстановка нод и нитей", self
        )
        self.smart_layout_action.setToolTip(
            "Разложить ноды по слоям и уменьшить переплетения нитей"
        )
        self.smart_layout_action.triggered.connect(
            self.scene.smart_layout_and_route
        )
        self.beginner_guide_action = QAction(
            "Как собирать программы из общих нод", self
        )
        self.beginner_guide_action.setShortcut("F1")
        self.beginner_guide_action.triggered.connect(
            lambda: self._show_text_help(
                "Справка для начала работы", BEGINNER_GUIDE
            )
        )
        self.game_guide_action = QAction(
            "Карта динамической игры из общих нод", self
        )
        self.game_guide_action.triggered.connect(
            lambda: self._show_text_help(
                "Динамическая игра без специальной ноды",
                DYNAMIC_GAME_GUIDE,
            )
        )

        style = self.style()
        action_icons = {
            self.new_action: QStyle.StandardPixmap.SP_FileIcon,
            self.open_action: QStyle.StandardPixmap.SP_DialogOpenButton,
            self.save_action: QStyle.StandardPixmap.SP_DialogSaveButton,
            self.generate_action: QStyle.StandardPixmap.SP_DriveHDIcon,
            self.run_action: QStyle.StandardPixmap.SP_MediaPlay,
            self.debug_run_action: QStyle.StandardPixmap.SP_DialogApplyButton,
            self.stop_action: QStyle.StandardPixmap.SP_MediaStop,
            self.delete_action: QStyle.StandardPixmap.SP_TrashIcon,
            self.undo_action: QStyle.StandardPixmap.SP_ArrowBack,
            self.redo_action: QStyle.StandardPixmap.SP_ArrowForward,
            self.validate_action: QStyle.StandardPixmap.SP_DialogApplyButton,
            self.fit_action: QStyle.StandardPixmap.SP_TitleBarMaxButton,
            self.smart_layout_action: QStyle.StandardPixmap.SP_FileDialogDetailedView,
        }
        for action, standard_icon in action_icons.items():
            action.setIcon(style.standardIcon(standard_icon))

    def _create_menus(self):
        self.menuBar().setFixedHeight(22)
        file_menu = self.menuBar().addMenu("Файл")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.import_ui_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_debug_log_action)
        file_menu.addSeparator()
        file_menu.addAction(self.generate_action)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)

        examples_menu = self.menuBar().addMenu("Примеры")
        visual_menu = examples_menu.addMenu("Visual Python Builder")
        self._populate_example_menu(
            visual_menu, APP_ROOT / "examples",
            self.load_visual_example)
        examples_menu.addSeparator()
        examples_menu.addAction("Открыть пример из JSON…").triggered.connect(
            self.open_example_dialog)

        edit_menu = self.menuBar().addMenu("Правка")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.duplicate_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.find_node_action)
        edit_menu.addAction(self.delete_action)

        view_menu = self.menuBar().addMenu("Вид")
        view_menu.addAction(self.palette_dock.toggleViewAction())
        view_menu.addAction(self.properties_dock.toggleViewAction())
        view_menu.addAction(self.navigator_dock.toggleViewAction())
        view_menu.addAction(self.console_dock.toggleViewAction())
        view_menu.addAction(self.problems_dock.toggleViewAction())
        view_menu.addAction(self.debugger_dock.toggleViewAction())
        view_menu.addSeparator()
        view_menu.addAction(self.reset_zoom_action)
        view_menu.addAction(self.fit_action)
        view_menu.addSeparator()
        view_menu.addAction(self.form_settings_action)

        run_menu = self.menuBar().addMenu("Запуск")
        run_menu.addAction(self.validate_action)
        run_menu.addSeparator()
        run_menu.addAction(self.run_action)
        run_menu.addAction(self.stop_action)

        wires_menu = self.menuBar().addMenu("Нити")
        wires_menu.addAction(self.wire_curve_action)
        wires_menu.addAction(self.wire_orthogonal_action)
        wires_menu.addSeparator()
        wires_menu.addAction(self.auto_route_wires_action)
        wires_menu.addAction(self.smart_layout_action)

        help_menu = self.menuBar().addMenu("Справка")
        help_menu.addAction(self.beginner_guide_action)
        help_menu.addAction(self.game_guide_action)

    def _create_toolbar(self):
        toolbar = QToolBar("Основная", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly
        )
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setFixedHeight(28)
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(self.validate_action)
        toolbar.addAction(self.smart_layout_action)
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.stop_action)
        toolbar.addAction(self.generate_action)
        toolbar.setStyleSheet(
            "QToolBar { padding:1px; spacing:1px; }"
            "QToolButton { padding:2px; margin:0; }"
        )
        self.main_toolbar = toolbar
        self.addToolBar(toolbar)

    def _apply_style(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #FFFFFF; color: #2C2C2B; }
            QDockWidget::title { background:#E5E5E5; border-bottom:1px solid #AFAFAF; padding:5px; font-weight:600; }
            QMenuBar { background:#EEEEEE; border-bottom:1px solid #B9B9B9; spacing:1px; }
            QMenuBar::item { padding:2px 7px; }
            QMenuBar::item:selected { background:#DCEAF5; }
            QToolBar { background:#EEEEEE; border-bottom:1px solid #B9B9B9; spacing:2px; padding:2px; }
            QToolButton { padding:5px 8px; border:1px solid transparent; }
            QToolButton:hover { background:#DCEAF5; border:1px solid #7AA7C7; }
            QTreeWidget { border:0; alternate-background-color:#F9F8F7; }
            QTreeWidget::item { min-height:20px; padding-left:2px; }
            QTreeWidget::item:selected { background:#CFE5F5; color:#000000; }
            QHeaderView::section { background:#E5E5E5; border:0; border-right:1px solid #B9B9B9; border-bottom:1px solid #B9B9B9; padding:4px; font-weight:600; }
            QListWidget { border:0; background:#FFFFFF; outline:0; padding:2px; }
            QListWidget::item { padding:2px; }
            QListWidget::item:selected { background:#CFE5F5; color:#000000; }
            QTabWidget::pane { border:1px solid #B9B9B9; }
            QTabBar::tab { background:#E5E5E5; border:1px solid #B9B9B9; padding:3px 9px; margin-right:-1px; }
            QTabBar::tab:selected { background:#FFFFFF; color:#000000; }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { border:1px solid #AFAFAF; padding:2px; background:#FFFFFF; }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border:1px solid #3979A8; }
            QPlainTextEdit { border:0; background:#202020; color:#F4F4F4; font-family:Consolas, monospace; font-size:13px; padding:12px; }
            QStatusBar { border-top:1px solid #E6E5E3; }
            """
        )

    def _set_component_icon(self, type_name: str, reset: bool = False):
        if reset:
            save_icon_assignment(type_name, None)
        else:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Выберите значок компонента", str(CUSTOM_ICONS_DIR),
                "Значки (*.ico *.png *.svg *.jpg *.jpeg *.bmp *.webp)",
            )
            if not filename:
                return
            try:
                save_icon_assignment(type_name, Path(filename))
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, "Значок", str(exc))
                return
        self._refresh_component_icons()
        self.scene.rebuild_nodes(
            next((n.model["id"] for n in self.scene.nodes.values() if n.isSelected()), None)
        )
        self.statusBar().showMessage(
            "Значок сохранён внутри папки программы и не потеряется при переносе.", 5000
        )

    def _refresh_component_icons(self):
        for palette in self.palette_lists:
            for index in range(palette.count()):
                item = palette.item(index)
                type_name = str(item.data(Qt.ItemDataRole.UserRole))
                path = component_icon_path(type_name)
                if path:
                    item.setIcon(QIcon(str(path)))

    def _palette_context_menu(self, palette: PaletteListWidget, position):
        item = palette.itemAt(position)
        if item is None:
            return
        type_name = str(item.data(Qt.ItemDataRole.UserRole))
        menu = QMenu(palette)
        show_help = menu.addAction("Справка об элементе…")
        menu.addSeparator()
        choose = menu.addAction("Выбрать свой значок…")
        reset = menu.addAction("Вернуть стандартный значок")
        reset.setEnabled(type_name in load_icon_assignments())
        selected = menu.exec(palette.mapToGlobal(position))
        if selected == show_help:
            self._show_component_help(type_name)
        elif selected == choose:
            self._set_component_icon(type_name)
        elif selected == reset:
            self._set_component_icon(type_name, reset=True)

    def _palette_double_clicked(self, item: QListWidgetItem):
        type_name = item.data(Qt.ItemDataRole.UserRole)
        if type_name:
            if self.tabs.currentIndex() == 1:
                if self.form_scene.window_item is None:
                    self._refresh_form()
                window = self.form_scene.window_item
                position = (
                    window.scenePos()
                    + QPointF(
                        window.rect().width() / 2,
                        window.rect().height() / 2,
                    )
                    if window
                    else QPointF(100, 100)
                )
                self.add_component_to_form(type_name, position)
                return
            center = self.view.mapToScene(self.view.viewport().rect().center())
            self.add_component(type_name, center)

    def _helper_double_clicked(self, item: QListWidgetItem):
        helper_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not helper_id.startswith("helper:"):
            return
        if self.tabs.currentIndex() != 0:
            self.tabs.setCurrentIndex(0)
        center = self.view.mapToScene(self.view.viewport().rect().center())
        self.scene.add_helper(self._new_helper_model(center, helper_id))
        self._mark_modified()
        self._schedule_history()

    @staticmethod
    def _new_helper_model(
        position: QPointF, helper_id: str = "helper:note"
    ) -> dict[str, Any]:
        kind = "text" if helper_id == "helper:text" else (
            "shape" if helper_id == "helper:shape" else "note"
        )
        is_text = kind == "text"
        return {
            "kind": kind,
            "title": "Текст" if is_text else ("Фигура" if kind == "shape" else "Помощник"),
            "text": "Новый текст" if is_text else "",
            "width": 260 if is_text else 180,
            "height": 90 if is_text else 120,
            "x": round(position.x(), 1),
            "y": round(position.y(), 1),
            "fill_color": "transparent" if is_text else "#DCEAF7",
            "border_color": "transparent" if is_text else "#183B63",
            "text_color": "#303030",
            "font_size": 10,
            "title_font_size": 10,
            "body_font_size": 10,
            "font_bold": False,
            "opacity": 100,
            "fill_alpha": 100,
            "border_alpha": 100,
            "text_alpha": 100,
            "text_x": 8,
            "text_y": 6,
            "shape": "none" if is_text else "rounded",
            "corner_radius": 8,
            "border_width": 2,
            "border_style": "solid",
        }

    def _helper_dropped(self, helper_id: str, position: QPointF):
        if not str(helper_id).startswith("helper:"):
            return
        self.scene.add_helper(self._new_helper_model(position, str(helper_id)))
        self._mark_modified()
        self._schedule_history()

    def _free_graph_position(self, position: QPointF) -> QPointF:
        candidate = QPointF(position)
        occupied = [node.pos() for node in self.scene.nodes.values()]
        for _attempt in range(80):
            if not any(QLineF(candidate, point).length() < 18 for point in occupied):
                return candidate
            candidate += QPointF(24, 24)
        return candidate

    def _free_form_position(self, x: int, y: int) -> tuple[int, int]:
        occupied = []
        for node in self.scene.nodes.values():
            if node.model["type"] == "Form" or not is_visual_type(node.model["type"]):
                continue
            props = node.model.get("properties", {})
            occupied.append((
                int(property_value(props, "x", "Left", default=0) or 0),
                int(property_value(props, "y", "Top", default=0) or 0),
            ))
        candidate_x, candidate_y = x, y
        for _attempt in range(80):
            if not any(
                abs(candidate_x - old_x) < 16 and abs(candidate_y - old_y) < 16
                for old_x, old_y in occupied
            ):
                return candidate_x, candidate_y
            candidate_x += 24
            candidate_y += 24
        return candidate_x, candidate_y

    def add_component(self, type_name: str, position: QPointF):
        position = self._free_graph_position(position)
        spec = COMPONENTS[type_name]
        model = {
            "id": uuid.uuid4().hex[:10],
            "type": type_name,
            "x": round(position.x(), 1),
            "y": round(position.y(), 1),
            "properties": default_properties(type_name),
            "enabled_ports": default_enabled_ports(spec),
        }
        self.scene.clearSelection()
        item = self.scene.add_node(model)
        item.setSelected(True)
        self._refresh_form()

    def add_component_to_form(
        self, type_name: str, scene_position: QPointF
    ):
        if not is_visual_type(type_name):
            QMessageBox.warning(
                self,
                "Невизуальный элемент",
                "Этот элемент не отображается на форме. "
                "Добавьте его на вкладке «Схема».",
            )
            return
        if self.form_scene.window_item is None:
            self._refresh_form()
        window = self.form_scene.window_item
        if window is None:
            return
        container = self.form_scene.container_at(scene_position)
        coordinate_parent: QGraphicsItem = container or window
        local = coordinate_parent.mapFromScene(scene_position)
        x = max(0, int(local.x()))
        y = max(0, int(
            local.y()
            - (FormWindowItem.TITLE_HEIGHT if container is None else 0)
        ))
        x, y = self._free_form_position(x, y)
        props = default_properties(type_name)
        set_property_value(props, x, "x", "Left")
        set_property_value(props, y, "y", "Top")
        graph_center = self.view.mapToScene(
            self.view.viewport().rect().center()
        )
        graph_center = self._free_graph_position(graph_center)
        model = {
            "id": uuid.uuid4().hex[:10],
            "type": type_name,
            "x": round(graph_center.x(), 1),
            "y": round(graph_center.y(), 1),
            "properties": props,
            "enabled_ports": default_enabled_ports(COMPONENTS[type_name]),
        }
        if container is not None:
            model["parent_id"] = container.model["id"]
        item = self.scene.add_node(model)
        self.scene.clearSelection()
        item.setSelected(True)
        self._refresh_form()
        self.form_scene.clearSelection()
        for control in self.form_scene.items():
            if (
                isinstance(control, FormControlItem)
                and control.model["id"] == model["id"]
            ):
                control.setSelected(True)
                break
        self._mark_modified()
        self._schedule_history()

    def _show_properties_for_model(self, model: dict[str, Any]):
        title_bar = self.properties_dock.titleBarWidget()
        if isinstance(title_bar, DockTitleBar) and title_bar.collapsed:
            title_bar.toggle_collapsed()
        self.properties_dock.show()
        self.properties.set_node(model)

    def _edit_dashboard_canvas(self, model: dict[str, Any]):
        props=model.setdefault("properties", {})
        try: data=json.loads(str(props.get("scene","[]")))
        except (TypeError,ValueError): data=[]
        dialog=DashboardDesignerDialog(data,self)
        if dialog.exec()!=QDialog.DialogCode.Accepted: return
        props["scene"]=json.dumps(dialog.data(),ensure_ascii=False,separators=(",",":"))
        self.properties.set_node(model); self._property_changed(); self._refresh_form()
        self.statusBar().showMessage("Canvas обновлён мышиным конструктором.",4000)

    def _edit_custom_instrument(self, model: dict[str, Any]):
        """Beginner-friendly editor for CustomInstrument's JSON design."""
        props = model.setdefault("properties", {})
        try:
            design = json.loads(str(props.get("design", "{}")))
        except (ValueError, TypeError):
            design = {}
        dialog = QDialog(self)
        dialog.setWindowTitle("Конструктор пользовательского прибора")
        dialog.resize(420, 260)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        template = QComboBox()
        template.addItems(["Dial", "Bar", "Ring", "Digital", "Graph"])
        current = str(props.get("template", "Dial"))
        template.setCurrentText(current if current in {"Dial","Bar","Ring","Digital","Graph"} else "Dial")
        ticks = QSpinBox(); ticks.setRange(0, 100); ticks.setValue(int(design.get("ticks", 10)))
        show_value = QCheckBox("Показывать текущее значение"); show_value.setChecked(bool(design.get("show_value", True)))
        primary = QLineEdit(str(props.get("primary_color", "#35C2FF")))
        background = QLineEdit(str(props.get("background_color", "#101820")))
        form.addRow("Шаблон", template); form.addRow("Деления", ticks)
        form.addRow("Основной цвет", primary); form.addRow("Цвет фона", background)
        form.addRow("", show_value); layout.addLayout(form)
        hint = QLabel("Настройки сохраняются в проекте и попадают в сгенерированную программу.")
        hint.setWordWrap(True); layout.addWidget(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        shapes = {"Dial":"dial", "Bar":"bar", "Ring":"ring", "Digital":"digital", "Graph":"graph"}
        props["template"] = template.currentText()
        props["design"] = json.dumps({"shape": shapes[template.currentText()], "show_value": show_value.isChecked(), "ticks": ticks.value()}, ensure_ascii=False)
        props["primary_color"] = primary.text().strip() or "#35C2FF"
        props["background_color"] = background.text().strip() or "#101820"
        self.properties.set_node(model)
        self._property_changed()
        self.statusBar().showMessage("Дизайн пользовательского прибора обновлён.", 4000)

    def _create_empty_container(self,position:QPointF):
        props=default_properties("UserContainer"); props["subgraph"]={"format":1,"name":"Внутренняя схема","nodes":[],"connections":[]}; props["interface"]=[]
        model={"id":uuid.uuid4().hex[:10],"type":"UserContainer","x":round(position.x(),1),"y":round(position.y(),1),"properties":props,"enabled_ports":[]}
        self.scene.clearSelection(); item=self.scene.add_node(model); item.setSelected(True); self._mark_modified(); self._schedule_history()

    def _edit_container_passport(self, model: dict[str, Any]):
        props = model.setdefault("properties", {})
        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Паспорт контейнера — {props.get('name', 'Контейнер')}"
        )
        dialog.resize(820, 620)
        layout = QVBoxLayout(dialog)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        general_page = QWidget()
        general_form = QFormLayout(general_page)
        name_edit = QLineEdit(str(props.get("name", "Мой блок")))
        description_edit = QPlainTextEdit()
        description_edit.setPlainText(str(props.get("description", "")))
        description_edit.setMaximumHeight(130)
        version_edit = QLineEdit(str(props.get("version", "1.0")))
        category_edit = QLineEdit(
            str(props.get("category", "Мои контейнеры"))
        )
        subgroup_edit = QLineEdit(str(props.get("subgroup", "Основные")))
        tags_edit = QLineEdit(str(props.get("tags", "")))
        general_form.addRow("Название", name_edit)
        general_form.addRow("Назначение", description_edit)
        general_form.addRow("Версия", version_edit)
        general_form.addRow("Категория", category_edit)
        general_form.addRow("Подкатегория", subgroup_edit)
        general_form.addRow("Метки", tags_edit)
        tabs.addTab(general_page, "Паспорт")

        interface_page = QWidget()
        interface_layout = QVBoxLayout(interface_page)
        interface_hint = QLabel(
            "Порядок строк определяет порядок точек на сторонах ноды. "
            "Направление существующей точки не меняется: для другого направления "
            "удалите её и создайте новую. Для входов и выходов данных укажите "
            "тип — это улучшит подсказки и защитит от неверных соединений."
        )
        interface_hint.setWordWrap(True)
        interface_layout.addWidget(interface_hint)
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(
            [
                "Название", "Техническое имя", "Направление",
                "Тип данных", "Описание",
            ]
        )
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setAlternatingRowColors(True)

        def set_interface_row(
            row: int,
            caption: str,
            port: str,
            kind: str,
            description: str = "",
            proxy_id: str = "",
            data_type: str = "any",
            data_type_source: str = "",
        ):
            caption_item = QTableWidgetItem(caption)
            caption_item.setData(
                Qt.ItemDataRole.UserRole, proxy_id
            )
            port_item = QTableWidgetItem(port)
            kind_item = QTableWidgetItem(
                INTERFACE_KINDS.get(kind, {}).get("label", kind)
            )
            kind_item.setData(Qt.ItemDataRole.UserRole, kind)
            kind_item.setFlags(
                kind_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            data_type_combo = QComboBox()
            for key, label in INTERFACE_DATA_TYPES.items():
                data_type_combo.addItem(label, key)
            selected_type = (
                data_type if kind in {"data_in", "data_out"} else "any"
            )
            data_type_combo.setCurrentIndex(
                max(0, data_type_combo.findData(selected_type))
            )
            data_type_combo.setEnabled(
                kind in {"data_in", "data_out"}
            )
            source_text = (
                data_type_source.strip()
                if kind in {"data_in", "data_out"}
                else ""
            )
            data_type_combo.setProperty(
                "data_type_source", source_text
            )
            data_type_combo.setToolTip(
                (
                    "Источник типа: " + source_text
                    if source_text else
                    "Источник типа не записан. При изменении тип будет "
                    "помечен как выбранный вручную."
                )
                if kind in {"data_in", "data_out"} else
                "События и действия не переносят значение данных."
            )
            data_type_combo.currentIndexChanged.connect(
                lambda _index, combo=data_type_combo: (
                    combo.setProperty(
                        "data_type_source",
                        "Выбран вручную в паспорте",
                    ),
                    combo.setToolTip(
                        "Источник типа: Выбран вручную в паспорте"
                    ),
                )
            )
            table.setItem(row, 0, caption_item)
            table.setItem(row, 1, port_item)
            table.setItem(row, 2, kind_item)
            table.setCellWidget(row, 3, data_type_combo)
            table.setItem(row, 4, QTableWidgetItem(description))

        def append_interface_row(
            caption: str,
            port: str,
            kind: str,
            description: str = "",
            proxy_id: str = "",
            data_type: str = "any",
            data_type_source: str = "",
        ):
            row = table.rowCount()
            table.insertRow(row)
            set_interface_row(
                row, caption, port, kind, description, proxy_id,
                data_type, data_type_source
            )

        for item in props.get("interface", []):
            if isinstance(item, dict):
                append_interface_row(
                    str(item.get("caption") or item.get("port") or ""),
                    str(item.get("port") or ""),
                    str(item.get("kind") or ""),
                    str(item.get("description") or ""),
                    str(item.get("proxy_id") or ""),
                    str(item.get("data_type") or "any"),
                    str(item.get("data_type_source") or ""),
                )
        interface_layout.addWidget(table, 1)
        controls = QHBoxLayout()
        add_point = QPushButton("Добавить точку…")
        remove_point = QPushButton("Удалить")
        move_up = QPushButton("Выше")
        move_down = QPushButton("Ниже")
        controls.addWidget(add_point)
        controls.addWidget(remove_point)
        controls.addStretch(1)
        controls.addWidget(move_up)
        controls.addWidget(move_down)
        interface_layout.addLayout(controls)
        tabs.addTab(interface_page, "Внешние точки")

        def add_interface_point():
            point_dialog = QDialog(dialog)
            point_dialog.setWindowTitle("Новая внешняя точка")
            point_layout = QVBoxLayout(point_dialog)
            form = QFormLayout()
            caption = QLineEdit("Новая точка")
            kind = QComboBox()
            for key, definition in INTERFACE_KINDS.items():
                kind.addItem(definition["label"], key)
            description = QLineEdit()
            data_type = QComboBox()
            for key, label in INTERFACE_DATA_TYPES.items():
                data_type.addItem(label, key)
            data_type.setEnabled(
                str(kind.currentData()) in {"data_in", "data_out"}
            )
            kind.currentIndexChanged.connect(
                lambda: data_type.setEnabled(
                    str(kind.currentData()) in {"data_in", "data_out"}
                )
            )
            form.addRow("Название", caption)
            form.addRow("Направление", kind)
            form.addRow("Тип данных", data_type)
            form.addRow("Описание", description)
            point_layout.addLayout(form)
            point_buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel
            )
            point_buttons.accepted.connect(point_dialog.accept)
            point_buttons.rejected.connect(point_dialog.reject)
            point_layout.addWidget(point_buttons)
            if point_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            label = caption.text().strip() or "Новая точка"
            technical = re.sub(r"\W+", "_", label).strip("_") or "Port"
            append_interface_row(
                label,
                technical,
                str(kind.currentData()),
                description.text(),
                data_type=str(data_type.currentData()),
                data_type_source="Выбран вручную в паспорте",
            )
            table.selectRow(table.rowCount() - 1)

        def remove_interface_point():
            row = table.currentRow()
            if row >= 0:
                table.removeRow(row)

        def move_interface_row(delta: int):
            row = table.currentRow()
            target = row + delta
            if row < 0 or target < 0 or target >= table.rowCount():
                return
            def row_values(index):
                caption_item = table.item(index, 0)
                port_item = table.item(index, 1)
                kind_item = table.item(index, 2)
                type_combo = table.cellWidget(index, 3)
                description_item = table.item(index, 4)
                return {
                    "caption": caption_item.text() if caption_item else "",
                    "port": port_item.text() if port_item else "",
                    "kind": str(
                        kind_item.data(Qt.ItemDataRole.UserRole)
                        if kind_item else ""
                    ),
                    "description": (
                        description_item.text()
                        if description_item else ""
                    ),
                    "proxy_id": str(
                        caption_item.data(Qt.ItemDataRole.UserRole)
                        if caption_item else ""
                    ),
                    "data_type": str(
                        type_combo.currentData()
                        if isinstance(type_combo, QComboBox) else "any"
                    ),
                    "data_type_source": str(
                        type_combo.property("data_type_source") or ""
                        if isinstance(type_combo, QComboBox) else ""
                    ),
                }

            first = row_values(row)
            second = row_values(target)
            for index, value in ((row, second), (target, first)):
                set_interface_row(index, **value)
            table.selectRow(target)

        add_point.clicked.connect(add_interface_point)
        remove_point.clicked.connect(remove_interface_point)
        move_up.clicked.connect(lambda: move_interface_row(-1))
        move_down.clicked.connect(lambda: move_interface_row(1))

        errors_label = QLabel()
        errors_label.setWordWrap(True)
        errors_label.setStyleSheet(
            "color:#9B1C1C; background:#FFF1F1; "
            "border:1px solid #E3A4A4; padding:5px;"
        )
        errors_label.hide()
        layout.addWidget(errors_label)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)
        buttons.rejected.connect(dialog.reject)

        def accept_passport():
            rows = []
            for row in range(table.rowCount()):
                caption_item = table.item(row, 0)
                port_item = table.item(row, 1)
                kind_item = table.item(row, 2)
                data_type_combo = table.cellWidget(row, 3)
                description_item = table.item(row, 4)
                rows.append(
                    {
                        "caption": caption_item.text() if caption_item else "",
                        "port": port_item.text() if port_item else "",
                        "kind": str(
                            kind_item.data(Qt.ItemDataRole.UserRole)
                            if kind_item else ""
                        ),
                        "description": (
                            description_item.text()
                            if description_item else ""
                        ),
                        "data_type": str(
                            data_type_combo.currentData()
                            if isinstance(data_type_combo, QComboBox)
                            else "any"
                        ),
                        "data_type_source": str(
                            data_type_combo.property("data_type_source") or ""
                            if isinstance(data_type_combo, QComboBox)
                            else ""
                        ),
                        "proxy_id": str(
                            caption_item.data(Qt.ItemDataRole.UserRole)
                            if caption_item else ""
                        ),
                    }
                )
            candidate = copy.deepcopy(model)
            candidate_props = candidate.setdefault("properties", {})
            candidate_props.update(
                {
                    "name": name_edit.text().strip() or "Мой блок",
                    "description": description_edit.toPlainText().strip(),
                    "version": version_edit.text().strip() or "1.0",
                    "category": (
                        category_edit.text().strip() or "Мои контейнеры"
                    ),
                    "subgroup": subgroup_edit.text().strip() or "Основные",
                    "tags": tags_edit.text().strip(),
                }
            )
            try:
                rename_map = apply_container_interface(candidate, rows)
            except ValueError as exc:
                errors_label.setText(str(exc))
                errors_label.show()
                return
            errors = validate_container_model(candidate)
            if errors:
                errors_label.setText("\n".join("• " + error for error in errors))
                errors_label.show()
                return
            old_proxies = {
                str(item.get("proxy_id"))
                for item in props.get("interface", [])
                if isinstance(item, dict)
            }
            new_proxies = {
                str(item.get("proxy_id"))
                for item in candidate_props.get("interface", [])
                if isinstance(item, dict)
            }
            if old_proxies - new_proxies:
                answer = QMessageBox.question(
                    dialog,
                    "Удаление внешних точек",
                    "Удаляемые точки и связанные с ними внутренние и внешние "
                    "нити будут удалены. Продолжить?",
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
            model.clear()
            model.update(candidate)
            container_id = str(model.get("id"))
            removed_ports = {
                str(item.get("port"))
                for item in props.get("interface", [])
                if isinstance(item, dict)
                and str(item.get("proxy_id")) not in new_proxies
            }
            for connection in list(self.scene.connections):
                data = connection.model
                if (
                    str(data.get("to_node")) == container_id
                    and str(data.get("to_port")) in rename_map
                ):
                    data["to_port"] = rename_map[str(data["to_port"])]
                if (
                    str(data.get("from_node")) == container_id
                    and str(data.get("from_port")) in rename_map
                ):
                    data["from_port"] = rename_map[str(data["from_port"])]
                if (
                    str(data.get("to_node")) == container_id
                    and str(data.get("to_port")) in removed_ports
                ) or (
                    str(data.get("from_node")) == container_id
                    and str(data.get("from_port")) in removed_ports
                ):
                    self.scene.remove_connection(connection)
            dialog.accept()

        buttons.accepted.connect(accept_passport)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        project = self.scene.to_project(self.project_name)
        self.scene.load_project(project)
        self._refresh_form()
        self._mark_modified()
        self._schedule_history()
        self.statusBar().showMessage(
            "Паспорт и внешний интерфейс контейнера обновлены.", 5000
        )

    def _pack_selected_container(self):
        ids={i.model["id"] for i in self.scene.selectedItems() if isinstance(i,NodeItem)}
        if not ids:return
        project,cid=pack_project(self.scene.to_project(self.project_name),ids); self.scene.load_project(project); self.scene.nodes[cid].setSelected(True)
        self._refresh_form(); self._mark_modified(); self._schedule_history(); self.statusBar().showMessage(f"Создан контейнер из {len(ids)} нод",5000)

    def _open_user_container(self,model:dict[str,Any]):
        props=model.setdefault("properties",{}); inner=copy.deepcopy(props.get("subgraph",{}))
        if not isinstance(inner,dict):inner={"format":1,"nodes":[],"connections":[]}
        self._container_stack.append((copy.deepcopy(self.scene.to_project(self.project_name)),str(model["id"]),str(props.get("name","Контейнер"))))
        self.scene.in_container=True; self.scene.load_project(inner); self._refresh_form(); self.properties.set_node(None)
        self.statusBar().showMessage(
            "Внутри контейнера · протяните нить к рамке, чтобы создать "
            "внешнюю точку · ПКМ по фону для возврата",
            8000,
        )

    def _return_from_container(self):
        if not self._container_stack:return
        inner=self.scene.to_project("Внутренняя схема"); parent,cid,title=self._container_stack.pop()
        node=next((n for n in parent.get("nodes",[]) if n.get("id")==cid),None)
        previous_interface=(
            node.get("properties",{}).get("interface",[])
            if node else []
        )
        interface=build_interface(inner, previous_interface)
        if node: node.setdefault("properties",{})["subgraph"]=inner; node["properties"]["interface"]=interface; node["enabled_ports"]=[i["port"] for i in interface]
        self.scene.in_container=bool(self._container_stack); self.scene.load_project(parent); self._refresh_form(); self._mark_modified(); self._schedule_history()
        if cid in self.scene.nodes:self.scene.nodes[cid].setSelected(True)
        self.statusBar().showMessage(f"Контейнер «{title}» сохранён · внешних точек: {len(interface)}",5000)

    def _unpack_user_container(self,model:dict[str,Any]):
        self.scene.load_project(expand_user_containers(self.scene.to_project(self.project_name))); self._refresh_form(); self._mark_modified(); self._schedule_history()

    def _commit_all_containers(self):
        while self._container_stack:self._return_from_container()

    def _graph_node_action(self, node_id: str, action: str):
        node = self.scene.nodes.get(node_id)
        if node is None:
            return
        if not node.isSelected():
            self.scene.clearSelection()
            node.setSelected(True)

        if action == "properties":
            self._show_properties_for_model(node.model)
        elif action == "help":
            self._show_component_help(node.spec.type_name)
        elif action == "instrument_designer":
            self._edit_custom_instrument(node.model)
        elif action == "canvas_designer": self._edit_dashboard_canvas(node.model)
        elif action == "open_container": self._open_user_container(node.model)
        elif action == "container_passport":
            self._edit_container_passport(node.model)
        elif action == "unpack_container": self._unpack_user_container(node.model)
        elif action == "save_container":
            self._save_selected_container_to_library(node.model)
        elif action == "pack_container": self._pack_selected_container()
        elif action == "choose_icon":
            self._set_component_icon(node.spec.type_name)
        elif action == "reset_icon":
            self._set_component_icon(node.spec.type_name, reset=True)
        elif action == "select_wires":
            self.scene.clearSelection()
            node.setSelected(True)
            for connection in self.scene.connections:
                if (
                    connection.source.node_item is node
                    or connection.target.node_item is node
                ):
                    connection.setSelected(True)
        elif action == "copy":
            self.copy_selected()
        elif action == "duplicate":
            self.duplicate_selected()
        elif action == "delete":
            self.delete_selected()
        elif action.startswith("port:"):
            _prefix, port_name, state = action.split(":", 2)
            self._port_toggle_requested(
                node.model, port_name, state == "on"
            )

    def _show_text_help(self, title: str, text: str):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(760, 640)
        layout = QVBoxLayout(dialog)
        viewer = QPlainTextEdit(dialog)
        viewer.setReadOnly(True)
        viewer.setPlainText(text)
        viewer.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        viewer.setStyleSheet(
            "QPlainTextEdit { background:#FFFFFF; color:#202020;"
            " border:1px solid #B9B9B9; font-family:'Segoe UI';"
            " font-size:13px; padding:10px; }"
        )
        layout.addWidget(viewer)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _show_component_help(self, type_name: str):
        spec = COMPONENTS.get(type_name)
        if spec is None:
            QMessageBox.warning(
                self, "Справка", f"Неизвестный тип элемента: {type_name}"
            )
            return
        self._show_text_help(
            f"Справка: {spec.caption}",
            format_component_help(type_name),
        )

    def _graph_canvas_action(self, action: str, position: QPointF):
        if action == "paste":
            self.paste()
        elif action == "select_all":
            self.scene.clearSelection()
            for node in self.scene.nodes.values():
                node.setSelected(True)
        elif action == "clear_selection":
            self.scene.clearSelection()
        elif action == "fit":
            self.tabs.setCurrentWidget(self.scheme_page)
            self.fit_canvas()
        elif action == "reset_zoom":
            self.tabs.setCurrentWidget(self.scheme_page)
            self.reset_zoom()
        elif action == "toggle_snap":
            self.scene.snap_enabled = not self.scene.snap_enabled
            state = "включена" if self.scene.snap_enabled else "выключена"
            self.statusBar().showMessage(f"Привязка к сетке {state}.", 3000)
        elif action == "auto_route_all":
            self.scene.auto_route_all_connections()
        elif action == "smart_layout":
            self.scene.smart_layout_and_route()
        elif action == "orthogonal":
            self.scene.set_line_style("orthogonal")
        elif action == "curve":
            self.scene.set_line_style("curve")
        elif action == "create_container": self._create_empty_container(position)
        elif action == "pack_container": self._pack_selected_container()
        elif action == "return_container": self._return_from_container()
        elif action == "validate": self.validate_project()

    def _form_node_action(self, node_id: str, action: str):
        control = next(
            (
                item
                for item in self.form_scene.items()
                if isinstance(item, FormControlItem)
                and item.model["id"] == node_id
            ),
            None,
        )
        node = self.scene.nodes.get(node_id)
        if control is None or node is None:
            return
        self.form_scene.clearSelection()
        control.setSelected(True)
        if action == "canvas_designer":
            self._edit_dashboard_canvas(node.model)
        elif action == "delete":
            self.scene.clearSelection()
            node.setSelected(True)
            self.scene.delete_selected()
            self._refresh_form()
        elif action == "duplicate":
            duplicate_model = copy.deepcopy(node.model)
            duplicate_model["id"] = uuid.uuid4().hex[:10]
            duplicate_model["x"] = float(
                duplicate_model.get("x", 0)
            ) + 30
            duplicate_model["y"] = float(
                duplicate_model.get("y", 0)
            ) + 30
            duplicate_props = duplicate_model.setdefault(
                "properties", {}
            )
            left = int(
                property_value(
                    duplicate_props, "x", "Left", default=0
                )
            )
            top = int(
                property_value(
                    duplicate_props, "y", "Top", default=0
                )
            )
            set_property_value(
                duplicate_props, left + 10, "x", "Left"
            )
            set_property_value(
                duplicate_props, top + 10, "y", "Top"
            )
            created = self.scene.add_node(duplicate_model)
            self.scene.clearSelection()
            created.setSelected(True)
            self._refresh_form()
            self._mark_modified()
            self._schedule_history()
        elif action in {"front", "back"}:
            z_values = [
                float(item.model.get("z", 2))
                for item in self.form_scene.items()
                if isinstance(item, FormControlItem)
            ] or [2]
            z_value = (
                max(z_values) + 1
                if action == "front"
                else min(z_values) - 1
            )
            control.model["z"] = z_value
            control.setZValue(z_value)
            self._mark_modified()
            self._schedule_history()
        elif action == "properties":
            title_bar = self.properties_dock.titleBarWidget()
            if (
                isinstance(title_bar, DockTitleBar)
                and title_bar.collapsed
            ):
                title_bar.toggle_collapsed()
            self.properties_dock.show()
            self.properties.set_node(control.model)

    def _form_scene_action(self, action: str):
        if action == "grid_settings":
            self.configure_form_grid()
        elif action == "fit":
            self.tabs.setCurrentWidget(self.form_view)
            self.fit_canvas()
        elif action == "reset_zoom":
            self.tabs.setCurrentWidget(self.form_view)
            self.reset_zoom()

    def configure_form_grid(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки редактора формы")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        show_grid = QCheckBox()
        show_grid.setChecked(self.form_scene.show_grid)
        snap = QCheckBox()
        snap.setChecked(self.form_scene.snap_enabled)
        step = QSpinBox()
        step.setRange(2, 100)
        step.setSuffix(" px")
        step.setValue(self.form_scene.snap_size)
        form.addRow("Показывать сетку", show_grid)
        form.addRow("Привязка к сетке", snap)
        form.addRow("Шаг сетки", step)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.form_scene.show_grid = show_grid.isChecked()
            self.form_scene.snap_enabled = snap.isChecked()
            self.form_scene.snap_size = step.value()
            self.form_scene.update()
            self.statusBar().showMessage(
                f"Сетка формы: {step.value()} px · "
                f"привязка {'включена' if snap.isChecked() else 'выключена'}",
                4000,
            )

    def delete_selected(self):
        if self.tabs.currentIndex() == 1:
            selected = [
                item
                for item in self.form_scene.selectedItems()
                if isinstance(item, FormControlItem)
            ]
            if not selected:
                return
            node_id = selected[0].model["id"]
            node = self.scene.nodes.get(node_id)
            if node:
                self.scene.clearSelection()
                node.setSelected(True)
                self.scene.delete_selected()
                self._refresh_form()
            return
        self.scene.delete_selected()
        self._refresh_form()

    def _selected_node_ids(self) -> list[str]:
        if self.tabs.currentIndex() == 1:
            return [
                item.model["id"]
                for item in self.form_scene.selectedItems()
                if isinstance(item, FormControlItem)
            ]
        return [
            item.model["id"]
            for item in self.scene.selectedItems()
            if isinstance(item, NodeItem)
        ]

    def copy_selected(self):
        selected_ids = set(self._selected_node_ids())
        nodes = [
            copy.deepcopy(item.model)
            for item in self.scene.nodes.values()
            if item.model["id"] in selected_ids
            and item.model["type"] != "Form"
        ]
        if not nodes:
            return
        ids = {node["id"] for node in nodes}
        self._clipboard = {
            "nodes": nodes,
            "connections": [
                copy.deepcopy(item.model)
                for item in self.scene.connections
                if item.model["from_node"] in ids
                and item.model["to_node"] in ids
            ],
        }
        self.statusBar().showMessage(
            f"Скопировано элементов: {len(nodes)}", 3000
        )

    def paste(self):
        if not self._clipboard:
            return
        source = copy.deepcopy(self._clipboard)
        id_map = {
            node["id"]: uuid.uuid4().hex[:10]
            for node in source["nodes"]
        }
        self.scene.clearSelection()
        new_nodes = []
        for node in source["nodes"]:
            old_id = node["id"]
            node["id"] = id_map[old_id]
            node["x"] = float(node.get("x", 0)) + 30
            node["y"] = float(node.get("y", 0)) + 30
            if node["type"] in FormScene.VISUAL_TYPES:
                props = node.setdefault("properties", {})
                props["x"] = int(props.get("x", 0)) + 10
                props["y"] = int(props.get("y", 0)) + 10
            new_nodes.append(node)
            item = self.scene.add_node(node)
            item.setSelected(True)
        new_connections = []
        for connection in source["connections"]:
            connection["from_node"] = id_map[connection["from_node"]]
            connection["to_node"] = id_map[connection["to_node"]]
            new_connections.append(connection)
            self.scene.add_connection(connection)
        self._clipboard = {
            "nodes": copy.deepcopy(new_nodes),
            "connections": copy.deepcopy(new_connections),
        }
        self._refresh_form()
        self._scene_changed()

    def duplicate_selected(self):
        self.copy_selected()
        self.paste()

    def _scene_changed(self):
        self._mark_modified()
        self._schedule_history()
        self._schedule_navigator_refresh()

    def _schedule_history(self):
        if not self._restoring_history:
            self._history_timer.start()

    def _project_snapshot(self) -> dict[str, Any]:
        return copy.deepcopy(self.scene.to_project(self.project_name))

    def _reset_history(self):
        self._history_timer.stop()
        self._history = [self._project_snapshot()]
        self._history_index = 0
        self._update_history_actions()

    def _push_history(self):
        if self._restoring_history:
            return
        snapshot = self._project_snapshot()
        if (
            self._history_index >= 0
            and snapshot == self._history[self._history_index]
        ):
            return
        del self._history[self._history_index + 1 :]
        self._history.append(snapshot)
        if len(self._history) > 100:
            self._history.pop(0)
        else:
            self._history_index += 1
        self._update_history_actions()

    def _update_history_actions(self):
        if hasattr(self, "undo_action"):
            self.undo_action.setEnabled(self._history_index > 0)
            self.redo_action.setEnabled(
                0 <= self._history_index < len(self._history) - 1
            )

    def undo(self):
        if self._history_index > 0:
            self._history_index -= 1
            self._restore_history_snapshot()

    def redo(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_history_snapshot()

    def _restore_history_snapshot(self):
        self._history_timer.stop()
        self._restoring_history = True
        snapshot = copy.deepcopy(self._history[self._history_index])
        self.scene.load_project(snapshot)
        self.project_name = snapshot.get("name", self.project_name)
        self._refresh_form()
        self._refresh_code()
        self.properties.set_node(None)
        self._restoring_history = False
        self.modified = True
        self._update_title()
        self._update_history_actions()

    def _property_changed(self):
        model = self.properties.model
        if model is not None and COMPONENTS[model["type"]].hiasm_sub:
            node_id = model["id"]
            self.scene.rebuild_nodes(node_id)
            model = self.scene.nodes[node_id].model
            QTimer.singleShot(
                0, lambda current=model: self.properties.set_node(current)
            )
        self._mark_modified()
        self._schedule_history()
        self._refresh_form()
        self._schedule_navigator_refresh()
        if self.tabs.currentIndex() == 2:
            self._refresh_code()

    def _port_toggle_requested(
        self, model: dict[str, Any], port_name: str, enable: bool
    ):
        spec = COMPONENTS[model["type"]]
        instance_ports = effective_ports(
            model["type"], model.get("properties", {})
        )
        port_spec = next(
            (port for port in instance_ports if port.name == port_name), None
        )
        if port_spec is None:
            return
        if port_spec.required and not enable:
            QTimer.singleShot(
                0, lambda current=model: self.properties.set_node(current)
            )
            self.statusBar().showMessage(
                f"Точка «{port_spec.caption}» обязательна.", 5000
            )
            return

        related = [
            connection
            for connection in self.scene.connections
            if (
                connection.model["from_node"] == model["id"]
                and connection.model["from_port"] == port_name
            )
            or (
                connection.model["to_node"] == model["id"]
                and connection.model["to_port"] == port_name
            )
        ]
        if not enable and related:
            answer = QMessageBox.question(
                self,
                "Отключение точки",
                f"С точкой «{port_spec.caption}» связано линий: {len(related)}.\n"
                "Удалить эти связи и отключить точку?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                QTimer.singleShot(
                    0, lambda current=model: self.properties.set_node(current)
                )
                return
            for connection in related:
                self.scene.removeItem(connection)
                self.scene.connections.remove(connection)

        enabled_ports = model.setdefault(
            "enabled_ports", default_enabled_ports(spec, instance_ports)
        )
        if enable and port_name not in enabled_ports:
            enabled_ports.append(port_name)
        elif not enable and port_name in enabled_ports:
            enabled_ports.remove(port_name)

        node_id = model["id"]
        QTimer.singleShot(
            0, lambda selected_id=node_id: self._apply_port_rebuild(selected_id)
        )

    def _apply_port_rebuild(self, node_id: str):
        self.scene.rebuild_nodes(node_id)
        self._mark_modified()
        self._schedule_history()
        self.statusBar().showMessage("Состав точек обновлён.", 3000)

    def _form_model_changed(self):
        self._mark_modified()
        self._schedule_history()
        if self.tabs.currentIndex() == 2:
            self._refresh_code()

    def _tab_changed(self, index: int):
        if index == 1:
            self._refresh_form()
        elif index == 2:
            self._refresh_code()

    def _active_canvas(self) -> CanvasView | None:
        if self.tabs.currentIndex() == 0:
            return self.view
        if self.tabs.currentIndex() == 1:
            return self.form_view
        return None

    def _show_zoom(self, percent: int):
        self.statusBar().showMessage(
            f"Масштаб: {percent}% · колесико меняет масштаб · ЛКМ по фону перемещает полотно",
            2500,
        )

    def reset_zoom(self):
        canvas = self._active_canvas()
        if canvas is None:
            return
        canvas.resetTransform()
        self._show_zoom(100)

    def fit_canvas(self):
        canvas = self._active_canvas()
        if canvas is None:
            return
        rect = canvas.scene().itemsBoundingRect()
        if not rect.isEmpty():
            canvas.fitInView(
                rect.adjusted(-40, -40, 40, 40),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            self._show_zoom(round(canvas.transform().m11() * 100))

    def _refresh_form(self):
        self.form_scene.rebuild(self.scene)

    def _refresh_code(self):
        project = self.scene.to_project(self.project_name)
        try:
            self.code_preview.setPlainText(generate_python(project))
        except Exception as exc:
            self.code_preview.setPlainText(f"# Ошибка генерации:\n# {exc}")

    def _mark_modified(self):
        self.modified = True
        self._update_title()

    def _update_title(self):
        marker = " •" if self.modified else ""
        self.setWindowTitle(f"{self.project_name}{marker} — {APP_NAME} {APP_VERSION}")

    def _show_demo_at_working_zoom(self):
        self.view.resetTransform()
        rect=self.scene.itemsBoundingRect()
        if not rect.isEmpty():
            self.view.centerOn(rect.left()+self.view.viewport().width()/2, rect.top()+self.view.viewport().height()/2)
        self._show_zoom(100)

    def _new_demo(self):
        demo_path = APP_ROOT / "examples" / "14_Лаборатория_сигналов_отладка.json"
        if demo_path.exists():
            project = json.loads(demo_path.read_text(encoding="utf-8"))
            self.project_name = project.get("name", "Демонстрация")
            self._reset_container_navigation()
            self.scene.load_project(project)
            self.properties.set_node(None)
            self.modified = False
            self._update_title()
            self._refresh_form()
            self._refresh_code()
            self._reset_history()
            self.tabs.setCurrentIndex(0)
            QTimer.singleShot(0, self._show_demo_at_working_zoom)
            self.statusBar().showMessage(
                "Открыт контрольный пример 14.0. Нажмите F5: сообщения [OK] "
                "теперь появляются в консоли немедленно.",
                12000,
            )

    def new_project(self):
        if not self._confirm_discard():
            return
        self._reset_container_navigation()
        self.scene.load_project({"nodes": [], "connections": []})
        self.properties.set_node(None)
        self.project_path = None
        self.project_name = "Новый проект"
        self.modified = False
        self._update_title()
        self.add_component("Form", QPointF(-100, -100))
        self.modified = False
        self._update_title()
        self._refresh_form()
        self._refresh_code()
        self._reset_history()

    def _populate_example_menu(self, menu, directory: Path, callback):
        """Строит подменю из JSON-файлов, включая вложенные папки."""
        directory = Path(directory)
        if not directory.exists():
            empty = menu.addAction("Примеры не найдены")
            empty.setEnabled(False)
            return
        submenus = {(): menu}
        files = sorted(directory.rglob("*.json"), key=lambda value: value.as_posix().lower())
        for path in files:
            relative = path.relative_to(directory)
            parent_key = ()
            target = menu
            for part in relative.parts[:-1]:
                parent_key = (*parent_key, part)
                if parent_key not in submenus:
                    submenus[parent_key] = target.addMenu(part.replace("_", " "))
                target = submenus[parent_key]
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                label = str(data.get("name") or data.get("meta", {}).get("name") or path.stem)
            except Exception:
                label = path.stem
            action = target.addAction(label.replace("_", " "))
            action.setToolTip(str(relative))
            action.triggered.connect(
                lambda checked=False, value=path, handler=callback: handler(value))
        if not files:
            empty = menu.addAction("Примеры не найдены")
            empty.setEnabled(False)

    @staticmethod
    def _project_kind(project: dict[str, Any]) -> str:
        nodes = project.get("nodes")
        if not isinstance(nodes, list):
            return "unknown"
        if "edges" in project or any(isinstance(node, dict) and "spec_key" in node for node in nodes):
            return "nodeflow"
        if "connections" in project or any(isinstance(node, dict) and "type" in node for node in nodes):
            return "visual"
        return "unknown"

    def _load_visual_project_path(self, path: Path, as_example=False):
        if not self._confirm_discard():
            return False
        try:
            project = json.loads(Path(path).read_text(encoding="utf-8"))
            if self._project_kind(project) != "visual":
                raise ValueError(
                    "Файл не является проектом Visual Python Builder.")
            structure_errors = self._validate_project_structure(project)
            if structure_errors:
                raise ValueError("\n".join(structure_errors))
            self._reset_container_navigation()
            self.scene.load_project(project)
            self.properties.set_node(None)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть проект:\n{exc}")
            return False
        self.project_path = None if as_example else Path(path)
        base_name = project.get("name", Path(path).stem)
        self.project_name = f"Пример — {base_name}" if as_example else base_name
        self.modified = False
        self._update_title(); self._refresh_form(); self._refresh_code(); self._reset_history()
        self.tabs.setCurrentIndex(0)
        QTimer.singleShot(0, self.fit_canvas)
        if as_example:
            self.statusBar().showMessage(
                f"Пример загружен: {Path(path).name}. F5 — запуск; Ctrl+S — сохранить копию.", 10000)
        return True

    def load_visual_example(self, path):
        return self._load_visual_project_path(Path(path), as_example=True)

    def import_ui_file(self):
        """Import a Qt Designer file into the current Builder project."""
        if not self._confirm_discard():
            return False
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Импортировать Qt Designer .ui",
            "",
            "Qt Designer UI (*.ui)",
        )
        if not filename:
            return False
        try:
            project, report = import_ui_to_project(filename)
            structure_errors = self._validate_project_structure(project)
            if structure_errors:
                raise ValueError("\n".join(structure_errors))
            self._reset_container_navigation()
            self.scene.load_project(project)
            self.properties.set_node(None)
        except Exception as exc:
            QMessageBox.critical(
                self, "Ошибка импорта .ui",
                f"Не удалось импортировать файл:\n{exc}",
            )
            return False

        self.project_path = None
        self.project_name = project.get("name") or Path(filename).stem
        self.modified = True
        self._update_title()
        self._refresh_form()
        self._refresh_code()
        self._reset_history()
        self.tabs.setCurrentIndex(0)
        self.fit_canvas()

        counts = report_counts(report)
        created = counts.get("created_node", 0)
        connections = counts.get("created_connection", 0)
        warnings = sum(
            value for key, value in counts.items()
            if key.endswith("warning")
            or key in {"unsupported_widget", "unsupported_menu", "layout_info",
                       "data_warning", "skipped_widget", "missing_component"}
        )
        details = [
            f"Создано компонентов: {created}",
            f"Создано связей: {connections}",
        ]
        if warnings:
            details.append(f"Предупреждений: {warnings}")
        self.problems.clear()
        for item in report:
            kind = str(item.get("class", "info"))
            if kind in {"created_node", "created_connection", "layout_info"}:
                continue
            label = "Предупреждение" if kind.endswith("warning") or kind in {
                "unsupported_widget", "unsupported_menu", "data_warning",
                "missing_component",
            } else "Информация"
            self.problems.addTopLevelItem(
                QTreeWidgetItem([f"{label}: {item.get('name', '')}", "Импорт .ui"])
            )
        if warnings or len(report) > created + connections:
            self.problems_dock.show()
        self.statusBar().showMessage(
            f"Импорт завершён · {created} компонентов · {connections} связей",
            8000,
        )
        return True

    def open_example_dialog(self):
        root = APP_ROOT
        filename, _ = QFileDialog.getOpenFileName(
            self, "Открыть пример", str(root / "examples"), "Примеры JSON (*.json)")
        if not filename:
            return
        try:
            project = json.loads(Path(filename).read_text(encoding="utf-8"))
            kind = self._project_kind(project)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать JSON:\n{exc}")
            return
        if kind == "visual":
            self.load_visual_example(Path(filename))
        else:
            QMessageBox.warning(
                self, "Неизвестный формат",
                "Файл не похож на проект Visual Python Builder.",
            )

    def open_project(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Открыть проект", "", "Проекты Visual Python (*.vpy.json);;JSON (*.json)")
        if not filename:
            return
        self._load_visual_project_path(Path(filename), as_example=False)

    def save_project(self):
        self._commit_all_containers()
        if self.project_path is None:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить проект",
                f"{self.project_name}.vpy.json",
                "Проекты Visual Python (*.vpy.json)",
            )
            if not filename:
                return False
            self.project_path = Path(filename)
            self.project_name = self.project_path.name.removesuffix(".vpy.json")
        project = self.scene.to_project(self.project_name)
        try:
            self._write_text_atomic(
                self.project_path,
                json.dumps(project, ensure_ascii=False, indent=2),
            )
        except Exception as exc:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось сохранить проект:\n{exc}"
            )
            return False
        self.modified = False
        self._update_title()
        self.statusBar().showMessage(f"Сохранено: {self.project_path}", 4000)
        return True

    def generate_file(self):
        self._commit_all_containers()
        project = self.scene.to_project(self.project_name)
        errors = self.validate_project(show_success=False)
        if errors:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Создать Python-файл", f"{self.project_name}.py", "Python (*.py)"
        )
        if not filename:
            return
        try:
            code = generate_python(project)
            compile(code, filename, "exec")
            self._write_text_atomic(Path(filename), code)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать файл:\n{exc}")
            return
        self.statusBar().showMessage(f"Создано: {filename}", 5000)
        QMessageBox.information(
            self,
            "Готово",
            f"Python-файл создан:\n{filename}\n\nЗапуск: python \"{filename}\"",
        )

    def run_project(self, debug_mode: bool = False):
        self._commit_all_containers()
        if self.preview_process.state() != QProcess.ProcessState.NotRunning:
            self.stop_project()
        project = self.scene.to_project(self.project_name)
        errors = self.validate_project(show_success=False)
        if errors:
            return
        try:
            self._debug_mode_active = bool(debug_mode)
            self._debug_waiting_flow = False
            self._debug_animation_armed = (
                self.debug_start_combo.currentData() == "all"
            )
            if self._debug_mode_active:
                self._prepare_debug_layout()
            code = generate_python(project)
            compile(code, "<предпросмотр>", "exec")
            preview_path = (
                Path(tempfile.gettempdir()) / "visual_python_builder_preview.py"
            )
            self._write_text_atomic(preview_path, code)
            self._preview_source = code
            self._preview_path = preview_path
            self._runtime_stdout = ""
            self._runtime_stderr = ""
            self._runtime_stdout_buffer = ""
            self._debug_log_path = None
            self._clear_debug_values()
            self.debug_continue_button.setEnabled(False)
            self.debug_step_button.setEnabled(
                self._debug_mode_active
                and self.debug_speed_slider.value() == 0
            )
            self.debug_stop_button.setEnabled(self._debug_mode_active)
            self.problems.clear()
            self.console.clear()
            self.console.appendPlainText(
                f"> {sys.executable} -u {preview_path}\n"
            )
            self.console_dock.show()
            self.preview_process.setProgram(sys.executable)
            self.preview_process.setArguments(["-u", str(preview_path)])
            environment = QProcessEnvironment.systemEnvironment()
            environment.insert("PYTHONUTF8", "1")
            environment.insert("PYTHONUNBUFFERED", "1")
            environment.insert("PYTHONIOENCODING", "utf-8")
            environment.insert(
                "VPB_DEBUG_MODE", "1" if self._debug_mode_active else "0"
            )
            environment.insert(
                "VPB_DEBUG_WAIT_START",
                "1" if self._debug_mode_active else "0",
            )
            if self._debug_mode_active and self._debug_preview_geometry:
                environment.insert(
                    "VPB_DEBUG_GEOMETRY",
                    ",".join(str(value) for value in self._debug_preview_geometry),
                )
            app_dir = str(APP_ROOT)
            old_pythonpath = environment.value("PYTHONPATH")
            environment.insert(
                "PYTHONPATH",
                os.pathsep.join(
                    part for part in (app_dir, str(preview_path.parent), old_pythonpath)
                    if part
                ),
            )
            self.preview_process.setProcessEnvironment(environment)
            self.preview_process.setWorkingDirectory(
                str(self.project_path.parent if self.project_path is not None else APP_ROOT)
            )
            self.preview_process.start()
            self.run_action.setEnabled(False)
            self.debug_run_action.setEnabled(False)
            self.debug_run_button.setEnabled(False)
            self.stop_action.setEnabled(True)
            self.debug_start_button.setEnabled(self._debug_mode_active)
            if self._debug_mode_active:
                self.debugger_dock.show()
            self.statusBar().showMessage(
                (
                    f"Отладка запущена: {preview_path}"
                    if self._debug_mode_active
                    else f"Проект запущен: {preview_path}"
                ),
                5000,
            )
        except Exception as exc:
            self._debug_mode_active = False
            self.debug_run_button.setEnabled(True)
            self.debug_start_button.setEnabled(False)
            self.debug_stop_button.setEnabled(False)
            self._restore_debug_layout()
            QMessageBox.critical(
                self, "Ошибка запуска", f"Не удалось запустить проект:\n{exc}"
            )

    def stop_project(self):
        if self.preview_process.state() == QProcess.ProcessState.NotRunning:
            return
        self.preview_process.terminate()
        QTimer.singleShot(
            1500,
            lambda: (
                self.preview_process.kill()
                if self.preview_process.state()
                != QProcess.ProcessState.NotRunning
                else None
            ),
        )

    def _read_process_output(self):
        text = bytes(
            self.preview_process.readAllStandardOutput()
        ).decode("utf-8", errors="replace")
        if text:
            self._runtime_stdout += text
            self._runtime_stdout_buffer += text
            complete = self._runtime_stdout_buffer.splitlines(keepends=True)
            self._runtime_stdout_buffer = ""
            if complete and not complete[-1].endswith(("\n", "\r")):
                self._runtime_stdout_buffer = complete.pop()
            visible = []
            for line in complete:
                if line.startswith(DEBUG_STREAM_PREFIX):
                    self._handle_debug_message(line[len(DEBUG_STREAM_PREFIX):].strip())
                else:
                    visible.append(line)
            if visible:
                self.console.moveCursor(QTextCursor.MoveOperation.End)
                self.console.insertPlainText("".join(visible))

    def _read_process_error(self):
        text = bytes(
            self.preview_process.readAllStandardError()
        ).decode("utf-8", errors="replace")
        if text:
            self._runtime_stderr += text
            self.console.moveCursor(QTextCursor.MoveOperation.End)
            self.console.insertPlainText(text)

    def _process_finished(self, exit_code: int, exit_status):
        if self._runtime_stdout_buffer:
            line = self._runtime_stdout_buffer.strip()
            if line.startswith(DEBUG_STREAM_PREFIX):
                self._handle_debug_message(line[len(DEBUG_STREAM_PREFIX):].strip())
            elif line:
                self.console.moveCursor(QTextCursor.MoveOperation.End)
                self.console.insertPlainText(self._runtime_stdout_buffer)
            self._runtime_stdout_buffer = ""
        self.console.appendPlainText(
            f"\n[Процесс завершён, код {exit_code}]"
        )
        self.run_action.setEnabled(True)
        self.debug_run_action.setEnabled(True)
        self.debug_run_button.setEnabled(True)
        self.stop_action.setEnabled(False)
        self._debug_mode_active = False
        self._debug_waiting_flow = False
        self.debug_continue_button.setEnabled(False)
        self.debug_step_button.setEnabled(False)
        self.debug_start_button.setEnabled(False)
        self.debug_stop_button.setEnabled(False)
        self._restore_debug_layout()
        combined_output = "\n".join(
            value for value in (self._runtime_stdout, self._runtime_stderr) if value
        )
        stderr_is_exception = (
            "Traceback (most recent call last)" in self._runtime_stderr
            or "[RUNTIME_ERROR_LOG]" in self._runtime_stderr
        )
        if exit_code != 0 or stderr_is_exception:
            diagnostics = runtime_diagnostics(
                self._runtime_stderr,
                self._preview_source,
                str(self._preview_path or ""),
            )
            if not diagnostics and exit_code != 0:
                diagnostics = runtime_diagnostics(
                    f"Процесс завершён с кодом {exit_code}.",
                    self._preview_source,
                    str(self._preview_path or ""),
                )
            self.problems.clear()
            for diagnostic in diagnostics:
                node = self.scene.nodes.get(diagnostic.node_id)
                caption = node.spec.caption if node else (
                    diagnostic.node_type or "Выполнение"
                )
                item = QTreeWidgetItem([format_diagnostic(diagnostic), caption])
                item.setData(0, Qt.ItemDataRole.UserRole, diagnostic.node_id)
                item.setToolTip(0, diagnostic.detail)
                item.setForeground(0, QColor("#C62828"))
                self.problems.addTopLevelItem(item)
            log_dir = Path.home() / ".visual_python_builder" / "logs"
            self._debug_log_path = write_debug_log(
                log_dir / f"runtime_{uuid.uuid4().hex[:10]}.log",
                combined_output or f"Процесс завершён с кодом {exit_code}.",
            )
            self.console.appendPlainText(
                f"\n[Отладочный лог: {self._debug_log_path}]"
            )
            self.problems_dock.show()
            self.statusBar().showMessage(
                f"Ошибка выполнения. Лог сохранён: {self._debug_log_path}", 10000
            )
            return
        self.statusBar().showMessage(
            f"Проект завершён с кодом {exit_code}", 5000
        )

    def _handle_debug_message(self, raw: str):
        # Normal F5 runs must never populate the debugger or animate wires.
        # The generated runtime also suppresses these messages, but keeping
        # this guard here protects the editor from stale/foreign output.
        if not self._debug_mode_active:
            return
        try:
            payload = json.loads(raw)
        except Exception:
            return
        kind = str(payload.get("kind", "probe"))
        node_id = str(payload.get("node_id", ""))
        port = str(payload.get("port", ""))
        if kind == "flow":
            armed = self._debug_animation_armed
            matched = False
            if armed and self.debug_animation_checkbox.isChecked():
                matched = self.scene.trigger_debug_flow(node_id, port)
            if not self._debug_mode_active:
                return
            if (
                not armed
                or not matched
                or not self.debug_animation_checkbox.isChecked()
            ):
                self._send_debug_command("flow_ack")
            elif self.debug_speed_slider.value() == 0:
                self._debug_waiting_flow = True
                self.debug_step_button.setEnabled(True)
            else:
                self._debug_waiting_flow = True
                QTimer.singleShot(
                    max(1, self.scene.debug_pulse_duration),
                    lambda: self._send_debug_command("flow_ack"),
                )
            return
        point = str(payload.get("point", "")).strip() or "без имени"
        value = payload.get("value")
        if isinstance(value, (dict, list)):
            value_text = json.dumps(value, ensure_ascii=False, default=str)
        else:
            value_text = str(value)
        state = "ТОЧКА ОСТАНОВА" if kind == "breakpoint" else "измерение"
        row = self._debug_rows.get(point)
        if row is None:
            row = self.debug_table.rowCount()
            self.debug_table.insertRow(row)
            self._debug_rows[point] = row
        values = [
            point,
            value_text,
            str(payload.get("type", "")),
            str(payload.get("time", "")),
            state,
        ]
        for column, text in enumerate(values):
            item = self.debug_table.item(row, column)
            if item is None:
                item = QTableWidgetItem()
                self.debug_table.setItem(row, column, item)
            item.setText(text)
            if column == 1:
                item.setToolTip(
                    f"Нода: {payload.get('node_id', '')}\n"
                    f"Порт: {payload.get('port', '')}"
                )
        if self.debug_animation_checkbox.isChecked():
            self.scene.trigger_debug_flow(node_id, port)
        color = QColor("#C62828" if kind == "breakpoint" else "#4A148C")
        for column in range(self.debug_table.columnCount()):
            item = self.debug_table.item(row, column)
            if item:
                item.setForeground(color)
        if kind == "breakpoint":
            self._debug_animation_armed = True
            self.debug_step_button.setEnabled(False)
            self.debug_continue_button.setEnabled(True)
            self.statusBar().showMessage(
                f"Выполнение остановлено на точке «{point}». Нажмите «Продолжить».",
                0,
            )
        self.debugger_dock.show()

    def _clear_debug_values(self):
        self.debug_table.setRowCount(0)
        self._debug_rows.clear()
        self.debug_continue_button.setEnabled(False)

    def _send_debug_command(self, command: str):
        if self.preview_process.state() == QProcess.ProcessState.NotRunning:
            return
        payload = (json.dumps({"cmd": command}, ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
        self.preview_process.write(payload)
        self.preview_process.waitForBytesWritten(250)
        if command in {"continue", "resume"}:
            self.debug_continue_button.setEnabled(False)
        elif command == "debug_start":
            self.debug_start_button.setEnabled(False)
        elif command == "flow_ack":
            self._debug_waiting_flow = False
            self.debug_step_button.setEnabled(False)

    def save_debug_log(self):
        """Save the last preview output and generated source for bug reports."""
        if not self._runtime_stdout and not self._runtime_stderr and not self._preview_source:
            self.statusBar().showMessage("Отладочных данных пока нет.", 4000)
            return
        default_path = str(
            self._debug_log_path
            or (Path.home() / ".visual_python_builder" / "debug.log")
        )
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отладочный лог",
            default_path,
            "Лог и текст (*.log *.txt);;Все файлы (*)",
        )
        if not filename:
            return
        source = self._preview_source
        output = "\n".join(
            value for value in (self._runtime_stdout, self._runtime_stderr) if value
        )
        text = (
            "Visual Python Builder runtime diagnostic\n"
            f"Preview: {self._preview_path or 'не создан'}\n\n"
            "=== GENERATED SOURCE ===\n"
            f"{source}\n"
            "=== PROCESS OUTPUT ===\n"
            f"{output}\n"
        )
        destination = write_debug_log(filename, text)
        self._debug_log_path = destination
        self.statusBar().showMessage(f"Отладочный лог сохранён: {destination}", 7000)

    @staticmethod
    def _write_text_atomic(path: Path, text: str):
        """Write a UTF-8 file without leaving a partially written target."""
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def validate_project(self, show_success: bool = True):
        project = self.scene.to_project(self.project_name)
        errors = self._validate_project(project)
        warnings = (self._validate_project_warnings(project)
                    if not self._validate_project_structure(project) else [])
        if not errors:
            try:
                compile(generate_python(project), "<диагностика>", "exec")
            except Exception as exc:
                errors.append(f"Генератор создал некорректный Python-код: {exc}")
        self.problems.clear()
        for severity, messages in (("Ошибка", errors), ("Предупреждение", warnings)):
            for message in messages:
                node_id = ""
                if message.startswith("[") and "]" in message:
                    node_id, message = message[1:].split("]", 1)
                    message = message.strip()
                node = self.scene.nodes.get(node_id)
                caption = node.spec.caption if node else "Проект"
                item = QTreeWidgetItem([f"{severity}: {message}", caption])
                item.setData(0, Qt.ItemDataRole.UserRole, node_id)
                item.setForeground(0, QColor("#C62828" if severity == "Ошибка" else "#B26A00"))
                self.problems.addTopLevelItem(item)
        if errors or warnings:
            self.problems_dock.show()
            self.statusBar().showMessage(
                f"Диагностика: ошибок {len(errors)}, предупреждений {len(warnings)}", 5000
            )
        elif show_success:
            self.problems_dock.show()
            self.problems.addTopLevelItem(QTreeWidgetItem(["Ошибок и предупреждений не найдено", "Проект"]))
            self.statusBar().showMessage("Диагностика завершена: проблем нет", 5000)
        return errors

    def _problem_activated(self, item: QTreeWidgetItem, column: int):
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        node = self.scene.nodes.get(node_id) if node_id else None
        if node:
            self.tabs.setCurrentWidget(self.scheme_page)
            self.scene.clearSelection()
            node.setSelected(True)
            self.view.centerOn(node)

    def _validate_project(self, project: dict[str, Any]) -> list[str]:
        errors = self._validate_project_structure(project)
        if errors:
            return errors
        nodes = project.get("nodes", [])
        links = project.get("connections", [])
        by_id = {node.get("id"): node for node in nodes}
        types = [node.get("type") for node in nodes]
        if types.count("Form") != 1:
            errors.append("В проекте должна быть ровно одна «Форма».")
        # Форма сама является полноценной программой. Пустое окно — законный
        # результат, поэтому отсутствие дочерних виджетов не считается ошибкой.
        names: dict[str, str] = {}
        for node in nodes:
            node_id = str(node.get("id", ""))
            node_type = node.get("type")
            if node_type not in COMPONENTS:
                errors.append(f"[{node_id}] Неизвестный тип компонента: {node_type}")
                continue
            errors.extend(diagnose_node_model(node))
            props = node.get("properties", {})
            name = str(props.get("name", "")).strip()
            if name:
                if not name.isidentifier() or keyword.iskeyword(name):
                    errors.append(f"[{node_id}] Недопустимое имя Python: {name}")
                elif name in names:
                    errors.append(f"[{node_id}] Имя «{name}» уже используется.")
                else:
                    names[name] = node_id
        bindable = {
            "text": {"LineEdit", "TextEdit", "PlainTextEdit"},
            "value": {"Slider", "SpinBox", "DoubleSpinBox", "Dial", "ScrollBar"},
            "checked": {"CheckBox", "RadioButton", "GroupBox", "Button", "ToolButton"},
            "currentIndex": {"ComboBox"},
        }
        named_nodes = {
            str(node.get("properties", {}).get("name", "")).strip(): node
            for node in nodes if str(node.get("properties", {}).get("name", "")).strip()
        }
        for node in nodes:
            if node.get("type") != "TwoWayBinding":
                continue
            node_id = str(node.get("id", ""))
            props = node.get("properties", {})
            target_name = str(props.get("target", "")).strip()
            property_name = str(props.get("property", "text"))
            target = named_nodes.get(target_name)
            if target is None:
                errors.append(f"[{node_id}] Компонент привязки «{target_name}» не найден.")
            elif target.get("type") not in bindable.get(property_name, set()):
                errors.append(
                    f"[{node_id}] Свойство «{property_name}» нельзя привязать к "
                    f"компоненту типа «{target.get('type')}»."
                )

        occupied_inputs: set[tuple[str, str]] = set()
        for link in links:
            source = by_id.get(link.get("from_node"))
            target = by_id.get(link.get("to_node"))
            if not source or not target:
                errors.append("Обнаружена связь с удалённым компонентом.")
                continue
            if (
                source.get("type") not in COMPONENTS
                or target.get("type") not in COMPONENTS
            ):
                continue
            source_ports = {
                port.name: port for port in effective_ports(
                    source["type"], source.get("properties", {})
                )
            }
            target_ports = {
                port.name: port for port in effective_ports(
                    target["type"], target.get("properties", {})
                )
            }
            source_port = source_ports.get(str(link.get("from_port")))
            target_port = target_ports.get(str(link.get("to_port")))
            if source_port is None:
                errors.append(
                    f"[{source['id']}] Неизвестная исходящая точка "
                    f"«{link.get('from_port')}»."
                )
                continue
            if target_port is None:
                errors.append(
                    f"[{target['id']}] Неизвестная входящая точка "
                    f"«{link.get('to_port')}»."
                )
                continue
            advice = advise_connection(
                source_port.kind,
                target_port.kind,
                source_port.data_type,
                target_port.data_type,
                same_node=source.get("id") == target.get("id"),
            )
            if not advice.allowed:
                fix = (
                    f" Вставьте универсальную ноду "
                    f"«{advice.adapter_caption}»."
                    if advice.needs_adapter else ""
                )
                errors.append(
                    f"[{target['id']}] Нельзя передать «{source_port.caption}» "
                    f"ноды «{COMPONENTS[source['type']].caption}» в "
                    f"«{target_port.caption}» ноды "
                    f"«{COMPONENTS[target['type']].caption}». "
                    f"{advice.message}{fix}"
                )
            source_enabled = source.get(
                "enabled_ports", list(source_ports)
            )
            target_enabled = target.get(
                "enabled_ports", list(target_ports)
            )
            if source_port.name not in source_enabled:
                errors.append(
                    f"[{source['id']}] Связь использует отключённую точку "
                    f"«{source_port.caption}»."
                )
            if target_port.name not in target_enabled:
                errors.append(
                    f"[{target['id']}] Связь использует отключённую точку "
                    f"«{target_port.caption}»."
                )
            key = (str(link.get("to_node")), str(link.get("to_port")))
            if key in occupied_inputs:
                errors.append(f"[{key[0]}] К точке «{key[1]}» подключено несколько источников.")
            occupied_inputs.add(key)
        return errors

    @staticmethod
    def _validate_project_warnings(project: dict[str, Any]) -> list[str]:
        """Non-blocking pre-run checks for risky or incomplete scenarios."""
        nodes = project.get("nodes", [])
        links = project.get("connections", [])
        warnings: list[str] = diagnose_event_flow(project)
        environment_types = {
            "FileRead": "чтение файла", "FileWrite": "запись файла",
            "HTTPGet": "сетевой запрос", "RunProcess": "внешний процесс",
            "SQLiteQuery": "доступ к базе данных", "OpenFileDialog": "диалог файла",
            "SaveFileDialog": "диалог файла",
        }
        for node in nodes:
            node_id = str(node.get("id", ""))
            node_type = str(node.get("type", ""))
            props = node.get("properties", {})
            if node_type in environment_types:
                warnings.append(
                    f"[{node_id}] Узел использует окружение ({environment_types[node_type]}); "
                    "проверьте доступность ресурсов на целевой машине."
                )
            if node_type == "FileRead":
                path = str(props.get("path", "")).strip()
                if not path:
                    warnings.append(f"[{node_id}] Не задан путь к читаемому файлу.")
                elif not Path(path).expanduser().exists():
                    warnings.append(f"[{node_id}] Файл пока не существует: {path}")
            if node_type == "FileWrite" and not str(props.get("path", "")).strip():
                warnings.append(f"[{node_id}] Не задан путь для записи файла.")
            if node_type == "HTTPGet" and not str(props.get("url", "")).strip():
                warnings.append(f"[{node_id}] Не задан URL сетевого запроса.")
            if node_type == "RunProcess" and not str(props.get("program", "")).strip():
                warnings.append(f"[{node_id}] Не задана запускаемая программа.")
            if node_type == "RepeatLoop" and int(props.get("count", 10) or 0) > 10000:
                warnings.append(f"[{node_id}] Большой синхронный цикл может временно заблокировать интерфейс.")
            if node_type in {"ForRange", "WhileLoop"} and int(props.get("max_iterations", props.get("stop", 10)) or 0) > 10000:
                warnings.append(f"[{node_id}] Большой синхронный цикл может временно заблокировать интерфейс.")
            if node_type == "WhileLoop" and not any(link.get("to_node") == node_id and link.get("to_port") == "Condition" for link in links):
                warnings.append(f"[{node_id}] Условие while не подключено; остановка зависит от doBreak или защитного предела.")
            if node_type == "UserContainer" and not props.get("interface"):
                warnings.append(f"[{node_id}] Контейнер не имеет внешних точек.")
            if node_type == "KeyboardInput" and not str(props.get("keys", "")).strip():
                warnings.append(f"[{node_id}] Фильтр клавиатуры пуст: будут приниматься все клавиши.")
        # Detect event-flow cycles. They can be intentional, so this is a warning.
        graph: dict[str, set[str]] = {}
        by_id = {node.get("id"): node for node in nodes}
        for link in links:
            source = by_id.get(link.get("from_node"))
            if not source or source.get("type") not in COMPONENTS:
                continue
            ports = {p.name: p for p in effective_ports(source["type"], source.get("properties", {}))}
            port = ports.get(str(link.get("from_port")))
            if port and port.kind == "event_out":
                graph.setdefault(str(link.get("from_node")), set()).add(str(link.get("to_node")))
        visiting: set[str] = set(); visited: set[str] = set(); cycle_nodes: set[str] = set()
        def visit(node_id: str):
            if node_id in visiting:
                cycle_nodes.add(node_id); return
            if node_id in visited: return
            visiting.add(node_id)
            for target in graph.get(node_id, ()): visit(target)
            visiting.remove(node_id); visited.add(node_id)
        for node_id in graph: visit(node_id)
        if cycle_nodes:
            warnings.append("В цепочке событий обнаружен цикл; убедитесь, что он не вызывает бесконечный повтор.")
        return warnings

    @staticmethod
    def _validate_project_structure(project: Any) -> list[str]:
        if not isinstance(project, dict):
            return ["Корень файла проекта должен быть JSON-объектом."]
        if project.get("format", 1) != 1:
            return [f"Неподдерживаемый формат проекта: {project.get('format')}."]
        nodes = project.get("nodes")
        links = project.get("connections")
        if not isinstance(nodes, list) or not isinstance(links, list):
            return ["Поля «nodes» и «connections» должны быть списками."]
        errors: list[str] = []
        ids: set[str] = set()
        for index, node in enumerate(nodes, 1):
            if not isinstance(node, dict):
                errors.append(f"Компонент №{index} должен быть JSON-объектом.")
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id:
                errors.append(f"У компонента №{index} отсутствует корректный id.")
            elif node_id in ids:
                errors.append(f"[{node_id}] Идентификатор компонента повторяется.")
            else:
                ids.add(node_id)
            if not isinstance(node.get("type"), str):
                errors.append(f"[{node_id or index}] Отсутствует тип компонента.")
            if not isinstance(node.get("properties", {}), dict):
                errors.append(f"[{node_id or index}] Свойства должны быть объектом.")
            enabled_ports = node.get("enabled_ports")
            if enabled_ports is not None and not isinstance(enabled_ports, list):
                errors.append(
                    f"[{node_id or index}] enabled_ports должен быть списком."
                )
        for index, link in enumerate(links, 1):
            if not isinstance(link, dict):
                errors.append(f"Связь №{index} должна быть JSON-объектом.")
                continue
            required = ("from_node", "from_port", "to_node", "to_port")
            if any(not isinstance(link.get(key), str) for key in required):
                errors.append(f"Связь №{index} содержит некорректные поля.")
        return errors

    def _confirm_discard(self) -> bool:
        if not self.modified:
            return True
        answer = QMessageBox.question(
            self,
            "Несохранённые изменения",
            "Сохранить изменения перед продолжением?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            return bool(self.save_project())
        return True

    def closeEvent(self, event):
        if self._confirm_discard():
            workspace = QSettings(
                "VisualPythonBuilder", "VisualPythonBuilder"
            )
            workspace.setValue("workspace/geometry", self.saveGeometry())
            workspace.setValue("workspace/state", self.saveState())
            if self.preview_process.state() != QProcess.ProcessState.NotRunning:
                self.preview_process.kill()
                self.preview_process.waitForFinished(1000)
            event.accept()
        else:
            event.ignore()
