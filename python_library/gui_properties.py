"""Единая модель свойств визуальных компонентов NodeFlow.

Свойства описываются отдельно от вычислительных портов ноды. Это позволяет
показывать полный HiAsm-подобный инспектор, не превращая каждую настройку Qt в
точку на корпусе ноды.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List


SIZE_POLICIES = [
    "Fixed", "Minimum", "Maximum", "Preferred", "Expanding",
    "MinimumExpanding", "Ignored",
]
FOCUS_POLICIES = ["NoFocus", "TabFocus", "ClickFocus", "StrongFocus", "WheelFocus"]
CURSORS = [
    "ArrowCursor", "UpArrowCursor", "CrossCursor", "WaitCursor",
    "IBeamCursor", "SizeVerCursor", "SizeHorCursor", "SizeBDiagCursor",
    "SizeFDiagCursor", "SizeAllCursor", "BlankCursor", "SplitVCursor",
    "SplitHCursor", "PointingHandCursor", "ForbiddenCursor",
    "OpenHandCursor", "ClosedHandCursor", "WhatsThisCursor", "BusyCursor",
]
ALIGNMENTS = ["left", "center", "right"]


def _p(name: str, ptype: str, default: Any, label: str, group: str,
       hint: str = "", choices: Iterable[str] | None = None,
       minimum: float | None = None, maximum: float | None = None,
       multiline: bool = False, editor: str = "", advanced: bool = False
       ) -> Dict[str, Any]:
    return {
        "name": name, "type": ptype, "default": default, "label": label,
        "group": group, "hint": hint, "choices": list(choices or []) or None,
        "minimum": minimum, "maximum": maximum, "multiline": multiline,
        "editor": editor, "advanced": advanced,
    }


def common_widget_properties() -> List[Dict[str, Any]]:
    return [
        _p("name", "text", "", "Имя объекта", "Основные",
           "Уникальное имя элемента в сгенерированном приложении."),
        _p("geometry_x", "number", 20, "Слева", "Положение",
           "Координата X внутри формы.", minimum=0),
        _p("geometry_y", "number", 20, "Сверху", "Положение",
           "Координата Y внутри формы.", minimum=0),
        _p("width", "number", 120, "Ширина", "Положение",
           "Ширина элемента.", minimum=1),
        _p("height", "number", 32, "Высота", "Положение",
           "Высота элемента.", minimum=1),
        _p("min_width", "number", 0, "Мин. ширина", "Ограничения",
           minimum=0),
        _p("min_height", "number", 0, "Мин. высота", "Ограничения",
           minimum=0),
        _p("max_width", "number", 16777215, "Макс. ширина", "Ограничения",
           minimum=0, advanced=True),
        _p("max_height", "number", 16777215, "Макс. высота", "Ограничения",
           minimum=0, advanced=True),
        _p("h_size_policy", "text", "Preferred", "Горизонтальная политика",
           "Компоновка", choices=SIZE_POLICIES),
        _p("v_size_policy", "text", "Preferred", "Вертикальная политика",
           "Компоновка", choices=SIZE_POLICIES),
        _p("enabled", "bool", True, "Доступен", "Поведение"),
        _p("visible", "bool", True, "Видим", "Поведение"),
        _p("accept_drops", "bool", False, "Принимать перетаскивание",
           "Поведение", advanced=True),
        _p("mouse_tracking", "bool", False, "Отслеживать мышь",
           "Поведение", advanced=True),
        _p("focus_policy", "text", "StrongFocus", "Фокус", "Поведение",
           choices=FOCUS_POLICIES, advanced=True),
        _p("cursor", "text", "ArrowCursor", "Курсор", "Поведение",
           choices=CURSORS, advanced=True),
        _p("tooltip", "text", "", "Подсказка", "Подсказки"),
        _p("whats_this", "text", "", "Расширенная подсказка", "Подсказки",
           multiline=True),
        _p("accessible_name", "text", "", "Имя доступности", "Доступность",
           advanced=True),
        _p("accessible_description", "text", "", "Описание доступности",
           "Доступность", multiline=True, advanced=True),
        _p("font_family", "text", "Segoe UI", "Семейство", "Шрифт"),
        _p("font_size", "number", 10, "Размер", "Шрифт", minimum=1,
           maximum=200),
        _p("font_bold", "bool", False, "Полужирный", "Шрифт"),
        _p("font_italic", "bool", False, "Курсив", "Шрифт"),
        _p("font_underline", "bool", False, "Подчёркнутый", "Шрифт"),
        _p("style", "style", "", "Таблица стилей", "Внешний вид",
           multiline=True),
    ]


def class_properties(class_name: str, key: str = "") -> List[Dict[str, Any]]:
    text_buttons = {"QPushButton", "QToolButton", "QCommandLinkButton"}
    checks = {"QCheckBox", "QRadioButton"}
    sliders = {"QSlider", "QDial", "QScrollBar"}
    text_edits = {"QTextEdit", "QPlainTextEdit", "QTextBrowser"}
    result: List[Dict[str, Any]] = []
    if class_name in text_buttons:
        result += [
            _p("text", "text", "Кнопка", "Текст", "Содержимое"),
            _p("checkable", "bool", False, "Переключаемая", "Поведение"),
            _p("checked", "bool", False, "Нажата", "Поведение"),
            _p("auto_repeat", "bool", False, "Автоповтор", "Поведение"),
            _p("auto_repeat_delay", "number", 300, "Задержка автоповтора",
               "Поведение", minimum=0, advanced=True),
            _p("auto_repeat_interval", "number", 100,
               "Интервал автоповтора", "Поведение", minimum=1,
               advanced=True),
            _p("flat", "bool", False, "Плоская", "Внешний вид"),
            _p("default_button", "bool", False, "Кнопка по умолчанию",
               "Поведение"),
            _p("icon_path", "file", "", "Значок", "Содержимое",
               editor="file"),
            _p("icon_size", "number", 16, "Размер значка", "Содержимое",
               minimum=1),
        ]
    if class_name == "QCommandLinkButton":
        result.append(_p("description", "text", "", "Описание", "Содержимое",
                         multiline=True))
    if class_name == "QLabel":
        result += [
            _p("text", "text", "Надпись", "Текст", "Содержимое",
               multiline=True),
            _p("align", "text", "left", "Выравнивание", "Текст",
               choices=ALIGNMENTS),
            _p("wrap", "bool", False, "Перенос слов", "Текст"),
            _p("indent", "number", -1, "Абзац", "Текст"),
            _p("margin", "number", 0, "Отступ текста", "Текст", minimum=0),
            _p("scaled_contents", "bool", False, "Масштабировать картинку",
               "Содержимое"),
            _p("open_external_links", "bool", False, "Открывать ссылки",
               "Поведение"),
        ]
    if class_name == "QLineEdit":
        result += [
            _p("value", "text", "", "Текст", "Содержимое"),
            _p("placeholder", "text", "", "Текст-подсказка", "Содержимое"),
            _p("read_only", "bool", False, "Только чтение", "Поведение"),
            _p("max_length", "number", 32767, "Максимальная длина",
               "Ограничения", minimum=0),
            _p("echo_mode", "text", "Normal", "Режим отображения",
               "Поведение", choices=[
                   "Normal", "NoEcho", "Password", "PasswordEchoOnEdit"]),
            _p("input_mask", "text", "", "Маска ввода", "Проверка"),
            _p("clear_button", "bool", False, "Кнопка очистки", "Поведение"),
            _p("alignment", "text", "left", "Выравнивание", "Текст",
               choices=ALIGNMENTS),
        ]
    if class_name in text_edits:
        value_name = "text" if class_name == "QPlainTextEdit" else "value"
        result += [
            _p(value_name, "text", "", "Текст", "Содержимое", multiline=True),
            _p("placeholder", "text", "", "Текст-подсказка", "Содержимое"),
            _p("read_only", "bool", False, "Только чтение", "Поведение"),
            _p("line_wrap", "bool", True, "Перенос строк", "Текст"),
            _p("tab_changes_focus", "bool", False,
               "Tab переводит фокус", "Поведение", advanced=True),
        ]
        if class_name == "QTextEdit":
            result.append(_p("accept_rich_text", "bool", True,
                             "Форматированный текст", "Текст"))
    if class_name in checks:
        result += [
            _p("text", "text", class_name[1:-6], "Текст", "Содержимое"),
            _p("checked", "bool", False, "Отмечен", "Состояние"),
        ]
        if class_name == "QCheckBox":
            result.append(_p("tristate", "bool", False,
                             "Три состояния", "Поведение"))
    if class_name in ("QComboBox", "QFontComboBox"):
        result += [
            _p("items", "list", None, "Элементы", "Данные", editor="list"),
            _p("editable", "bool", False, "Редактируемый", "Поведение"),
            _p("current_index", "number", 0, "Текущий индекс", "Состояние",
               minimum=-1),
            _p("max_visible_items", "number", 10, "Видимых элементов",
               "Поведение", minimum=1),
            _p("duplicates_enabled", "bool", False, "Разрешить повторы",
               "Поведение", advanced=True),
            _p("placeholder", "text", "", "Текст-подсказка", "Содержимое"),
        ]
    if class_name in ("QListWidget", "QListView", "QColumnView"):
        result += [
            _p("items", "list", None, "Элементы", "Данные", editor="list"),
            _p("selection_mode", "text", "SingleSelection", "Выделение",
               "Поведение", choices=[
                   "NoSelection", "SingleSelection", "MultiSelection",
                   "ExtendedSelection", "ContiguousSelection"]),
            _p("sorting_enabled", "bool", False, "Сортировка", "Поведение"),
            _p("alternating_rows", "bool", False, "Чередовать строки",
               "Внешний вид"),
            _p("drag_enabled", "bool", False, "Разрешить перетаскивание",
               "Поведение", advanced=True),
        ]
    if class_name in ("QSpinBox", "QDoubleSpinBox"):
        result += [
            _p("value", "number", 0, "Значение", "Диапазон"),
            _p("minimum", "number", 0, "Минимум", "Диапазон"),
            _p("maximum", "number", 100, "Максимум", "Диапазон"),
            _p("step", "number", 1, "Шаг", "Диапазон"),
            _p("decimals", "number", 0, "Знаков после запятой", "Текст",
               minimum=0, maximum=20),
            _p("prefix", "text", "", "Префикс", "Текст"),
            _p("suffix", "text", "", "Суффикс", "Текст"),
            _p("wrapping", "bool", False, "Зацикливать", "Поведение"),
            _p("keyboard_tracking", "bool", True, "Отслеживать ввод",
               "Поведение"),
            _p("alignment", "text", "right", "Выравнивание", "Текст",
               choices=ALIGNMENTS),
        ]
    if class_name in sliders:
        result += [
            _p("value", "number", 0, "Значение", "Диапазон"),
            _p("minimum", "number", 0, "Минимум", "Диапазон"),
            _p("maximum", "number", 99, "Максимум", "Диапазон"),
            _p("step", "number", 1, "Одиночный шаг", "Диапазон"),
            _p("page_step", "number", 10, "Страничный шаг", "Диапазон"),
            _p("orientation", "text", "Horizontal", "Ориентация",
               "Внешний вид", choices=["Horizontal", "Vertical"]),
            _p("tracking", "bool", True, "Непрерывное изменение",
               "Поведение"),
            _p("inverted_appearance", "bool", False, "Инвертировать вид",
               "Внешний вид"),
            _p("inverted_controls", "bool", False, "Инвертировать управление",
               "Поведение"),
        ]
        if class_name == "QSlider":
            result += [
                _p("tick_position", "text", "NoTicks", "Деления",
                   "Внешний вид", choices=[
                       "NoTicks", "TicksBothSides", "TicksAbove",
                       "TicksBelow", "TicksLeft", "TicksRight"]),
                _p("tick_interval", "number", 0, "Интервал делений",
                   "Внешний вид", minimum=0),
            ]
        if class_name == "QDial":
            result += [
                _p("notches_visible", "bool", True, "Показывать деления",
                   "Внешний вид"),
                _p("wrapping", "bool", False, "Зацикливать", "Поведение"),
            ]
    if class_name == "QProgressBar":
        result += [
            _p("value", "number", 0, "Значение", "Диапазон"),
            _p("minimum", "number", 0, "Минимум", "Диапазон"),
            _p("maximum", "number", 100, "Максимум", "Диапазон"),
            _p("format", "text", "%p%", "Формат", "Текст"),
            _p("text_visible", "bool", True, "Показывать текст",
               "Внешний вид"),
            _p("orientation", "text", "Horizontal", "Ориентация",
               "Внешний вид", choices=["Horizontal", "Vertical"]),
            _p("inverted_appearance", "bool", False, "Инвертировать",
               "Внешний вид"),
        ]
    if class_name in ("QTableWidget", "QTableView"):
        result += [
            _p("sorting_enabled", "bool", False, "Сортировка", "Поведение"),
            _p("alternating_rows", "bool", False, "Чередовать строки",
               "Внешний вид"),
            _p("grid_visible", "bool", True, "Показывать сетку",
               "Внешний вид"),
            _p("selection_behavior", "text", "SelectItems", "Тип выделения",
               "Поведение", choices=["SelectItems", "SelectRows", "SelectColumns"]),
            _p("selection_mode", "text", "SingleSelection", "Режим выделения",
               "Поведение", choices=[
                   "NoSelection", "SingleSelection", "MultiSelection",
                   "ExtendedSelection", "ContiguousSelection"]),
        ]
    if class_name in ("QTreeWidget", "QTreeView"):
        result += [
            _p("sorting_enabled", "bool", False, "Сортировка", "Поведение"),
            _p("alternating_rows", "bool", False, "Чередовать строки",
               "Внешний вид"),
            _p("root_decorated", "bool", True, "Корневые ветви",
               "Внешний вид"),
            _p("uniform_rows", "bool", False, "Одинаковая высота строк",
               "Внешний вид"),
            _p("indentation", "number", 20, "Отступ ветвей", "Внешний вид",
               minimum=0),
            _p("animated", "bool", False, "Анимация раскрытия", "Поведение"),
        ]
    if class_name == "QCalendarWidget":
        result += [
            _p("grid_visible", "bool", False, "Показывать сетку",
               "Внешний вид"),
            _p("navigation_visible", "bool", True, "Панель навигации",
               "Внешний вид"),
            _p("date_edit_enabled", "bool", True, "Редактирование даты",
               "Поведение"),
            _p("first_day", "text", "Monday", "Первый день недели",
               "Внешний вид", choices=[
                   "Monday", "Tuesday", "Wednesday", "Thursday",
                   "Friday", "Saturday", "Sunday"]),
        ]
    if class_name in ("QDateEdit", "QTimeEdit", "QDateTimeEdit"):
        result += [
            _p("display_format", "text", "", "Формат", "Текст"),
            _p("calendar_popup", "bool", class_name != "QTimeEdit",
               "Календарь", "Поведение"),
            _p("read_only", "bool", False, "Только чтение", "Поведение"),
            _p("wrapping", "bool", False, "Зацикливать", "Поведение"),
        ]
    if class_name == "QGroupBox":
        result += [
            _p("title", "text", "Группа", "Заголовок", "Содержимое"),
            _p("flat", "bool", False, "Плоская рамка", "Внешний вид"),
            _p("checkable", "bool", False, "Переключаемая", "Поведение"),
            _p("checked", "bool", True, "Включена", "Состояние"),
            _p("alignment", "text", "left", "Выравнивание заголовка",
               "Текст", choices=ALIGNMENTS),
        ]
    if class_name == "QScrollArea":
        result += [
            _p("widget_resizable", "bool", True, "Растягивать содержимое",
               "Поведение"),
            _p("alignment", "text", "left", "Выравнивание содержимого",
               "Внешний вид", choices=ALIGNMENTS),
        ]
    if class_name in ("QTabWidget", "QToolBox", "QStackedWidget"):
        result += [
            _p("current_index", "number", 0, "Текущая страница",
               "Состояние", minimum=0),
        ]
        if class_name == "QTabWidget":
            result += [
                _p("tabs_closable", "bool", False, "Закрываемые вкладки",
                   "Поведение"),
                _p("movable", "bool", False, "Перемещаемые вкладки",
                   "Поведение"),
                _p("document_mode", "bool", False, "Режим документа",
                   "Внешний вид"),
                _p("tab_position", "text", "North", "Положение вкладок",
                   "Внешний вид", choices=["North", "South", "West", "East"]),
            ]
    if class_name == "QFrame":
        result += [
            _p("frame_shape", "text", "StyledPanel", "Форма рамки",
               "Внешний вид", choices=[
                   "NoFrame", "Box", "Panel", "StyledPanel", "HLine",
                   "VLine", "WinPanel"]),
            _p("frame_shadow", "text", "Plain", "Тень рамки",
               "Внешний вид", choices=["Plain", "Raised", "Sunken"]),
            _p("line_width", "number", 1, "Толщина", "Внешний вид",
               minimum=0),
        ]
    return result


def window_properties(dialog: bool = False) -> List[Dict[str, Any]]:
    return [
        _p("title", "text", "Диалог" if dialog else "Моё приложение",
           "Заголовок", "Основные"),
        _p("app_name", "text", "MyDialog" if dialog else "MyApp",
           "Имя приложения", "Основные"),
        _p("width", "number", 480 if dialog else 900, "Ширина", "Положение",
           minimum=1),
        _p("height", "number", 320 if dialog else 600, "Высота", "Положение",
           minimum=1),
        _p("minimum_width", "number", 0, "Мин. ширина", "Ограничения",
           minimum=0),
        _p("minimum_height", "number", 0, "Мин. высота", "Ограничения",
           minimum=0),
        _p("maximum_width", "number", 16777215, "Макс. ширина",
           "Ограничения", minimum=1),
        _p("maximum_height", "number", 16777215, "Макс. высота",
           "Ограничения", minimum=1),
        _p("resizable", "bool", True, "Изменяемый размер", "Поведение"),
        _p("center", "bool", True, "Центрировать", "Поведение"),
        _p("opacity", "number", 1.0, "Прозрачность", "Внешний вид",
           minimum=0.0, maximum=1.0),
        _p("always_on_top", "bool", False, "Поверх остальных", "Поведение"),
        _p("frameless", "bool", False, "Без рамки", "Внешний вид"),
        _p("statusbar", "text", "" if dialog else "Готово",
           "Строка состояния", "Содержимое"),
        _p("icon", "file", "", "Значок", "Внешний вид", editor="file"),
        _p("style", "style", "", "Таблица стилей", "Внешний вид",
           multiline=True),
        _p("font_family", "text", "Segoe UI", "Семейство", "Шрифт"),
        _p("font_size", "number", 10, "Размер", "Шрифт", minimum=1),
    ]


def layout_properties() -> List[Dict[str, Any]]:
    return [
        _p("name", "text", "layout", "Имя", "Основные"),
        _p("margin_left", "number", 11, "Слева", "Отступы"),
        _p("margin_top", "number", 11, "Сверху", "Отступы"),
        _p("margin_right", "number", 11, "Справа", "Отступы"),
        _p("margin_bottom", "number", 11, "Снизу", "Отступы"),
        _p("spacing", "number", 8, "Между элементами", "Компоновка"),
        _p("size_constraint", "text", "SetDefaultConstraint",
           "Ограничение размера", "Компоновка", choices=[
               "SetDefaultConstraint", "SetFixedSize", "SetMinimumSize",
               "SetMaximumSize", "SetMinAndMaxSize", "SetNoConstraint"]),
    ]


def property_definitions_for(key: str, class_name: str = "") -> List[Dict[str, Any]]:
    if key in ("Window.app_window", "Window.dialog_window"):
        return window_properties(key == "Window.dialog_window")
    if key in ("Layout.vbox", "Layout.hbox", "Layout.grid", "Layout.form"):
        return layout_properties()
    if class_name or key == "Gui.designer_widget":
        return common_widget_properties() + class_properties(class_name, key)
    return []


def _bool(value: Any, fallback: bool = False) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "no", "нет")
    return fallback if value is None else bool(value)


def _number(value: Any, fallback: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _append(calls: List[str], text: str) -> None:
    if text not in calls:
        calls.append(text)


def apply_properties(target: Dict[str, Any], params: Dict[str, Any]) -> None:
    """Накладывает значения инспектора на описание widget/layout/window."""
    kind = target.get("kind")
    if kind == "window":
        target["title"] = str(params.get("title", target.get("title", "")))
        for key in ("width", "height"):
            if key in params:
                target[key] = max(1, int(_number(params[key], target.get(key, 1))))
        target["stylesheet"] = str(params.get("style", target.get("stylesheet", "")))
        target["icon"] = str(params.get("icon", target.get("icon", "")))
        target["statusbar"] = str(params.get(
            "statusbar", target.get("statusbar", "")))
        target["resizable"] = _bool(params.get("resizable"), True)
        target["center"] = _bool(params.get("center"), True)
        extra = target.setdefault("extra", {})
        for key in (
                "minimum_width", "minimum_height", "maximum_width",
                "maximum_height", "opacity", "always_on_top", "frameless",
                "font_family", "font_size"):
            if key in params:
                extra[key] = params[key]
        return
    calls = target.setdefault("calls", [])
    if kind == "layout":
        left = int(_number(params.get("margin_left", params.get("margin", 11)), 11))
        top = int(_number(params.get("margin_top", params.get("margin", 11)), 11))
        right = int(_number(params.get("margin_right", params.get("margin", 11)), 11))
        bottom = int(_number(params.get("margin_bottom", params.get("margin", 11)), 11))
        spacing = int(_number(params.get("spacing", 8), 8))
        _append(calls, f"setContentsMargins({left}, {top}, {right}, {bottom})")
        _append(calls, f"setSpacing({spacing})")
        constraint = params.get("size_constraint")
        if constraint:
            _append(calls, "setSizeConstraint("
                    f"QtWidgets.QLayout.SizeConstraint.{constraint})")
        return
    if kind != "widget":
        return
    cls = str(target.get("cls") or "")
    x = int(_number(params.get("geometry_x", 20), 20))
    y = int(_number(params.get("geometry_y", 20), 20))
    width = max(1, int(_number(params.get("width", 120), 120)))
    height = max(1, int(_number(params.get("height", 32), 32)))
    _append(calls, f"setGeometry({x}, {y}, {width}, {height})")
    for key, method, fallback in (
            ("min_width", "setMinimumWidth", 0),
            ("min_height", "setMinimumHeight", 0),
            ("max_width", "setMaximumWidth", 16777215),
            ("max_height", "setMaximumHeight", 16777215)):
        if key in params:
            _append(calls, f"{method}({int(_number(params[key], fallback))})")
    for key, method, fallback in (
            ("enabled", "setEnabled", True),
            ("visible", "setVisible", True),
            ("accept_drops", "setAcceptDrops", False),
            ("mouse_tracking", "setMouseTracking", False)):
        if key in params:
            _append(calls, f"{method}({_bool(params[key], fallback)!r})")
    if params.get("whats_this"):
        _append(calls, f"setWhatsThis({str(params['whats_this'])!r})")
    if params.get("accessible_name"):
        _append(calls, f"setAccessibleName({str(params['accessible_name'])!r})")
    if params.get("accessible_description"):
        _append(calls, "setAccessibleDescription("
                f"{str(params['accessible_description'])!r})")
    if params.get("focus_policy"):
        _append(calls, "setFocusPolicy("
                f"QtCore.Qt.FocusPolicy.{params['focus_policy']})")
    if params.get("cursor"):
        _append(calls, "setCursor(QtGui.QCursor("
                f"QtCore.Qt.CursorShape.{params['cursor']}))")
    hp = params.get("h_size_policy", "Preferred")
    vp = params.get("v_size_policy", "Preferred")
    _append(calls, "setSizePolicy("
            f"QtWidgets.QSizePolicy.Policy.{hp}, "
            f"QtWidgets.QSizePolicy.Policy.{vp})")
    target["tooltip"] = str(params.get("tooltip", target.get("tooltip", "")))
    target["stylesheet"] = str(params.get("style", target.get("stylesheet", "")))
    target.setdefault("extra", {})["font"] = {
        "family": str(params.get("font_family", "Segoe UI")),
        "size": int(_number(params.get("font_size", 10), 10)),
        "bold": _bool(params.get("font_bold"), False),
        "italic": _bool(params.get("font_italic"), False),
        "underline": _bool(params.get("font_underline"), False),
    }

    # Простые свойства, совпадающие у большинства классов Qt.
    simple = {
        "checkable": "setCheckable", "checked": "setChecked",
        "auto_repeat": "setAutoRepeat", "flat": "setFlat",
        "read_only": "setReadOnly", "clear_button": "setClearButtonEnabled",
        "editable": "setEditable", "duplicates_enabled": "setDuplicatesEnabled",
        "sorting_enabled": "setSortingEnabled",
        "alternating_rows": "setAlternatingRowColors",
        "drag_enabled": "setDragEnabled", "wrapping": "setWrapping",
        "keyboard_tracking": "setKeyboardTracking",
        "tracking": "setTracking",
        "inverted_appearance": "setInvertedAppearance",
        "inverted_controls": "setInvertedControls",
        "notches_visible": "setNotchesVisible",
        "text_visible": "setTextVisible", "grid_visible": "setGridVisible",
        "navigation_visible": "setNavigationBarVisible",
        "date_edit_enabled": "setDateEditEnabled",
        "scaled_contents": "setScaledContents",
        "open_external_links": "setOpenExternalLinks",
        "tristate": "setTristate",
        "tab_changes_focus": "setTabChangesFocus",
        "accept_rich_text": "setAcceptRichText",
        "root_decorated": "setRootIsDecorated",
        "uniform_rows": "setUniformRowHeights", "animated": "setAnimated",
        "widget_resizable": "setWidgetResizable",
        "tabs_closable": "setTabsClosable", "movable": "setMovable",
        "document_mode": "setDocumentMode",
    }
    for key, method in simple.items():
        if key in params and isinstance(params[key], (bool, int)):
            _append(calls, f"{method}({_bool(params[key])!r})")
    numeric = {
        "minimum": "setMinimum", "maximum": "setMaximum",
        "value": "setValue", "step": "setSingleStep",
        "page_step": "setPageStep", "tick_interval": "setTickInterval",
        "max_length": "setMaxLength",
        "max_visible_items": "setMaxVisibleItems",
        "current_index": "setCurrentIndex", "indent": "setIndent",
        "margin": "setMargin", "indentation": "setIndentation",
        "line_width": "setLineWidth", "auto_repeat_delay": "setAutoRepeatDelay",
        "auto_repeat_interval": "setAutoRepeatInterval",
    }
    for key, method in numeric.items():
        if key in params:
            _append(calls, f"{method}({int(_number(params[key]))})")
    text_methods = {
        "prefix": "setPrefix", "suffix": "setSuffix",
        "input_mask": "setInputMask", "format": "setFormat",
        "display_format": "setDisplayFormat",
    }
    for key, method in text_methods.items():
        if params.get(key):
            _append(calls, f"{method}({str(params[key])!r})")
    if "text" in params and cls in (
            "QPushButton", "QToolButton", "QCommandLinkButton", "QLabel",
            "QCheckBox", "QRadioButton"):
        _append(calls, f"setText({str(params['text'])!r})")
    if "value" in params and cls in ("QLineEdit", "QTextEdit", "QTextBrowser"):
        method = "setText" if cls == "QLineEdit" else "setPlainText"
        _append(calls, f"{method}({str(params['value'])!r})")
    if "text" in params and cls == "QPlainTextEdit":
        _append(calls, f"setPlainText({str(params['text'])!r})")
    if params.get("placeholder") and cls in (
            "QLineEdit", "QTextEdit", "QPlainTextEdit", "QComboBox"):
        method = ("setPlaceholderText" if cls != "QComboBox"
                  else "setPlaceholderText")
        _append(calls, f"{method}({str(params['placeholder'])!r})")
    if params.get("echo_mode") and cls == "QLineEdit":
        _append(calls, "setEchoMode("
                f"QtWidgets.QLineEdit.EchoMode.{params['echo_mode']})")
    if params.get("orientation") and cls in (
            "QSlider", "QScrollBar", "QProgressBar"):
        _append(calls, "setOrientation("
                f"QtCore.Qt.Orientation.{params['orientation']})")
    if params.get("tick_position") and cls == "QSlider":
        _append(calls, "setTickPosition("
                f"QtWidgets.QSlider.TickPosition.{params['tick_position']})")
    if params.get("alignment"):
        align = {
            "left": "AlignLeft", "center": "AlignCenter",
            "right": "AlignRight",
        }.get(str(params["alignment"]), "AlignLeft")
        _append(calls, "setAlignment("
                f"QtCore.Qt.AlignmentFlag.{align})")
    if params.get("align") and cls == "QLabel":
        align = {
            "left": "AlignLeft", "center": "AlignCenter",
            "right": "AlignRight",
        }.get(str(params["align"]), "AlignLeft")
        _append(calls, "setAlignment("
                f"QtCore.Qt.AlignmentFlag.{align})")
    if "wrap" in params and cls == "QLabel":
        _append(calls, f"setWordWrap({_bool(params['wrap'])!r})")
    if params.get("title") and cls == "QGroupBox":
        _append(calls, f"setTitle({str(params['title'])!r})")
    if params.get("frame_shape") and cls == "QFrame":
        _append(calls, "setFrameShape("
                f"QtWidgets.QFrame.Shape.{params['frame_shape']})")
    if params.get("frame_shadow") and cls == "QFrame":
        _append(calls, "setFrameShadow("
                f"QtWidgets.QFrame.Shadow.{params['frame_shadow']})")
    if "default_button" in params and cls == "QPushButton":
        _append(calls, f"setDefault({_bool(params['default_button'])!r})")
    if params.get("description") and cls == "QCommandLinkButton":
        _append(calls, f"setDescription({str(params['description'])!r})")
    if params.get("icon_path") and cls in (
            "QPushButton", "QToolButton", "QCommandLinkButton"):
        _append(calls, f"setIcon(QtGui.QIcon({str(params['icon_path'])!r}))")
        size = max(1, int(_number(params.get("icon_size", 16), 16)))
        _append(calls, f"setIconSize(QtCore.QSize({size}, {size}))")
    if "decimals" in params and cls == "QDoubleSpinBox":
        _append(calls, f"setDecimals({int(_number(params['decimals']))})")
    if params.get("selection_mode") and cls in (
            "QListWidget", "QListView", "QColumnView", "QTableWidget",
            "QTableView", "QTreeWidget", "QTreeView"):
        _append(calls, "setSelectionMode("
                "QtWidgets.QAbstractItemView.SelectionMode."
                f"{params['selection_mode']})")
    if params.get("selection_behavior") and cls in (
            "QTableWidget", "QTableView"):
        _append(calls, "setSelectionBehavior("
                "QtWidgets.QAbstractItemView.SelectionBehavior."
                f"{params['selection_behavior']})")
    if "calendar_popup" in params and cls in (
            "QDateEdit", "QDateTimeEdit"):
        _append(calls, f"setCalendarPopup({_bool(params['calendar_popup'])!r})")
    if params.get("first_day") and cls == "QCalendarWidget":
        _append(calls, "setFirstDayOfWeek("
                f"QtCore.Qt.DayOfWeek.{params['first_day']})")
    if params.get("tab_position") and cls == "QTabWidget":
        _append(calls, "setTabPosition("
                f"QtWidgets.QTabWidget.TabPosition.{params['tab_position']})")
    if "line_wrap" in params and cls == "QTextEdit":
        mode = "WidgetWidth" if _bool(params["line_wrap"]) else "NoWrap"
        _append(calls, "setLineWrapMode("
                f"QtWidgets.QTextEdit.LineWrapMode.{mode})")
    if "line_wrap" in params and cls == "QPlainTextEdit":
        mode = "WidgetWidth" if _bool(params["line_wrap"]) else "NoWrap"
        _append(calls, "setLineWrapMode("
                f"QtWidgets.QPlainTextEdit.LineWrapMode.{mode})")


def imported_values(designer_params: Dict[str, Any]) -> Dict[str, Any]:
    """Преобразует свойства Qt Designer в поля единого инспектора."""
    raw = designer_params.get("props") or {}
    if isinstance(raw, str):
        import json
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}
    values: Dict[str, Any] = {}
    aliases = {
        "objectName": "name", "enabled": "enabled", "visible": "visible",
        "toolTip": "tooltip", "whatsThis": "whats_this",
        "styleSheet": "style", "accessibleName": "accessible_name",
        "accessibleDescription": "accessible_description",
        "text": "text", "title": "title", "checked": "checked",
        "checkable": "checkable", "readOnly": "read_only",
        "placeholderText": "placeholder", "minimum": "minimum",
        "maximum": "maximum", "value": "value",
        "singleStep": "step", "pageStep": "page_step",
        "tracking": "tracking", "tickInterval": "tick_interval",
        "format": "format", "textVisible": "text_visible",
        "editable": "editable", "currentIndex": "current_index",
        "maxVisibleItems": "max_visible_items",
        "wordWrap": "wrap", "margin": "margin", "indent": "indent",
        "gridVisible": "grid_visible", "sortingEnabled": "sorting_enabled",
        "alternatingRowColors": "alternating_rows",
    }
    for qt_name, name in aliases.items():
        if qt_name in raw:
            values[name] = raw[qt_name]
    geometry = raw.get("geometry")
    if isinstance(geometry, dict):
        values.update({
            "geometry_x": geometry.get("x", 0),
            "geometry_y": geometry.get("y", 0),
            "width": geometry.get("width", 120),
            "height": geometry.get("height", 32),
        })
    elif any(key in designer_params for key in ("x", "y", "width", "height")):
        values.update({
            "geometry_x": designer_params.get("x", 0),
            "geometry_y": designer_params.get("y", 0),
            "width": designer_params.get("width", 120),
            "height": designer_params.get("height", 32),
        })
    font = raw.get("font")
    if isinstance(font, dict):
        values.update({
            "font_family": font.get("family", "Segoe UI"),
            "font_size": font.get("pointSize", font.get("size", 10)),
            "font_bold": font.get("bold", False),
            "font_italic": font.get("italic", False),
            "font_underline": font.get("underline", False),
        })
    return values