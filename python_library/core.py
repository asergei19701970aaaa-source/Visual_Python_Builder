"""Ядро NodeFlow 18.0: четыре вида точек, граф и статический предпросмотр.

Здесь нет ни одного импорта PyQt — ядро работает без GUI
(и потому его можно тестировать в консоли: python main.py --headless).

Событийное выполнение находится в :mod:`python_library.runtime`. ``evaluate()``
оставлен как статический предпросмотр значений и генераторных описателей.
"""
from __future__ import annotations

import time
from dataclasses import replace
import traceback as _tb
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "18.0"

# Все типы портов. "any" совместим со всем.
PORT_TYPES: Tuple[str, ...] = (
    "any", "number", "text", "bool", "list", "dict",
    "widget", "layout", "window", "menu", "action", "binding",
    "style", "color", "font", "shape", "image", "file", "code", "chart",
    "value", "expression", "actions", "grid2d", "events",
)
PORT_KINDS: Tuple[str, ...] = ("method", "event", "data", "property")
INPUT_KINDS = {"method", "data"}
OUTPUT_KINDS = {"event", "property"}
PORT_KIND_NAMES = {
    "method": "Метод", "event": "Событие",
    "data": "Данные", "property": "Свойство",
}
PORT_KIND_SIDES = {
    "method": "слева", "event": "справа",
    "data": "сверху", "property": "снизу",
}
# Эти имена читаются только при миграции проектов 4.0. В новых спецификациях
# одинаковые «Выполнить/Готово» больше не создаются.
LEGACY_FLOW_METHOD_NAME = "__do__"
LEGACY_FLOW_EVENT_NAME = "__done__"
FLOW_METHOD_NAME = LEGACY_FLOW_METHOD_NAME
FLOW_EVENT_NAME = LEGACY_FLOW_EVENT_NAME
FLOW_SIGNAL_PREFIX = "__signal_"

# Реальные сигналы интерактивных GUI-элементов. Они компилируются в обычные
# Qt signal.connect(...) без промежуточной ноды «Связь: сигнал → действия».
GUI_SIGNAL_PORTS = {
    "Gui.button": (("__signal_clicked__", "onClick", "clicked"),),
    "Gui.checkbox": (("__signal_toggled__", "onChange", "toggled"),),
    "Gui.radio": (("__signal_toggled__", "onChange", "toggled"),),
    "Gui.line_edit": (("__signal_textChanged__", "onChange", "textChanged"),
                      ("__signal_returnPressed__", "onEnter", "returnPressed")),
    "Gui.text_edit": (("__signal_textChanged__", "onChange", "textChanged"),),
    "Gui.combo_box": (("__signal_currentIndexChanged__", "onChange", "currentIndexChanged"),),
    "Gui.list_widget": (("__signal_itemSelectionChanged__", "onSelect", "itemSelectionChanged"),),
    "Gui.spin_box": (("__signal_valueChanged__", "onChange", "valueChanged"),),
    "Gui.slider": (("__signal_valueChanged__", "onChange", "valueChanged"),),
    "Gui.table": (("__signal_itemSelectionChanged__", "onSelect", "itemSelectionChanged"),),
    "Gui.tree": (("__signal_itemSelectionChanged__", "onSelect", "itemSelectionChanged"),),
    "Gui.calendar": (("__signal_selectionChanged__", "onChange", "selectionChanged"),),
    "Gui.date_edit": (("__signal_dateChanged__", "onChange", "dateChanged"),),
    "Gui.tab_widget": (("__signal_currentChanged__", "onChange", "currentChanged"),),
    "GuiQt.tool_button": (("__signal_clicked__", "onClick", "clicked"),),
    "GuiQt.command_link_button": (("__signal_clicked__", "onClick", "clicked"),),
    "GuiQt.dialog_button_box": (("__signal_accepted__", "onAccept", "accepted"),
                                ("__signal_rejected__", "onReject", "rejected")),
    "GuiQt.font_combo_box": (("__signal_currentFontChanged__", "onChange", "currentFontChanged"),),
    "GuiQt.plain_text_edit": (("__signal_textChanged__", "onChange", "textChanged"),),
    "GuiQt.key_sequence_edit": (("__signal_keySequenceChanged__", "onChange", "keySequenceChanged"),),
    "GuiQt.time_edit": (("__signal_timeChanged__", "onChange", "timeChanged"),),
    "GuiQt.date_time_edit": (("__signal_dateTimeChanged__", "onChange", "dateTimeChanged"),),
    "GuiQt.dial": (("__signal_valueChanged__", "onChange", "valueChanged"),),
    "GuiQt.scroll_bar": (("__signal_valueChanged__", "onChange", "valueChanged"),),
}

# Явные HiAsm-подобные боковые выходы для регуляторов. Старые технические
# имена __signal_* сохраняются невидимыми, чтобы не ломать проекты 5–12.
HIASM_PRIMARY_SIGNALS = {
    "Gui.slider": ("onPosition", "Позиция изменена", "valueChanged", "number"),
    "Gui.spin_box": (
        "onValueChanged", "Значение изменено", "valueChanged", "number"),
    "GuiQt.dial": ("onPosition", "Позиция изменена", "valueChanged", "number"),
    "GuiQt.scroll_bar": (
        "onPosition", "Позиция изменена", "valueChanged", "number"),
}

# События универсальной ноды, созданной импортом Qt Designer. Класс хранится
# в params, поэтому её интерфейс строится для каждого экземпляра отдельно.
DESIGNER_CLASS_SIGNAL_PORTS = {
    "QPushButton": (("__signal_clicked__", "onClick", "clicked"),),
    "QToolButton": (("__signal_clicked__", "onClick", "clicked"),),
    "QCommandLinkButton": (("__signal_clicked__", "onClick", "clicked"),),
    "QCheckBox": (("__signal_toggled__", "onChange", "toggled"),),
    "QRadioButton": (("__signal_toggled__", "onChange", "toggled"),),
    "QLineEdit": (
        ("__signal_textChanged__", "onChange", "textChanged"),
        ("__signal_returnPressed__", "onEnter", "returnPressed"),
    ),
    "QTextEdit": (("__signal_textChanged__", "onChange", "textChanged"),),
    "QPlainTextEdit": (("__signal_textChanged__", "onChange", "textChanged"),),
    "QComboBox": (
        ("__signal_currentIndexChanged__", "onChange",
         "currentIndexChanged"),),
    "QFontComboBox": (
        ("__signal_currentFontChanged__", "onChange",
         "currentFontChanged"),),
    "QListWidget": (
        ("__signal_itemSelectionChanged__", "onSelect",
         "itemSelectionChanged"),),
    "QTreeWidget": (
        ("__signal_itemSelectionChanged__", "onSelect",
         "itemSelectionChanged"),),
    "QTableWidget": (
        ("__signal_itemSelectionChanged__", "onSelect",
         "itemSelectionChanged"),),
    "QSpinBox": (("__signal_valueChanged__", "onChange", "valueChanged"),),
    "QDoubleSpinBox": (
        ("__signal_valueChanged__", "onChange", "valueChanged"),),
    "QSlider": (("__signal_valueChanged__", "onChange", "valueChanged"),),
    "QDial": (("__signal_valueChanged__", "onChange", "valueChanged"),),
    "QScrollBar": (
        ("__signal_valueChanged__", "onChange", "valueChanged"),),
    "QCalendarWidget": (
        ("__signal_selectionChanged__", "onChange", "selectionChanged"),),
    "QDateEdit": (("__signal_dateChanged__", "onChange", "dateChanged"),),
    "QTimeEdit": (("__signal_timeChanged__", "onChange", "timeChanged"),),
    "QDateTimeEdit": (
        ("__signal_dateTimeChanged__", "onChange", "dateTimeChanged"),),
    "QTabWidget": (
        ("__signal_currentChanged__", "onChange", "currentChanged"),),
    "QDialogButtonBox": (
        ("__signal_accepted__", "onAccept", "accepted"),
        ("__signal_rejected__", "onReject", "rejected"),
    ),
}

# Возможности методов GUI. Один и тот же набор применяется к обычным нодам и
# экземплярам, созданным импортом Qt Designer.
GUI_CLASS_CAPABILITIES = {
    "QPushButton": ("text", "enabled", "visible"),
    "QToolButton": ("text", "enabled", "visible"),
    "QCommandLinkButton": ("text", "enabled", "visible"),
    "QLabel": ("text", "enabled", "visible"),
    "QLineEdit": ("text", "clear", "enabled", "visible"),
    "QTextEdit": ("text", "clear", "enabled", "visible"),
    "QPlainTextEdit": ("text", "clear", "enabled", "visible"),
    "QTextBrowser": ("text", "clear", "enabled", "visible"),
    "QCheckBox": ("checked", "text", "enabled", "visible"),
    "QRadioButton": ("checked", "text", "enabled", "visible"),
    "QComboBox": ("index", "clear", "enabled", "visible"),
    "QListWidget": ("add_item", "clear", "enabled", "visible"),
    "QTreeWidget": ("clear", "enabled", "visible"),
    "QTableWidget": ("clear", "enabled", "visible"),
    "QSpinBox": ("value", "enabled", "visible"),
    "QDoubleSpinBox": ("value", "enabled", "visible"),
    "QSlider": ("value", "enabled", "visible"),
    "QDial": ("value", "enabled", "visible"),
    "QScrollBar": ("value", "enabled", "visible"),
    "QProgressBar": ("value", "enabled", "visible"),
    "QLCDNumber": ("display", "enabled", "visible"),
    "QTabWidget": ("index", "enabled", "visible"),
    "QStackedWidget": ("index", "enabled", "visible"),
    "QDateEdit": ("enabled", "visible"),
    "QTimeEdit": ("enabled", "visible"),
    "QDateTimeEdit": ("enabled", "visible"),
    "QCalendarWidget": ("enabled", "visible"),
    "QGroupBox": ("enabled", "visible"),
    "QWidget": ("enabled", "visible"),
}

GUI_KEY_CLASSES = {
    "Gui.button": "QPushButton",
    "Gui.label": "QLabel",
    "Gui.line_edit": "QLineEdit",
    "Gui.text_edit": "QTextEdit",
    "Gui.checkbox": "QCheckBox",
    "Gui.radio": "QRadioButton",
    "Gui.combo_box": "QComboBox",
    "Gui.list_widget": "QListWidget",
    "Gui.spin_box": "QSpinBox",
    "Gui.slider": "QSlider",
    "Gui.progress_bar": "QProgressBar",
    "Gui.table": "QTableWidget",
    "Gui.tree": "QTreeWidget",
    "Gui.calendar": "QCalendarWidget",
    "Gui.date_edit": "QDateEdit",
    "Gui.tab_widget": "QTabWidget",
    "Gui.image": "QLabel",
    "Gui.separator": "QFrame",
    "Gui.group_box": "QGroupBox",
    "Gui.scroll_area": "QScrollArea",
    "Gui.chart_widget": "QWidget",
    "Gui.text_browser": "QTextBrowser",
    "Gui.custom_widget": "QWidget",
    "Gui.designer_container": "QWidget",
    "Gui.web_engine_view": "QWebEngineView",
    "GuiQt.tool_button": "QToolButton",
    "GuiQt.command_link_button": "QCommandLinkButton",
    "GuiQt.dialog_button_box": "QDialogButtonBox",
    "GuiQt.font_combo_box": "QFontComboBox",
    "GuiQt.plain_text_edit": "QPlainTextEdit",
    "GuiQt.key_sequence_edit": "QKeySequenceEdit",
    "GuiQt.time_edit": "QTimeEdit",
    "GuiQt.date_time_edit": "QDateTimeEdit",
    "GuiQt.dial": "QDial",
    "GuiQt.scroll_bar": "QScrollBar",
    "GuiQt.lcd_number": "QLCDNumber",
    "GuiQt.tree_widget": "QTreeWidget",
    "GuiQt.list_view": "QListView",
    "GuiQt.column_view": "QColumnView",
    "GuiQt.tool_box": "QToolBox",
    "GuiQt.stacked_widget": "QStackedWidget",
    "GuiQt.splitter": "QSplitter",
    "GuiQt.mdi_area": "QMdiArea",
    "GuiQt.dock_widget": "QDockWidget",
    "GuiQt.frame": "QFrame",
    "GuiQt.graphics_view": "QGraphicsView",
    "Layout.container": "QWidget",
    "Layout.splitter": "QSplitter",
}

# Автоматическое обновление проектов, импортированных старыми версиями:
# универсальная Designer-нода заменяется обычной нодой библиотеки.
LEGACY_DESIGNER_NODE_KEYS = {
    "QPushButton": "Gui.button",
    "QToolButton": "GuiQt.tool_button",
    "QCommandLinkButton": "GuiQt.command_link_button",
    "QDialogButtonBox": "GuiQt.dialog_button_box",
    "QLabel": "Gui.label",
    "QLineEdit": "Gui.line_edit",
    "QTextEdit": "Gui.text_edit",
    "QPlainTextEdit": "GuiQt.plain_text_edit",
    "QTextBrowser": "Gui.text_browser",
    "QCheckBox": "Gui.checkbox",
    "QRadioButton": "Gui.radio",
    "QComboBox": "Gui.combo_box",
    "QFontComboBox": "GuiQt.font_combo_box",
    "QListWidget": "Gui.list_widget",
    "QListView": "GuiQt.list_view",
    "QTreeWidget": "GuiQt.tree_widget",
    "QTreeView": "Gui.tree",
    "QTableWidget": "Gui.table",
    "QTableView": "Gui.table",
    "QColumnView": "GuiQt.column_view",
    "QSpinBox": "Gui.spin_box",
    "QDoubleSpinBox": "Gui.spin_box",
    "QTimeEdit": "GuiQt.time_edit",
    "QDateEdit": "Gui.date_edit",
    "QDateTimeEdit": "GuiQt.date_time_edit",
    "QSlider": "Gui.slider",
    "QDial": "GuiQt.dial",
    "QScrollBar": "GuiQt.scroll_bar",
    "QLCDNumber": "GuiQt.lcd_number",
    "QProgressBar": "Gui.progress_bar",
    "QCalendarWidget": "Gui.calendar",
    "QKeySequenceEdit": "GuiQt.key_sequence_edit",
    "QGraphicsView": "GuiQt.graphics_view",
    "QWebEngineView": "Gui.web_engine_view",
    "QOpenGLWidget": "Gui.custom_widget",
    "QQuickWidget": "Gui.custom_widget",
    "Line": "Gui.separator",
    "QGroupBox": "Gui.group_box",
    "QFrame": "GuiQt.frame",
    "QScrollArea": "Gui.scroll_area",
    "QSplitter": "GuiQt.splitter",
    "QToolBox": "GuiQt.tool_box",
    "QStackedWidget": "GuiQt.stacked_widget",
    "QDockWidget": "GuiQt.dock_widget",
    "QMdiArea": "GuiQt.mdi_area",
    "QTabWidget": "Gui.tab_widget",
}

WINDOW_RUNTIME_KEYS = {"Window.app_window", "Window.dialog_window"}
LAYOUT_RUNTIME_KEYS = {
    "Layout.vbox", "Layout.hbox", "Layout.grid", "Layout.form"}

# Явные боковые интерфейсы переходных action-нод. В отличие от 4.0 они
# добавляются не всем подряд, а только элементам с реальным действием.
# Значение: (имя метода, подпись, имя события, подпись события).
SEMANTIC_ACTION_POINTS = {
    "Signal.act_message": ("doShow", "Показать", "onShown", "Показано"),
    "Signal.act_set_text": ("doSetText", "Задать текст", "onChanged", "Изменено"),
    "Signal.act_copy_text": ("doCopy", "Копировать", "onCopied", "Скопировано"),
    "Signal.act_clear": ("doClear", "Очистить", "onCleared", "Очищено"),
    "Signal.act_append": ("doAppend", "Добавить", "onAppended", "Добавлено"),
    "Signal.act_status": ("doStatus", "Показать статус", "onShown", "Показано"),
    "Signal.act_open_file": ("doOpen", "Открыть", "onOpened", "Открыто"),
    "Signal.act_save_file": ("doSave", "Сохранить", "onSaved", "Сохранено"),
    "Signal.act_calc": ("doCalculate", "Вычислить", "onCalculated", "Вычислено"),
    "Signal.act_enable": ("doEnabled", "Изменить доступность", "onChanged", "Изменено"),
    "Signal.act_visible": ("doVisible", "Изменить видимость", "onChanged", "Изменено"),
    "Signal.act_close": ("doClose", "Закрыть", "onClosed", "Закрыто"),
    "Signal.act_timer": ("doStart", "Запустить таймер", "onStarted", "Запущено"),
    "Signal.act_code": ("doExecute", "Выполнить код", "onExecuted", "Выполнено"),
    "RuntimeMemory.memory_change": ("doChange", "Изменить", "onChange", "Изменено"),
    "RuntimeFlow.show_value": ("doShow", "Показать", "onShown", "Показано"),
    "RuntimeFlow.timer_control": ("doTimer", "Управлять", "onChanged", "Изменено"),
    "RuntimeFlow.repaint_canvas": ("doRepaint", "Перерисовать", "onRepaint", "Перерисовано"),
    "RuntimeGrid.grid_change": ("doChange", "Изменить", "onChange", "Изменено"),
    "RuntimePaint.draw_shape": ("doDraw", "Рисовать", "onDraw", "Нарисовано"),
    "RuntimePaint.draw_grid": ("doDraw", "Рисовать", "onDraw", "Нарисовано"),
}


def is_virtual_flow_output(name: str) -> bool:
    return str(name).startswith(FLOW_SIGNAL_PREFIX)

# Допустимые преобразования типов (источник → приёмник).
COMPATIBLE_PAIRS = {
    ("layout", "widget"), ("widget", "layout"),
    ("widget", "list"), ("layout", "list"), ("action", "list"),
    ("binding", "list"), ("shape", "list"), ("menu", "list"),
    ("dict", "list"),
    ("chart", "widget"),
    ("number", "bool"), ("bool", "number"),
    ("number", "text"), ("bool", "text"),
    ("file", "text"), ("text", "file"),
    ("color", "text"), ("text", "color"),
    ("code", "text"), ("text", "code"),
    ("style", "text"), ("text", "style"),
    ("font", "text"),
    ("image", "file"), ("file", "image"),
    ("action", "actions"), ("actions", "list"),
    ("binding", "events"), ("list", "events"),
    ("grid2d", "value"),
    ("expression", "value"), ("expression", "number"),
    ("expression", "text"), ("expression", "bool"),
    ("expression", "list"), ("expression", "dict"),
    ("expression", "color"), ("expression", "grid2d"),
    ("number", "value"), ("text", "value"), ("bool", "value"),
    ("list", "value"), ("dict", "value"), ("color", "value"),
    ("file", "value"), ("image", "value"), ("code", "value"),
}


class GraphError(Exception):
    """Ошибка структуры графа (цикл, несовместимые типы и т.п.)."""


def types_compatible(source: str, target: str) -> bool:
    """Можно ли соединить выход типа source со входом типа target."""
    if source == target:
        return True
    if "any" in (source, target):
        return True
    return (source, target) in COMPATIBLE_PAIRS


@dataclass
class Port:
    """Описание одного входа или выхода ноды."""

    name: str
    type: str = "any"
    default: Any = None
    label: str = ""
    hint: str = ""
    choices: Optional[List[str]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    multiline: bool = False
    kind: str = ""
    # Имя внешнего сигнала/события хоста. Для Qt это clicked,
    # textChanged и т. п. Поле не влияет на геометрию точки.
    signal: str = ""
    # Используется методом runtime, но не передаётся старой fn при статическом
    # предпросмотре ноды.
    runtime_only: bool = False
    # Формула чтения актуального свойства GUI в сгенерированном приложении.
    runtime_getter: str = ""
    # Служебная структурная точка старой модели GUI. Она остаётся в формате
    # проектов для совместимости, но не рисуется и не требует ручной линии.
    internal: bool = False
    # Поле полного инспектора GUI: хранится в params, но не передаётся fn и
    # не рисуется как точка на ноде.
    inspector_only: bool = False
    group: str = ""
    editor: str = ""
    advanced: bool = False

    def __post_init__(self) -> None:
        if self.type not in PORT_TYPES:
            self.type = "any"
        if self.kind not in ("",) + PORT_KINDS:
            self.kind = ""
        if not self.label:
            self.label = self.name

    @property
    def tooltip(self) -> str:
        parts = [f"{self.label} — тип: {self.type}"]
        if self.kind:
            parts.append(
                f"Роль: {PORT_KIND_NAMES[self.kind]} "
                f"({PORT_KIND_SIDES[self.kind]})")
        if self.hint:
            parts.append(self.hint)
        if self.choices:
            parts.append("Варианты: " + ", ".join(str(c) for c in self.choices))
        if self.minimum is not None or self.maximum is not None:
            parts.append(f"Диапазон: {self.minimum} … {self.maximum}")
        return "\n".join(parts)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "type": self.type, "default": self.default,
            "label": self.label, "hint": self.hint, "choices": self.choices,
            "minimum": self.minimum, "maximum": self.maximum,
            "multiline": self.multiline, "kind": self.kind,
            "signal": self.signal, "runtime_only": self.runtime_only,
            "runtime_getter": self.runtime_getter,
            "internal": self.internal,
            "inspector_only": self.inspector_only,
            "group": self.group, "editor": self.editor,
            "advanced": self.advanced,
        }


@dataclass
class NodeSpec:
    """Шаблон ноды: что она умеет, что принимает и что отдаёт."""

    key: str
    title: str
    category: str
    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)
    fn: Optional[Callable[..., Any]] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    color: str = ""
    doc: str = ""
    purpose: str = ""
    howto: str = ""
    inputs_doc: Dict[str, str] = field(default_factory=dict)
    outputs_doc: Dict[str, str] = field(default_factory=dict)
    connect_from: str = ""
    connect_to: str = ""
    example: str = ""
    mistakes: str = ""
    see_also: str = ""
    # Обработчики нового runtime. Сигнатуры намеренно не типизированы здесь,
    # чтобы core не зависел от python_library.runtime.
    method_handlers: Dict[str, Callable[..., Any]] = field(default_factory=dict)
    property_handlers: Dict[str, Callable[..., Any]] = field(default_factory=dict)
    auto_events: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Роль определяется направлением, а не типом Python-значения.
        # Без явной роли вход является данными, выход — свойством.
        for port in self.inputs:
            if port.kind not in INPUT_KINDS:
                port.kind = "data"
        for port in self.outputs:
            if port.kind not in OUTPUT_KINDS:
                port.kind = "property"
        # Начиная с 11.0 дерево интерфейса собирается автоматически.
        # Старые widget/layout/window-порты сохраняются лишь как внутренний
        # канал совместимости: на холсте этих верхних/нижних точек нет.
        if self.key.startswith(("Gui.", "GuiQt.", "Layout.", "Window.")):
            for port in (*self.inputs, *self.outputs):
                if port.type in ("widget", "layout", "window"):
                    port.internal = True
        # GUI-события являются настоящими индивидуальными событиями элемента.
        for name, label, signal in GUI_SIGNAL_PORTS.get(self.key, ()):
            if not any(port.name == name for port in self.outputs):
                primary = HIASM_PRIMARY_SIGNALS.get(self.key)
                self.outputs.append(Port(
                    name, "action", label=label,
                    hint=f"Реальное событие Qt: {signal}", kind="event",
                    signal=signal,
                    internal=bool(primary and primary[2] == signal)))
        primary = HIASM_PRIMARY_SIGNALS.get(self.key)
        if primary and not any(port.name == primary[0]
                               for port in self.outputs):
            self.outputs.append(Port(
                primary[0], primary[3], label=primary[1],
                hint=(f"Основной боковой выход. Передаёт новое значение "
                      f"сигнала Qt {primary[2]} прямо в подключённый метод."),
                kind="event", signal=primary[2]))
        action = SEMANTIC_ACTION_POINTS.get(self.key)
        if action:
            method_name, method_label, event_name, event_label = action
            if not any(port.name == method_name for port in self.inputs):
                self.inputs.insert(0, Port(
                    method_name, "any", label=method_label, kind="method"))
            if not any(port.name == event_name for port in self.outputs):
                self.outputs.append(Port(
                    event_name, "any", label=event_label, kind="event"))
            self.auto_events.setdefault(method_name, [event_name])
        class_name = GUI_KEY_CLASSES.get(self.key)
        if class_name:
            self._add_gui_methods(
                GUI_CLASS_CAPABILITIES.get(class_name, ()))
        if self.key in WINDOW_RUNTIME_KEYS:
            self._add_window_methods()
        if self.key in LAYOUT_RUNTIME_KEYS:
            self._add_layout_methods()
        self._add_inspector_properties()

    def _add_inspector_properties(self, explicit_class: str = "") -> None:
        """Добавляет полную модель свойств без новых точек на корпусе."""
        from python_library.gui_properties import property_definitions_for
        class_name = explicit_class or GUI_KEY_CLASSES.get(self.key, "")
        for raw in property_definitions_for(self.key, class_name):
            current = self.input(raw["name"])
            if current is not None:
                current.group = raw.get("group", "")
                current.editor = raw.get("editor", "")
                current.advanced = bool(raw.get("advanced"))
                if not current.hint:
                    current.hint = raw.get("hint", "")
                if not current.choices and raw.get("choices"):
                    current.choices = list(raw["choices"])
                if current.minimum is None:
                    current.minimum = raw.get("minimum")
                if current.maximum is None:
                    current.maximum = raw.get("maximum")
                continue
            self.inputs.append(Port(
                raw["name"], raw.get("type", "text"),
                default=raw.get("default"), label=raw.get("label", ""),
                hint=raw.get("hint", ""), choices=raw.get("choices"),
                minimum=raw.get("minimum"), maximum=raw.get("maximum"),
                multiline=bool(raw.get("multiline")), kind="data",
                internal=True, inspector_only=True,
                group=raw.get("group", ""), editor=raw.get("editor", ""),
                advanced=bool(raw.get("advanced"))))

    def _add_gui_methods(self, capabilities: Sequence[str]) -> None:
        """Добавляет осмысленные методы управления виджетом."""
        definitions = {
            "text": ("doSetText", "Задать текст", "MethodText", "text", "",
                     "onTextChanged", "Текст задан"),
            "value": ("doSetValue", "Задать значение", "MethodValue",
                      "number", 0, "onValueSet", "Значение задано"),
            "display": ("doDisplay", "Показать число", "MethodValue",
                        "number", 0, "onValueSet", "Значение показано"),
            "index": ("doSetIndex", "Выбрать индекс", "MethodIndex",
                      "number", 0, "onIndexSet", "Индекс выбран"),
            "checked": ("doSetChecked", "Установить флаг", "MethodChecked",
                        "bool", True, "onChecked", "Флаг установлен"),
            "enabled": ("doEnabled", "Доступность", "MethodEnabled",
                        "bool", True, "onEnabled", "Доступность изменена"),
            "visible": ("doVisible", "Видимость", "MethodVisible",
                        "bool", True, "onVisible", "Видимость изменена"),
            "add_item": ("doAddItem", "Добавить строку", "MethodText",
                         "text", "", "onItemAdded", "Строка добавлена"),
            "clear": ("doClear", "Очистить", "", "any", None,
                      "onCleared", "Очищено"),
        }
        property_definitions = {
            "text": ("CurrentText", "Текущий текст", "text", "text"),
            "value": (
                "CurrentValue", "Текущее значение", "number", "value"),
            "display": (
                "CurrentValue", "Текущее значение", "number", "value"),
            "index": (
                "CurrentIndex", "Текущий индекс", "number", "index"),
            "checked": (
                "IsChecked", "Флаг установлен", "bool", "checked"),
            "enabled": ("IsEnabled", "Доступен", "bool", "enabled"),
            "visible": ("IsVisible", "Видим", "bool", "visible"),
        }
        for capability in capabilities:
            (method, method_label, data, data_type, default,
             event, event_label) = definitions[capability]
            if not any(port.name == method for port in self.inputs):
                self.inputs.append(Port(
                    method, (data_type if data else "action"),
                    label=method_label, kind="method"))
            if data and not any(port.name == data for port in self.inputs):
                self.inputs.append(Port(
                    data, data_type, default=default, label=method_label,
                    kind="data", runtime_only=True))
            if not any(port.name == event for port in self.outputs):
                self.outputs.append(Port(
                    event, "any", label=event_label, kind="event"))
            self.auto_events.setdefault(method, [event])
            prop = property_definitions.get(capability)
            if prop and not any(port.name == prop[0] for port in self.outputs):
                self.outputs.append(Port(
                    prop[0], prop[2], label=prop[1], kind="property",
                    runtime_getter=prop[3]))

    def _add_window_methods(self) -> None:
        definitions = (
            ("doShow", "Показать окно", "", "", None,
             "onShown", "Окно показано"),
            ("doHide", "Скрыть окно", "", "", None,
             "onHidden", "Окно скрыто"),
            ("doClose", "Закрыть окно", "", "", None,
             "onClosed", "Окно закрыто"),
            ("doSetTitle", "Задать заголовок", "MethodTitle", "text", "",
             "onTitleChanged", "Заголовок изменён"),
            ("doSetWidth", "Задать ширину", "MethodWidth", "number", 900,
             "onWidthChanged", "Ширина изменена"),
            ("doSetHeight", "Задать высоту", "MethodHeight", "number", 600,
             "onHeightChanged", "Высота изменена"),
            ("doResize", "Изменить размер", "MethodWidth", "number", 900,
             "onResized", "Размер изменён"),
        )
        for method, label, data, data_type, default, event, event_label in definitions:
            if not any(port.name == method for port in self.inputs):
                self.inputs.append(Port(
                    method, (data_type if data else "action"),
                    label=label, kind="method"))
            if data and not any(port.name == data for port in self.inputs):
                self.inputs.append(Port(
                    data, data_type, default=default, label=label,
                    kind="data", runtime_only=True))
            if method == "doResize" and not any(
                    port.name == "MethodHeight" for port in self.inputs):
                self.inputs.append(Port(
                    "MethodHeight", "number", default=600,
                    label="Новая высота", kind="data", runtime_only=True))
            if not any(port.name == event for port in self.outputs):
                self.outputs.append(Port(
                    event, "any", label=event_label, kind="event"))
            self.auto_events.setdefault(method, [event])
        for name, label, ptype, getter in (
                ("CurrentTitle", "Текущий заголовок", "text", "window_title"),
                ("IsVisible", "Окно видимо", "bool", "visible"),
                ("CurrentWidth", "Текущая ширина", "number", "width"),
                ("CurrentHeight", "Текущая высота", "number", "height")):
            if not any(port.name == name for port in self.outputs):
                self.outputs.append(Port(
                    name, ptype, label=label, kind="property",
                    runtime_getter=getter))

    def _add_layout_methods(self) -> None:
        for method, label, data, event in (
                ("doSetSpacing", "Задать интервал",
                 "MethodSpacing", "onSpacingChanged"),
                ("doSetMargins", "Задать отступы",
                 "MethodMargin", "onMarginsChanged")):
            if not any(port.name == method for port in self.inputs):
                self.inputs.append(Port(
                    method, "number", label=label, kind="method"))
            if not any(port.name == data for port in self.inputs):
                self.inputs.append(Port(
                    data, "number", default=0, label=label,
                    kind="data", runtime_only=True))
            if not any(port.name == event for port in self.outputs):
                self.outputs.append(Port(
                    event, "any", label=label + " изменён", kind="event"))
            self.auto_events.setdefault(method, [event])
        if not any(port.name == "ItemCount" for port in self.outputs):
            self.outputs.append(Port(
                "ItemCount", "number", label="Количество элементов",
                kind="property", runtime_getter="layout_count"))

    def input(self, name: str) -> Optional[Port]:
        for port in self.inputs:
            if port.name == name:
                return port
        return None

    def output(self, name: str) -> Optional[Port]:
        for port in self.outputs:
            if port.name == name:
                return port
        return None

    @property
    def search_text(self) -> str:
        return " ".join([self.title, self.key, self.category,
                         self.description, self.purpose, self.howto,
                         self.connect_from, self.connect_to, self.example,
                         self.see_also, " ".join(self.tags)]).lower()

    @property
    def tooltip(self) -> str:
        lines = [f"<b>{self.title}</b>", f"<i>{self.category}</i>"]
        if self.description:
            lines.append(self.description)
        if self.purpose:
            lines.append(f"<b>Зачем:</b> {self.purpose}")
        if self.inputs:
            lines.append("<b>Входы:</b> " + ", ".join(
                f"{p.label} ({PORT_KIND_NAMES[p.kind]}, {p.type})"
                for p in self.inputs if not p.internal))
        if self.outputs:
            lines.append("<b>Выходы:</b> " + ", ".join(
                f"{p.label} ({PORT_KIND_NAMES[p.kind]}, {p.type})"
                for p in self.outputs if not p.internal))
        if self.doc:
            lines.append(self.doc)
        return "<br>".join(lines)


@dataclass
class Node:
    """Экземпляр ноды на холсте."""

    id: str
    spec_key: str
    x: float = 0.0
    y: float = 0.0
    params: Dict[str, Any] = field(default_factory=dict)
    custom_title: str = ""
    notes: str = ""
    color: str = ""
    collapsed: bool = False
    disabled: bool = False
    width: float = 0.0
    # Скрытие касается только представления. Логика и имена портов стабильны.
    hidden_ports: List[str] = field(default_factory=list)
    # Исходные параметры конкретного виджета Qt Designer. Они накладываются
    # на результат обычной GUI-ноды и сохраняют редкие свойства/геометрию.
    ui_state: Dict[str, Any] = field(default_factory=dict)
    # Контейнер хранит вложенную схему и описание внешних точек.
    subgraph: Dict[str, Any] = field(default_factory=dict)
    interface: Dict[str, Any] = field(default_factory=dict)
    # рассчитанные значения (не сохраняются в файл)
    results: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    traceback: str = ""
    duration_ms: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "spec": self.spec_key, "x": self.x, "y": self.y,
            "params": _jsonable(self.params), "title": self.custom_title,
            "notes": self.notes, "color": self.color,
            "collapsed": self.collapsed, "disabled": self.disabled,
            "width": self.width,
            "hidden_ports": list(self.hidden_ports),
            "ui_state": _jsonable(self.ui_state),
            "subgraph": _jsonable(self.subgraph),
            "interface": _jsonable(self.interface),
        }


@dataclass
class Edge:
    """Связь между выходом одной ноды и входом другой."""

    id: str
    src_node: str
    src_port: str
    dst_node: str
    dst_port: str
    line_style: str = "curve"
    bends: List[List[float]] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "src": [self.src_node, self.src_port],
            "dst": [self.dst_node, self.dst_port],
            "line_style": self.line_style,
            "bends": _jsonable(self.bends),
        }


def _jsonable(value: Any) -> Any:
    """Приводит значение к виду, который можно записать в JSON."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class Graph:
    """Граф нод: хранение, валидация связей, вычисление, сериализация."""

    VERSION = VERSION

    def __init__(self, specs: Optional[Dict[str, NodeSpec]] = None) -> None:
        self.specs: Dict[str, NodeSpec] = dict(specs or {})
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.log: List[str] = []
        self.meta: Dict[str, Any] = {"name": "Новая схема", "notes": ""}
        self._counter = 0

    # ------------------------------------------------------------------ id
    def new_id(self, prefix: str = "n") -> str:
        self._counter += 1
        candidate = f"{prefix}{self._counter}"
        while candidate in self.nodes or candidate in self.edges:
            self._counter += 1
            candidate = f"{prefix}{self._counter}"
        return candidate

    # --------------------------------------------------------------- nodes
    def add_node(self, spec_key: str, x: float = 0.0, y: float = 0.0,
                 params: Optional[Dict[str, Any]] = None,
                 node_id: Optional[str] = None) -> Node:
        spec = self.specs.get(spec_key)
        if spec is None:
            raise GraphError(f"Неизвестный тип ноды: {spec_key}")
        node = Node(id=node_id or self.new_id(), spec_key=spec_key, x=x, y=y)
        node.params = {p.name: p.default for p in spec.inputs
                       if p.kind == "data"}
        if params:
            node.params.update(params)
        effective = self.spec_of(node)
        if effective is not None:
            for port in effective.inputs:
                if port.kind == "data":
                    node.params.setdefault(port.name, port.default)
            node.hidden_ports = [
                f"in:{port.name}" for port in effective.inputs
                if port.runtime_only
            ]
        self.nodes[node.id] = node
        return node

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        for edge_id in [e.id for e in self.edges.values()
                        if e.src_node == node_id or e.dst_node == node_id]:
            self.edges.pop(edge_id, None)

    def spec_of(self, node: Node) -> Optional[NodeSpec]:
        spec = self.specs.get(node.spec_key)
        if spec is not None and node.spec_key == "Gui.designer_widget":
            class_name = str(node.params.get("class_name") or "QWidget")
            outputs = list(spec.outputs)
            for name, label, signal in DESIGNER_CLASS_SIGNAL_PORTS.get(
                    class_name, ()):
                if not any(port.name == name for port in outputs):
                    outputs.append(Port(
                        name, "action", label=label, kind="event",
                        hint=f"Событие импортированного {class_name}: {signal}",
                        signal=signal))
            dynamic = replace(
                spec, inputs=list(spec.inputs), outputs=outputs,
                auto_events=dict(spec.auto_events))
            dynamic._add_gui_methods(
                GUI_CLASS_CAPABILITIES.get(class_name, ()))
            dynamic._add_inspector_properties(class_name)
            return dynamic
        # Служебные мосты контейнера получают роль и тип от конкретной
        # внешней точки. Внутри контейнера направление зеркально: внешний
        # метод становится событием моста, а внешнее событие — методом.
        if spec is not None and node.spec_key == "Container.input":
            outer_kind = str(node.params.get("port_kind") or "data")
            inner_kind = {"method": "event", "data": "property"}.get(
                outer_kind, "property")
            port_type = str(node.params.get("port_type") or "any")
            return replace(spec, outputs=[Port(
                "value", port_type, label=str(
                    node.params.get("label") or "Значение"),
                kind=inner_kind)])
        if spec is not None and node.spec_key == "Container.output":
            outer_kind = str(node.params.get("port_kind") or "property")
            inner_kind = {"event": "method", "property": "data"}.get(
                outer_kind, "data")
            port_type = str(node.params.get("port_type") or "any")
            label = str(node.params.get("label") or "Значение")
            return replace(spec,
                           inputs=[Port("value", port_type, label=label,
                                        kind=inner_kind)],
                           outputs=[Port("value", port_type, label=label,
                                         kind=outer_kind)])
        if spec is None or node.spec_key != "Container.subgraph" \
                or not node.interface:
            return spec
        # В interface также лежат чисто графические поля side/offset.
        # Они нужны рамке внутреннего редактора, но не являются аргументами Port.
        port_fields = {
            "name", "type", "default", "label", "hint", "choices",
            "minimum", "maximum", "multiline", "kind", "signal",
            "runtime_only", "runtime_getter",
            "internal", "inspector_only", "group", "editor", "advanced",
        }
        inputs = [
            Port(**{key: value for key, value in raw.items()
                    if key in port_fields})
            for raw in node.interface.get("inputs", [])
        ]
        outputs = [
            Port(**{key: value for key, value in raw.items()
                    if key in port_fields})
            for raw in node.interface.get("outputs", [])
        ]
        return replace(spec, inputs=inputs, outputs=outputs)

    def nodes_of_type(self, spec_key: str) -> List[Node]:
        return [n for n in self.nodes.values() if n.spec_key == spec_key]

    def title_of(self, node: Node) -> str:
        if node.custom_title:
            return node.custom_title
        spec = self.spec_of(node)
        return spec.title if spec else node.spec_key

    # ---------------------------------------------------------- containers
    def pack_container(self, node_ids: Iterable[str],
                       title: str = "Контейнер") -> Node:
        """Упаковывает выбранные ноды; внешние точки создаёт по границе."""
        selected = {nid for nid in node_ids if nid in self.nodes}
        if len(selected) < 2:
            raise GraphError("Для контейнера выберите минимум две ноды")
        if any(self.nodes[nid].spec_key.startswith("Container.")
               for nid in selected):
            raise GraphError("Вложенные контейнеры появятся в следующем этапе")

        incoming = [e for e in self.edges.values()
                    if e.src_node not in selected and e.dst_node in selected]
        outgoing = [e for e in self.edges.values()
                    if e.src_node in selected and e.dst_node not in selected]
        output_sources = []
        for edge in outgoing:
            key = (edge.src_node, edge.src_port)
            if key not in output_sources:
                output_sources.append(key)
        inner_data = {
            "version": self.VERSION,
            "meta": {"name": str(title), "notes": "Внутренняя схема контейнера"},
            "nodes": [self.nodes[nid].as_dict() for nid in selected],
            "edges": [e.as_dict() for e in self.edges.values()
                      if e.src_node in selected and e.dst_node in selected],
        }
        inner = Graph.from_dict(inner_data, self.specs)
        input_defs = []
        output_defs = []
        for index, edge in enumerate(incoming, 1):
            dst = self.nodes[edge.dst_node]
            dst_spec = self.spec_of(dst)
            dst_port = dst_spec.input(edge.dst_port)
            label = f"{dst_spec.title}: {dst_port.label}"
            input_defs.append(Port(
                f"in{index}", dst_port.type, label=label,
                hint=f"В контейнере подключено к «{label}»",
                kind=dst_port.kind).as_dict())
            bridge = inner.add_node(
                "Container.input", dst.x - 240, dst.y,
                {"index": index, "port_name": f"in{index}", "label": label,
                 "port_type": dst_port.type, "port_kind": dst_port.kind},
                f"container_in_{index}")
            bridge.custom_title = f"ВНЕШНИЙ ВХОД {index}: {label}"
            bridge.width = 250.0
            inner.add_edge(bridge.id, "value", dst.id, edge.dst_port)
        for index, (src_id, src_port_name) in enumerate(output_sources, 1):
            src = self.nodes[src_id]
            src_spec = self.spec_of(src)
            src_port = src_spec.output(src_port_name)
            label = f"{src_spec.title}: {src_port.label}"
            output_defs.append(Port(
                f"out{index}", src_port.type, label=label,
                hint=f"В контейнере приходит из «{label}»",
                kind=src_port.kind).as_dict())
            bridge = inner.add_node(
                "Container.output", src.x + 280, src.y,
                {"index": index, "port_name": f"out{index}", "label": label,
                 "port_type": src_port.type, "port_kind": src_port.kind},
                f"container_out_{index}")
            bridge.custom_title = f"ВНЕШНИЙ ВЫХОД {index}: {label}"
            bridge.width = 250.0
            inner.add_edge(src.id, src_port_name, bridge.id, "value")

        min_x = min(self.nodes[nid].x for nid in selected)
        min_y = min(self.nodes[nid].y for nid in selected)
        for nid in list(selected):
            self.remove_node(nid)
        container = self.add_node("Container.subgraph", min_x, min_y)
        container.custom_title = f"{title} ({len(selected)} нод)"
        container.width = 300.0
        container.subgraph = inner.to_dict()
        container.interface = {
            "inputs": input_defs, "outputs": output_defs,
            "node_count": len(selected),
        }

        for index, edge in enumerate(incoming, 1):
            self.add_edge(edge.src_node, edge.src_port,
                          container.id, f"in{index}")
        source_to_index = {
            source: index for index, source in enumerate(output_sources, 1)}
        for edge in outgoing:
            index = source_to_index[(edge.src_node, edge.src_port)]
            self.add_edge(container.id, f"out{index}",
                          edge.dst_node, edge.dst_port)
        return container

    def unpack_container(self, container_id: str) -> List[str]:
        """Возвращает содержимое контейнера на основное полотно."""
        container = self.nodes.get(container_id)
        if container is None or container.spec_key != "Container.subgraph":
            raise GraphError("Выбранная нода не является контейнером")
        inner = Graph.from_dict(container.subgraph, self.specs)
        incoming = list(self.edges_into(container_id))
        outgoing = [e for e in self.edges.values()
                    if e.src_node == container_id]

        input_targets = {}
        output_sources = {}
        for bridge in inner.nodes.values():
            if bridge.spec_key == "Container.input":
                index = int(bridge.params.get("index", 1) or 1)
                name = bridge.params.get("port_name") or f"in{index}"
                input_targets[name] = [
                    (e.dst_node, e.dst_port) for e in inner.edges.values()
                    if e.src_node == bridge.id]
            elif bridge.spec_key == "Container.output":
                index = int(bridge.params.get("index", 1) or 1)
                name = bridge.params.get("port_name") or f"out{index}"
                source = inner.edges_into(bridge.id, "value")
                if source:
                    output_sources[name] = (
                        source[0].src_node, source[0].src_port)

        regular = [n for n in inner.nodes.values()
                   if not n.spec_key.startswith("Container.")]
        regular_ids = {n.id for n in regular}
        self.remove_node(container_id)
        for item in regular:
            if item.id in self.nodes:
                raise GraphError(f"Конфликт идентификатора {item.id}")
            self.nodes[item.id] = item
        for edge in inner.edges.values():
            if edge.src_node in regular_ids and edge.dst_node in regular_ids:
                self.add_edge(edge.src_node, edge.src_port,
                              edge.dst_node, edge.dst_port, edge.id)
        for edge in incoming:
            for dst_node, dst_port in input_targets.get(edge.dst_port, []):
                self.add_edge(edge.src_node, edge.src_port, dst_node, dst_port)
        for edge in outgoing:
            source = output_sources.get(edge.src_port)
            if source:
                self.add_edge(source[0], source[1],
                              edge.dst_node, edge.dst_port)
        return [n.id for n in regular]

    # --------------------------------------------------------------- edges
    def edges_into(self, node_id: str, port: Optional[str] = None) -> List[Edge]:
        return [e for e in self.edges.values()
                if e.dst_node == node_id and (port is None or e.dst_port == port)]

    def edge_into(self, node_id: str, port: str) -> Optional[Edge]:
        found = self.edges_into(node_id, port)
        return found[0] if found else None

    def edges_of(self, node_id: str) -> List[Edge]:
        return [e for e in self.edges.values()
                if e.src_node == node_id or e.dst_node == node_id]

    def can_connect(self, src_node: str, src_port: str,
                    dst_node: str, dst_port: str) -> Tuple[bool, str]:
        """Проверяет связь и возвращает (можно, причина)."""
        src = self.nodes.get(src_node)
        dst = self.nodes.get(dst_node)
        if src is None or dst is None:
            return False, "Нода не найдена"
        if src_node == dst_node:
            return False, "Нельзя соединить ноду с самой собой"
        src_spec, dst_spec = self.spec_of(src), self.spec_of(dst)
        if not src_spec or not dst_spec:
            return False, "Неизвестный тип ноды"
        out_port = src_spec.output(src_port)
        in_port = dst_spec.input(dst_port)
        if out_port is None:
            return False, f"Нет выхода '{src_port}'"
        if in_port is None:
            return False, f"Нет входа '{dst_port}'"
        # Событие без payload (action/any) может только запустить любой метод.
        # Событие с payload обязано совпасть с типом метода: поэтому числовой
        # onPosition больше не «прилипает» к Показать/Скрыть окно.
        trigger_without_value = (
            out_port.kind == "event" and in_port.kind == "method"
            and out_port.type in ("action", "any"))
        event_payload = (
            out_port.kind == "event" and in_port.kind == "method"
            and not trigger_without_value)
        payload_compatible = (
            out_port.type == in_port.type or in_port.type == "any")
        compatible = (
            payload_compatible if event_payload
            else types_compatible(out_port.type, in_port.type))
        if not trigger_without_value and not compatible:
            return False, (f"Типы не совпадают: "
                           f"{out_port.type} → {in_port.type}")
        expected = {
            "event": "method",
            "property": "data",
        }.get(out_port.kind)
        if expected != in_port.kind:
            # Списковые сборщики остаются переходником: они могут собирать
            # управляющие описатели вместе с обычными значениями.
            list_adapter = in_port.kind == "data" and in_port.type == "list"
            if not list_adapter:
                return False, (
                    "Несовместимые стороны: "
                    f"{out_port.kind or 'выход'} → "
                    f"{in_port.kind or 'вход'}. "
                    "Событие соединяется с методом, "
                    "свойство — с данными.")
        if in_port.type not in ("list", "actions", "events") \
                and self.edge_into(dst_node, dst_port):
            return False, "Вход уже занят (множественные связи — только у списков)"
        # Синхронный событийный runtime допускает управляющие циклы.
        # Цикл ленивых данных, напротив, не имеет корректного значения.
        if out_port.kind == "property" and self._creates_data_cycle(
                src_node, dst_node):
            return False, "Связь создаст цикл"
        return True, ""

    def add_edge(self, src_node: str, src_port: str,
                 dst_node: str, dst_port: str,
                 edge_id: Optional[str] = None,
                 line_style: str = "curve",
                 bends: Optional[List[List[float]]] = None) -> Edge:
        ok, reason = self.can_connect(src_node, src_port, dst_node, dst_port)
        if not ok:
            raise GraphError(reason)
        edge = Edge(id=edge_id or self.new_id("e"), src_node=src_node,
                    src_port=src_port, dst_node=dst_node, dst_port=dst_port,
                    line_style=(line_style if line_style in (
                        "curve", "orthogonal") else "curve"),
                    bends=list(bends or []))
        self.edges[edge.id] = edge
        return edge

    def remove_edge(self, edge_id: str) -> None:
        self.edges.pop(edge_id, None)

    def _creates_data_cycle(self, src_node: str, dst_node: str) -> bool:
        """Появится ли цикл среди связей свойство → данные."""
        stack = [src_node]
        seen = set()
        while stack:
            current = stack.pop()
            if current == dst_node:
                return True
            if current in seen:
                continue
            seen.add(current)
            for edge in self.edges_into(current):
                source = self.nodes.get(edge.src_node)
                target = self.nodes.get(edge.dst_node)
                if not source or not target:
                    continue
                source_spec = self.spec_of(source)
                target_spec = self.spec_of(target)
                out_port = source_spec.output(edge.src_port) if source_spec else None
                in_port = target_spec.input(edge.dst_port) if target_spec else None
                if (out_port and in_port and out_port.kind == "property"
                        and in_port.kind == "data"):
                    stack.append(edge.src_node)
        return False

    # ---------------------------------------------------------- evaluation
    def topological_order(self) -> List[str]:
        """Порядок вычисления нод (сначала источники)."""
        incoming = {nid: set() for nid in self.nodes}
        outgoing = {nid: set() for nid in self.nodes}
        for edge in self.edges.values():
            if edge.src_node in self.nodes and edge.dst_node in self.nodes:
                source = self.nodes[edge.src_node]
                target = self.nodes[edge.dst_node]
                source_spec = self.spec_of(source)
                target_spec = self.spec_of(target)
                out_port = source_spec.output(edge.src_port) if source_spec else None
                in_port = target_spec.input(edge.dst_port) if target_spec else None
                if not (out_port and in_port and out_port.kind == "property"
                        and in_port.kind == "data"):
                    continue
                incoming[edge.dst_node].add(edge.src_node)
                outgoing[edge.src_node].add(edge.dst_node)
        ready = sorted(nid for nid, deps in incoming.items() if not deps)
        order: List[str] = []
        while ready:
            current = ready.pop(0)
            order.append(current)
            for nxt in sorted(outgoing[current]):
                incoming[nxt].discard(current)
                if not incoming[nxt]:
                    ready.append(nxt)
                    ready.sort()
        if len(order) != len(self.nodes):
            raise GraphError("В графе есть цикл — вычисление невозможно")
        return order

    def _collect_input(self, node: Node, port: Port) -> Any:
        """Собирает значение входа: из связей или из параметров."""
        connected = self.edges_into(node.id, port.name)
        if not connected:
            return node.params.get(port.name, port.default)
        values = []
        for edge in connected:
            src = self.nodes.get(edge.src_node)
            if src is None:
                continue
            values.append(src.results.get(edge.src_port))
        if port.type in ("list", "actions", "events"):
            flat: List[Any] = []
            for value in values:
                if isinstance(value, (list, tuple)):
                    flat.extend(value)
                elif value is not None:
                    flat.append(value)
            return flat
        return values[0] if values else node.params.get(port.name, port.default)

    def evaluate(self) -> Dict[str, Dict[str, Any]]:
        """Вычисляет весь граф. Ошибка одной ноды не ломает остальные."""
        self.log = []
        results: Dict[str, Dict[str, Any]] = {}
        for node in self.nodes.values():
            node.results, node.error, node.traceback = {}, "", ""
            node.duration_ms = 0.0
        for node_id in self.topological_order():
            node = self.nodes[node_id]
            spec = self.spec_of(node)
            if spec is None:
                node.error = f"Неизвестный тип ноды: {node.spec_key}"
                self.log.append(f"[{node_id}] {node.error}")
                continue
            if node.disabled:
                self.log.append(f"[{node_id}] {spec.title}: отключена")
                continue
            kwargs = {}
            for port in spec.inputs:
                if (port.kind != "data" or port.runtime_only
                        or port.inspector_only):
                    continue
                value = self._collect_input(node, port)
                # Живое свойство GUI является выражением времени выполнения.
                # Статический конструктор виджета получает исходное значение,
                # а сама связь компилируется ниже в реактивный Qt binding.
                if (isinstance(value, dict)
                        and value.get("kind") == "expression"
                        and spec.key.startswith(
                            ("Gui.", "GuiQt.", "Layout.", "Window."))):
                    value = node.params.get(port.name, port.default)
                kwargs[port.name] = value
            started = time.perf_counter()
            try:
                if node.spec_key == "Container.input":
                    raw = node.params.get("value")
                elif node.spec_key == "Container.subgraph":
                    raw = self._evaluate_container(node, kwargs, spec)
                else:
                    raw = spec.fn(**kwargs) if spec.fn else None
                node.results = self._normalize(spec, raw)
                self._apply_imported_ui_state(node)
                self._apply_component_properties(node)
                self._attach_gui_runtime_properties(node, spec)
                node.duration_ms = (time.perf_counter() - started) * 1000.0
                results[node_id] = node.results
                self.log.append(
                    f"[{node_id}] {spec.title}: "
                    f"{', '.join(f'{k}={v!r}' for k, v in node.results.items())}"
                    f" ({node.duration_ms:.1f} мс)")
            except Exception as exc:  # noqa: BLE001 — изоляция ошибок ноды
                node.error = f"{type(exc).__name__}: {exc}"
                node.traceback = _tb.format_exc()
                node.duration_ms = (time.perf_counter() - started) * 1000.0
                self.log.append(f"[{node_id}] {spec.title}: ОШИБКА — {node.error}")
        self._attach_implicit_gui()
        self._attach_reactive_bindings()
        self._attach_flow_bindings()
        return results

    @staticmethod
    def _visual_value(node: Node) -> Optional[Dict[str, Any]]:
        """Возвращает внутреннее описание GUI-объекта ноды."""
        return next((
            value for value in node.results.values()
            if isinstance(value, dict)
            and value.get("kind") in ("widget", "layout")), None)

    @staticmethod
    def _auto_layout(children: Sequence[Dict[str, Any]],
                     name: str = "auto_main_layout") -> Dict[str, Any]:
        return {
            "kind": "layout", "cls": "QVBoxLayout", "name": name,
            "children": list(children),
            "calls": [
                "setContentsMargins(12, 12, 12, 12)",
                "setSpacing(8)",
            ],
            "grid": [], "form": [],
        }

    @staticmethod
    def _auto_form(children: Sequence[Dict[str, Any]],
                   name: str = "auto_form") -> Dict[str, Any]:
        """Абсолютная форма HiAsm: виджеты живут по Left/Top/Width/Height."""
        return {
            "kind": "widget", "cls": "QWidget", "module": "QtWidgets",
            "name": name, "calls": [], "content": None,
            "children": list(children), "tabs": [], "tooltip": "",
            "stylesheet": "", "helper": None,
            "extra": {"absolute_container": True},
        }

    @staticmethod
    def _contains_visual_name(value: Any, name: str) -> bool:
        """Есть ли именованный GUI-объект внутри дерева интерфейса."""
        if isinstance(value, dict):
            if value.get("name") == name \
                    and value.get("kind") in ("widget", "layout"):
                return True
            return any(Graph._contains_visual_name(item, name)
                       for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(Graph._contains_visual_name(item, name)
                       for item in value)
        return False

    def _attach_implicit_gui(self) -> None:
        """Автоматически помещает GUI-ноды в окно, как в HiAsm.

        Существующие структурные связи старых проектов и импорта .ui
        продолжают задавать точную вложенность, но больше не отображаются.
        Любой не подключённый визуальный элемент автоматически становится
        содержимым окна. Поэтому для появления кнопки, поля или надписи линия
        ``Widget -> Layout -> Window`` больше не нужна.
        """
        windows = []
        visuals: Dict[str, Dict[str, Any]] = {}
        for node in self.nodes.values():
            for value in node.results.values():
                if isinstance(value, dict) and value.get("kind") == "window":
                    windows.append((node, value))
                    break
            visual = self._visual_value(node)
            if visual is not None:
                visuals[node.id] = visual
        if not windows or not visuals:
            return

        # Источники структурных линий, уже вложенные в другой GUI-объект,
        # не должны второй раз появляться на верхнем уровне.
        nested = set()
        assigned_to_window: Dict[str, set] = {}
        for edge in self.edges.values():
            source = self.nodes.get(edge.src_node)
            target = self.nodes.get(edge.dst_node)
            if source is None or target is None or edge.src_node not in visuals:
                continue
            target_spec = self.spec_of(target)
            target_port = target_spec.input(edge.dst_port) if target_spec else None
            if target_port is None or not target_port.internal:
                continue
            if target.spec_key in WINDOW_RUNTIME_KEYS:
                assigned_to_window.setdefault(target.id, set()).add(edge.src_node)
            elif edge.dst_node in visuals:
                nested.add(edge.src_node)

        roots = [
            (node_id, value) for node_id, value in visuals.items()
            if node_id not in nested
        ]

        # Новые свободные элементы не должны лежать друг на друге. Пока
        # пользователь не задал Left/Top в инспекторе, раскладываем их
        # стартовой сеткой; затем координаты становятся обычными свойствами.
        auto_widgets = [
            (node_id, value) for node_id, value in roots
            if value.get("kind") == "widget"
            and not (self.nodes[node_id].ui_state or {}).get(
                "designer_params")
            and int(self.nodes[node_id].params.get("geometry_x", 20) or 20) == 20
            and int(self.nodes[node_id].params.get("geometry_y", 20) or 20) == 20
        ]
        if len(auto_widgets) > 1:
            from python_library.gui_properties import apply_properties
            for index, (node_id, value) in enumerate(auto_widgets):
                item = self.nodes[node_id]
                item.params["geometry_x"] = 20 + (index % 3) * 160
                item.params["geometry_y"] = 20 + (index // 3) * 64
                apply_properties(value, item.params)

        # Если пользователь добавил ровно один пустой layout, он естественно
        # становится автоматическим контейнером всех свободных виджетов.
        empty_layouts = [
            (node_id, value) for node_id, value in roots
            if value.get("kind") == "layout"
            and not value.get("children")
            and not value.get("grid")
            and not value.get("form")
        ]
        root_widgets = [
            (node_id, value) for node_id, value in roots
            if value.get("kind") == "widget"
        ]
        if len(empty_layouts) == 1 and root_widgets:
            layout_id, layout = empty_layouts[0]
            layout["children"] = [value for unused_id, value in root_widgets]
            nested.update(node_id for node_id, unused_value in root_widgets)
            roots = [
                (node_id, value) for node_id, value in roots
                if node_id == layout_id or node_id not in nested
            ]

        # При нескольких окнах свободные элементы относятся к ближайшему на
        # схеме. Для обычного проекта с одним окном все GUI-ноды входят в него.
        groups: Dict[str, List[Dict[str, Any]]] = {
            node.id: [] for node, unused_window in windows}
        for node_id, value in roots:
            explicit = [
                window_node for window_node, unused_window in windows
                if node_id in assigned_to_window.get(window_node.id, set())
            ]
            if explicit:
                owner = explicit[0]
            elif len(windows) == 1:
                owner = windows[0][0]
            else:
                source = self.nodes[node_id]
                owner = min(
                    (item[0] for item in windows),
                    key=lambda item: (
                        (item.x - source.x) ** 2 + (item.y - source.y) ** 2))
            groups[owner.id].append(value)

        for window_node, window in windows:
            current = window.get("content")
            additions = groups.get(window_node.id, [])
            if current is None:
                if len(additions) == 1 \
                        and additions[0].get("kind") == "layout":
                    window["content"] = additions[0]
                elif additions:
                    window["content"] = self._auto_form(
                        additions, f"auto_{window_node.id}_layout")
                continue
            # Явно подключённый корень уже находится в current.
            extras = [
                value for value in additions if value is not current
            ]
            if not extras:
                continue
            if current.get("kind") == "layout":
                current.setdefault("children", []).extend(extras)
            elif (current.get("kind") == "widget"
                  and (current.get("extra") or {}).get(
                      "absolute_container")):
                current.setdefault("children", []).extend(extras)
            else:
                window["content"] = self._auto_form(
                    [current, *extras], f"auto_{window_node.id}_layout")

    @staticmethod
    def _reactive_signal(spec: NodeSpec, port: Port) -> str:
        """Сигнал Qt, который сообщает об изменении живого свойства."""
        preferred = {
            "value": ("valueChanged",),
            "index": ("currentIndexChanged", "currentChanged"),
            "checked": ("toggled", "stateChanged"),
            "text": ("textChanged", "currentTextChanged"),
        }.get(port.runtime_getter, ())
        signals = [item.signal for item in spec.outputs
                   if item.kind == "event" and item.signal]
        return next((name for name in preferred if name in signals), "")

    def _reactive_action(self, node: Node, port_name: str,
                         value_code: str) -> Optional[Dict[str, Any]]:
        """Строит setter для прямой линии «свойство → параметр GUI»."""
        target = next((
            value for value in node.results.values()
            if isinstance(value, dict)
            and value.get("kind") in ("widget", "layout", "window")), None)
        if target is None:
            return None
        kind = target.get("kind")
        name = target.get("name")
        if kind != "window" and not name:
            return None
        ref = "self" if kind == "window" else f"self.{name}"
        expression = ""
        if kind == "window":
            setters = {
                "title": f"{ref}.setWindowTitle(str({value_code}))",
                "width": (
                    f"{ref}.resize(max(1, int({value_code})), "
                    f"{ref}.height())"),
                "height": (
                    f"{ref}.resize({ref}.width(), "
                    f"max(1, int({value_code})))"),
                "style": f"{ref}.setStyleSheet(str({value_code}))",
                "statusbar": (
                    f"{ref}.statusBar().showMessage(str({value_code}))"),
            }
            expression = setters.get(port_name, "")
        elif kind == "layout":
            if port_name == "spacing":
                expression = f"{ref}.setSpacing(int({value_code}))"
            elif port_name == "margin":
                expression = (
                    f"_nf_margin = int({value_code})\n"
                    f"{ref}.setContentsMargins(_nf_margin, _nf_margin, "
                    "_nf_margin, _nf_margin)")
        else:
            cls = str(target.get("cls") or "")
            if port_name in ("text", "value"):
                if port_name == "value" and cls in (
                        "QSpinBox", "QDoubleSpinBox", "QSlider", "QDial",
                        "QScrollBar", "QProgressBar", "QLCDNumber"):
                    method = "display" if cls == "QLCDNumber" else "setValue"
                    expression = f"{ref}.{method}({value_code})"
                else:
                    expression = f"set_text({ref}, str({value_code}))"
            elif port_name == "title" and cls == "QGroupBox":
                expression = f"{ref}.setTitle(str({value_code}))"
            elif port_name == "placeholder":
                expression = f"{ref}.setPlaceholderText(str({value_code}))"
            elif port_name in ("checked", "enabled", "visible"):
                method = {
                    "checked": "setChecked",
                    "enabled": "setEnabled",
                    "visible": "setVisible",
                }[port_name]
                expression = f"{ref}.{method}(bool({value_code}))"
            elif port_name == "width":
                expression = f"{ref}.setFixedWidth(max(1, int({value_code})))"
            elif port_name == "height":
                expression = f"{ref}.setFixedHeight(max(1, int({value_code})))"
            elif port_name == "style":
                expression = f"{ref}.setStyleSheet(str({value_code}))"
        if not expression:
            return None
        return {
            "kind": "action", "code": expression, "imports": [],
            "label": f"reactive:{port_name}",
        }

    def _attach_reactive_bindings(self) -> None:
        """Компилирует одну линию свойства в автоматическое обновление GUI."""
        windows = [
            value for node in self.nodes.values()
            for value in node.results.values()
            if isinstance(value, dict) and value.get("kind") == "window"
        ]
        if not windows:
            return
        for edge in self.edges.values():
            source = self.nodes.get(edge.src_node)
            target = self.nodes.get(edge.dst_node)
            if source is None or target is None:
                continue
            source_spec = self.spec_of(source)
            target_spec = self.spec_of(target)
            if source_spec is None or target_spec is None:
                continue
            source_port = source_spec.output(edge.src_port)
            target_port = target_spec.input(edge.dst_port)
            if (source_port is None or target_port is None
                    or source_port.kind != "property"
                    or not source_port.runtime_getter
                    or target_port.kind != "data"
                    or target_port.internal):
                continue
            source_widget = self._visual_value(source)
            if source_widget is None or not source_widget.get("name"):
                continue
            signal = self._reactive_signal(source_spec, source_port)
            if not signal:
                continue
            expression = source.results.get(edge.src_port)
            if not isinstance(expression, dict) \
                    or expression.get("kind") != "expression":
                continue
            action = self._reactive_action(
                target, edge.dst_port, str(expression.get("code") or "None"))
            if action is None:
                continue
            binding = {
                "kind": "binding",
                "widget": source_widget["name"],
                "signal": signal,
                "slot": (
                    f"on_reactive_{source_widget['name']}_"
                    f"{edge.dst_node}_{edge.dst_port}_{edge.id}"),
                "actions": [action],
            }
            target_visual = next((
                value for value in target.results.values()
                if isinstance(value, dict)
                and value.get("kind") in ("widget", "layout", "window")),
                None)
            if target_visual and target_visual.get("kind") == "window":
                recipients = [target_visual]
            elif target_visual and target_visual.get("name"):
                recipients = [
                    window for window in windows
                    if self._contains_visual_name(
                        window.get("content"), target_visual["name"])
                ]
            else:
                recipients = windows
            for window in recipients:
                bindings = window.setdefault("bindings", [])
                if binding not in bindings:
                    bindings.append(binding)
                initial = window.setdefault("initial_actions", [])
                if action not in initial:
                    initial.append(action)

    def _attach_flow_bindings(self) -> None:
        """Компилирует GUI-событие → боковую цепочку в Qt binding."""
        windows = []
        for node in self.nodes.values():
            for value in node.results.values():
                if isinstance(value, dict) and value.get("kind") == "window":
                    windows.append(value)
        if not windows:
            return
        for edge in self.edges.values():
            source = self.nodes.get(edge.src_node)
            if source is None:
                continue
            widget = next((value for value in source.results.values()
                           if isinstance(value, dict)
                           and value.get("kind") == "widget"), None)
            if not widget or not widget.get("name"):
                continue
            source_spec = self.spec_of(source)
            source_port = (source_spec.output(edge.src_port)
                           if source_spec else None)
            signal = source_port.signal if source_port else None
            if not source_port or source_port.kind != "event" or not signal:
                continue
            actions = []
            stack = [(edge.dst_node, edge.dst_port)]
            seen = set()
            while stack:
                node_id, method_name = stack.pop(0)
                marker = (node_id, method_name)
                if marker in seen:
                    continue
                seen.add(marker)
                item = self.nodes.get(node_id)
                if item is None:
                    continue
                signal_value = self._signal_value_for_method(
                    signal, method_name)
                method_action = self._gui_method_action(
                    item, method_name, signal_value)
                if method_action:
                    actions.append(method_action)
                for value in item.results.values():
                    candidates = value if isinstance(value, list) else [value]
                    for candidate in candidates:
                        if (isinstance(candidate, dict)
                                and candidate.get("kind") == "action"):
                            actions.append(candidate)
                item_spec = self.spec_of(item)
                allowed_events = set(
                    item_spec.auto_events.get(method_name, [])
                    if item_spec else [])
                for following in self.edges.values():
                    if following.src_node != node_id:
                        continue
                    if allowed_events and following.src_port not in allowed_events:
                        continue
                    target = self.nodes.get(following.dst_node)
                    target_spec = self.spec_of(target) if target else None
                    out_port = (item_spec.output(following.src_port)
                                if item_spec else None)
                    in_port = (target_spec.input(following.dst_port)
                               if target_spec else None)
                    if (out_port and in_port and out_port.kind == "event"
                            and in_port.kind == "method"):
                        stack.append((following.dst_node, following.dst_port))
            binding = {
                "kind": "binding", "widget": widget["name"],
                "signal": signal,
                "slot": f"on_flow_{widget['name']}_{signal}_{edge.id}",
                "actions": actions,
            }
            for window in windows:
                bindings = window.setdefault("bindings", [])
                if binding not in bindings:
                    bindings.append(binding)

    @staticmethod
    def _code_of_runtime_value(value: Any) -> Tuple[str, List[str]]:
        if isinstance(value, dict) and value.get("kind") == "expression":
            return (str(value.get("code") or "None"),
                    list(value.get("imports") or []))
        return repr(value), []

    @staticmethod
    def _signal_value_for_method(signal: str, method_name: str) -> str:
        """Разрешает боковой линии передать payload Qt прямо в метод."""
        compatible = {
            "valueChanged": {
                "doSetValue", "doDisplay", "doSetIndex",
                "doSetWidth", "doSetHeight", "doSetSpacing",
            },
            "currentIndexChanged": {"doSetIndex", "doSetValue"},
            "currentChanged": {"doSetIndex", "doSetValue"},
            "textChanged": {"doSetText", "doSetTitle"},
            "currentTextChanged": {"doSetText", "doSetTitle"},
            "toggled": {"doSetChecked", "doEnabled", "doVisible"},
            "stateChanged": {"doSetChecked", "doEnabled", "doVisible"},
        }
        return ("_nf_signal_value"
                if method_name in compatible.get(str(signal), set()) else "")

    def _gui_method_action(self, node: Node, method_name: str,
                           event_value_code: str = "") -> Optional[Dict[str, Any]]:
        """Превращает метод GUI/окна/layout в действие генератора PyQt."""
        target = next((
            value for value in node.results.values()
            if isinstance(value, dict)
            and value.get("kind") in ("widget", "layout", "window")), None)
        if not target:
            return None
        kind = target.get("kind")
        name = target.get("name")
        if kind != "window" and not name:
            return None
        ref = "self" if kind == "window" else f"self.{name}"
        spec = self.spec_of(node)
        if spec is None or not spec.input(method_name) \
                or spec.input(method_name).kind != "method":
            return None
        definitions = {
            "doSetText": ("MethodText", "set_text({target}, str({value}))"),
            "doSetValue": ("MethodValue", "{target}.setValue({value})"),
            "doDisplay": ("MethodValue", "{target}.display({value})"),
            "doSetIndex": (
                "MethodIndex", "{target}.setCurrentIndex(int({value}))"),
            "doSetChecked": (
                "MethodChecked", "{target}.setChecked(bool({value}))"),
            "doEnabled": (
                "MethodEnabled", "{target}.setEnabled(bool({value}))"),
            "doVisible": (
                "MethodVisible", "{target}.setVisible(bool({value}))"),
            "doAddItem": (
                "MethodText", "{target}.addItem(str({value}))"),
            "doClear": ("", "{target}.clear()"),
            "doShow": ("", "{target}.show()"),
            "doHide": ("", "{target}.hide()"),
            "doClose": ("", "{target}.close()"),
            "doSetTitle": (
                "MethodTitle", "{target}.setWindowTitle(str({value}))"),
            "doSetWidth": ("MethodWidth", ""),
            "doSetHeight": ("MethodHeight", ""),
            "doResize": ("MethodWidth", ""),
            "doSetSpacing": (
                "MethodSpacing", "{target}.setSpacing(int({value}))"),
            "doSetMargins": ("MethodMargin", ""),
        }
        definition = definitions.get(method_name)
        if definition is None:
            return None
        data_name, template = definition
        imports: List[str] = []
        value_code = "None"
        if data_name:
            if event_value_code:
                value_code = event_value_code
            else:
                port = spec.input(data_name)
                value = self._collect_input(node, port) if port else None
                value_code, imports = self._code_of_runtime_value(value)
        if method_name == "doResize":
            height = spec.input("MethodHeight")
            height_value = self._collect_input(node, height) if height else 600
            height_code, height_imports = self._code_of_runtime_value(
                height_value)
            imports.extend(height_imports)
            expression = (
                f"{ref}.resize(int({value_code}), int({height_code}))")
        elif method_name == "doSetWidth":
            expression = (
                f"{ref}.resize(max(1, int({value_code})), {ref}.height())")
        elif method_name == "doSetHeight":
            expression = (
                f"{ref}.resize({ref}.width(), max(1, int({value_code})))")
        elif method_name == "doSetMargins":
            expression = (
                f"_nf_margin = int({value_code})\n"
                f"{ref}.setContentsMargins("
                "_nf_margin, _nf_margin, _nf_margin, _nf_margin)")
        else:
            expression = template.format(
                target=ref, value=value_code)
        return {
            "kind": "action", "code": expression,
            "imports": imports, "label": method_name,
        }

    def _evaluate_container(self, node: Node, kwargs: Dict[str, Any],
                            spec: NodeSpec) -> Any:
        """Вычисляет вложенную статическую схему как одну ноду."""
        if not node.subgraph:
            return [None for _ in spec.outputs]
        inner = Graph.from_dict(node.subgraph, self.specs)
        for item in inner.nodes.values():
            if item.spec_key == "Container.input":
                index = int(item.params.get("index", 1) or 1)
                name = item.params.get("port_name") or f"in{index}"
                item.params["value"] = kwargs.get(name)
        inner.evaluate()
        values = {}
        errors = []
        for item in inner.nodes.values():
            if item.error:
                errors.append(f"{inner.title_of(item)}: {item.error}")
            if item.spec_key == "Container.output":
                index = int(item.params.get("index", 1) or 1)
                name = item.params.get("port_name") or f"out{index}"
                values[name] = item.results.get("value")
        if errors:
            raise GraphError("Внутри контейнера: " + "; ".join(errors))
        ordered = [values.get(port.name) for port in spec.outputs
                   if port.kind == "property"]
        return ordered[0] if len(ordered) == 1 else ordered

    @staticmethod
    def _normalize(spec: NodeSpec, raw: Any) -> Dict[str, Any]:
        """Приводит результат функции к словарю {имя выхода: значение}."""
        names = [p.name for p in spec.outputs
                 if p.kind == "property" and not p.runtime_getter]
        if not names:
            result = {}
        elif isinstance(raw, dict) and set(raw).issubset(set(names)):
            result = {name: raw.get(name) for name in names}
        elif len(names) == 1:
            result = {names[0]: raw}
        elif isinstance(raw, (list, tuple)):
            result = {name: (raw[i] if i < len(raw) else None)
                      for i, name in enumerate(names)}
        else:
            result = {names[0]: raw}
        for name, unused_label, signal in GUI_SIGNAL_PORTS.get(spec.key, ()):
            if any(port.name == name for port in spec.outputs):
                result[name] = {
                    "kind": "flow_signal", "signal": signal,
                    "node": spec.key}
        primary = HIASM_PRIMARY_SIGNALS.get(spec.key)
        if primary and any(port.name == primary[0] for port in spec.outputs):
            result[primary[0]] = {
                "kind": "flow_signal", "signal": primary[2],
                "node": spec.key}
        return result

    @staticmethod
    def _attach_gui_runtime_properties(node: Node, spec: NodeSpec) -> None:
        """Добавляет свойства живого виджета, окна или layout."""
        target = next((
            value for value in node.results.values()
            if isinstance(value, dict)
            and value.get("kind") in ("widget", "layout", "window")), None)
        if not target:
            return
        kind = target.get("kind")
        name = target.get("name")
        if kind != "window" and not name:
            return
        ref = "self" if kind == "window" else f"self.{name}"
        getters = {
            "text": f"get_text({ref})",
            "value": f"{ref}.value()",
            "index": f"{ref}.currentIndex()",
            "checked": f"{ref}.isChecked()",
            "enabled": f"{ref}.isEnabled()",
            "visible": f"{ref}.isVisible()",
            "window_title": f"{ref}.windowTitle()",
            "width": f"{ref}.width()",
            "height": f"{ref}.height()",
            "layout_count": f"{ref}.count()",
        }
        for port in spec.outputs:
            if port.kind != "property" or not port.runtime_getter:
                continue
            code = getters.get(port.runtime_getter)
            if code:
                node.results[port.name] = {
                    "kind": "expression", "code": code,
                    "imports": [], "label": port.label,
                }

    def _apply_imported_ui_state(self, node: Node) -> None:
        """Накладывает полные свойства .ui на конкретную GUI-ноду."""
        state = node.ui_state or {}
        params = state.get("designer_params")
        generic = self.specs.get("Gui.designer_widget")
        if not isinstance(params, dict) or generic is None or generic.fn is None:
            return
        try:
            imported = generic.fn(**params)
        except Exception:
            return
        widget = next((
            value for value in node.results.values()
            if isinstance(value, dict) and value.get("kind") == "widget"), None)
        if not widget or not isinstance(imported, dict):
            return
        widget["name"] = imported.get("name") or widget.get("name")
        calls = []
        for call in list(imported.get("calls") or []) \
                + list(widget.get("calls") or []):
            if call not in calls:
                calls.append(call)
        widget["calls"] = calls
        merged_extra = dict(imported.get("extra") or {})
        merged_extra.update(widget.get("extra") or {})
        widget["extra"] = merged_extra
        if imported.get("tooltip"):
            widget["tooltip"] = imported["tooltip"]
        if imported.get("stylesheet"):
            widget["stylesheet"] = imported["stylesheet"]

    def _apply_component_properties(self, node: Node) -> None:
        """Накладывает единый HiAsm-подобный инспектор на результат GUI."""
        from python_library.gui_properties import apply_properties, imported_values
        state = node.ui_state or {}
        designer = state.get("designer_params")
        if isinstance(designer, dict) and not state.get(
                "inspector_properties_synced"):
            values = imported_values(designer)
            spec = self.spec_of(node)
            for key, value in values.items():
                if spec is not None and spec.input(key) is not None:
                    node.params[key] = value
            state["inspector_properties_synced"] = True
            node.ui_state = state
        for value in node.results.values():
            if isinstance(value, dict) and value.get("kind") in (
                    "widget", "layout", "window"):
                apply_properties(value, node.params)

    # ------------------------------------------------------- serialization
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.VERSION,
            "meta": _jsonable(self.meta),
            "nodes": [n.as_dict() for n in self.nodes.values()],
            "edges": [e.as_dict() for e in self.edges.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any],
                  specs: Optional[Dict[str, NodeSpec]] = None) -> "Graph":
        """Терпимо читает старые схемы и мигрирует поток версии 4.0."""
        graph = cls(specs)
        graph.meta.update(data.get("meta") or {})
        skipped: List[str] = []
        for raw in data.get("nodes", []):
            spec_key = raw.get("spec") or raw.get("spec_key") or ""
            original_spec_key = spec_key
            original_params = dict(raw.get("params") or {})
            imported_class = str(original_params.get("class_name") or "")
            if spec_key == "Gui.designer_widget":
                replacement = LEGACY_DESIGNER_NODE_KEYS.get(imported_class)
                if replacement in graph.specs:
                    spec_key = replacement
            node_id = str(raw.get("id") or graph.new_id())
            if spec_key not in graph.specs:
                skipped.append(f"{node_id} ({spec_key})")
                continue
            node = Node(
                id=node_id, spec_key=spec_key,
                x=float(raw.get("x", 0.0)), y=float(raw.get("y", 0.0)),
                custom_title=str(raw.get("title", "") or ""),
                notes=str(raw.get("notes", "") or ""),
                color=str(raw.get("color", "") or ""),
                collapsed=bool(raw.get("collapsed", False)),
                disabled=bool(raw.get("disabled", False)),
                width=float(raw.get("width", 0.0) or 0.0),
                hidden_ports=list(raw.get("hidden_ports") or []),
                ui_state=dict(raw.get("ui_state") or {}),
                subgraph=dict(raw.get("subgraph") or {}),
                interface=dict(raw.get("interface") or {}),
            )
            spec = graph.specs[spec_key]
            node.params = {p.name: p.default for p in spec.inputs
                           if p.kind == "data"}
            raw_params = dict(raw.get("params") or {})
            if original_spec_key == "Gui.designer_widget" \
                    and spec_key != original_spec_key:
                generic_spec = graph.specs.get("Gui.designer_widget")
                designer_params = ({
                    port.name: port.default for port in generic_spec.inputs
                    if port.kind == "data"
                } if generic_spec else {})
                designer_params.update(original_params)
                node.ui_state = {
                    "source": "legacy_qt_designer",
                    "class_name": imported_class,
                    "designer_params": designer_params,
                }
            # class_name нужен до построения динамического интерфейса
            if spec_key == "Gui.designer_widget" \
                    and "class_name" in raw_params:
                node.params["class_name"] = raw_params["class_name"]
            effective = graph.spec_of(node)
            if effective is not None:
                for port in effective.inputs:
                    if port.kind == "data":
                        node.params.setdefault(port.name, port.default)
            if "hidden_ports" not in raw and effective is not None:
                node.hidden_ports = [
                    f"in:{port.name}" for port in effective.inputs
                    if port.runtime_only
                ]
            for key, value in raw_params.items():
                effective_port = effective.input(key) if effective else None
                if (effective_port and effective_port.kind == "data") \
                        or spec_key.startswith("Container."):
                    node.params[key] = value
            graph.nodes[node.id] = node
        for raw in data.get("edges", []):
            src = raw.get("src") or [raw.get("src_node"), raw.get("src_port")]
            dst = raw.get("dst") or [raw.get("dst_node"), raw.get("dst_port")]
            try:
                src_node, src_port = str(src[0]), str(src[1])
                dst_node, dst_port = str(dst[0]), str(dst[1])
                if src_port == LEGACY_FLOW_EVENT_NAME:
                    source = graph.nodes.get(src_node)
                    source_spec = graph.spec_of(source) if source else None
                    events = ([p.name for p in source_spec.outputs
                               if p.kind == "event"] if source_spec else [])
                    if not events:
                        raise GraphError(
                            "универсальное событие 4.0 не имеет "
                            "однозначной замены")
                    src_port = events[0]
                if dst_port == LEGACY_FLOW_METHOD_NAME:
                    target = graph.nodes.get(dst_node)
                    target_spec = graph.spec_of(target) if target else None
                    methods = ([p.name for p in target_spec.inputs
                                if p.kind == "method"] if target_spec else [])
                    if not methods:
                        raise GraphError(
                            "универсальный метод 4.0 не имеет "
                            "однозначной замены")
                    dst_port = methods[0]
                graph.add_edge(src_node, src_port, dst_node, dst_port,
                               edge_id=raw.get("id"),
                               line_style=raw.get("line_style", "curve"),
                               bends=raw.get("bends") or [])
            except (GraphError, IndexError, TypeError):
                skipped.append(f"связь {src} → {dst}")
        # Подключённая точка всегда видима, даже если старый файл сохранил её
        # скрытой или новая версия назначила ей скрытие по умолчанию.
        for edge in graph.edges.values():
            source = graph.nodes.get(edge.src_node)
            target = graph.nodes.get(edge.dst_node)
            if source:
                key = f"out:{edge.src_port}"
                source.hidden_ports = [
                    item for item in source.hidden_ports if item != key]
            if target:
                key = f"in:{edge.dst_port}"
                target.hidden_ports = [
                    item for item in target.hidden_ports if item != key]
        if skipped:
            graph.log.append("Пропущено при загрузке: " + "; ".join(skipped))
        return graph

    def clone(self) -> "Graph":
        return Graph.from_dict(self.to_dict(), self.specs)

    def stats(self) -> Dict[str, int]:
        return {"nodes": len(self.nodes), "edges": len(self.edges),
                "errors": sum(1 for n in self.nodes.values() if n.error)}


def build_specs_map(specs: Iterable[NodeSpec]) -> Dict[str, NodeSpec]:
    """Собирает словарь {ключ: NodeSpec}."""
    return {spec.key: spec for spec in specs}


def ports_summary(ports: Sequence[Port]) -> str:
    return ", ".join(f"{p.label}:{p.type}" for p in ports)
