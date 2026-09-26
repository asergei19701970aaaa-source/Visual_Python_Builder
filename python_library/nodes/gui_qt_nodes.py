"""GUI: виджеты Qt Designer, которых не было в базовой библиотеке.

Набор повторяет палитру Qt Designer: кнопки, списки, контейнеры,
ввод даты/времени, регуляторы и прочие элементы.
"""
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, lst, num, txt

nd = library("GuiQt", "13. GUI: Виджеты Qt Designer", color="#2f7fa8")


def _q(value):
    return repr(txt(value))


def _finish(w, tooltip="", enabled=True, style="", width=0, height=0):
    """Общие настройки для всех нод этой библиотеки."""
    if txt(tooltip):
        w["tooltip"] = txt(tooltip)
    if not flag(enabled, True):
        w["calls"].append("setEnabled(False)")
    if num(width) > 0:
        w["calls"].append(f"setMinimumWidth({int(num(width))})")
    if num(height) > 0:
        w["calls"].append(f"setMinimumHeight({int(num(height))})")
    if txt(style):
        w["stylesheet"] = txt(style)
    return w


def _items(raw):
    return [txt(v) for v in lst(raw) if txt(v)]


def _children(raw):
    return [c for c in lst(raw) if isinstance(c, dict)]


# ----------------------------------------------------------------- кнопки

@nd("Кнопка-инструмент",
    inputs=[("text", "text", "Инструмент"), ("name", "text", ""),
            ("checkable", "bool", False), ("tooltip", "text", ""),
            ("enabled", "bool", True), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QToolButton", "кнопка"])
def tool_button(text, name, checkable, tooltip, enabled, style):
    """QToolButton — компактная кнопка для панелей."""
    calls = [f"setText({_q(text)})"]
    if flag(checkable):
        calls.append("setCheckable(True)")
    return _finish(u.widget("QToolButton", name=name or "tool_button",
                            calls=calls), tooltip, enabled, style)


@nd("Кнопка-ссылка",
    inputs=[("text", "text", "Действие"), ("description", "text", "Пояснение"),
            ("name", "text", ""), ("enabled", "bool", True),
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QCommandLinkButton"])
def command_link_button(text, description, name, enabled, style):
    """QCommandLinkButton — крупная кнопка с пояснением."""
    calls = [f"setText({_q(text)})"]
    if txt(description):
        calls.append(f"setDescription({_q(description)})")
    return _finish(u.widget("QCommandLinkButton", name=name or "link_button",
                            calls=calls), "", enabled, style)


@nd("Набор кнопок диалога",
    inputs=[{"name": "buttons", "type": "text", "default": "Ok, Cancel",
             "hint": "Ok, Cancel, Apply, Close, Yes, No, Save, Reset, Help"},
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QDialogButtonBox"])
def dialog_button_box(buttons, name, style):
    """QDialogButtonBox — стандартные кнопки диалога."""
    allowed = {"ok": "Ok", "cancel": "Cancel", "apply": "Apply",
               "close": "Close", "yes": "Yes", "no": "No", "save": "Save",
               "reset": "Reset", "help": "Help", "discard": "Discard",
               "open": "Open", "retry": "Retry", "ignore": "Ignore"}
    names = []
    for chunk in txt(buttons).replace("|", ",").split(","):
        key = chunk.strip().lower()
        if key in allowed and allowed[key] not in names:
            names.append(allowed[key])
    if not names:
        names = ["Ok", "Cancel"]
    expression = " | ".join(
        f"QtWidgets.QDialogButtonBox.StandardButton.{n}" for n in names)
    return _finish(u.widget("QDialogButtonBox", name=name or "button_box",
                            calls=[f"setStandardButtons({expression})"]),
                   style=style)


# ------------------------------------------------------------------- ввод

@nd("Выбор шрифта",
    inputs=[("name", "text", ""), ("tooltip", "text", ""),
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QFontComboBox", "шрифт"])
def font_combo_box(name, tooltip, style):
    """QFontComboBox — список шрифтов системы."""
    return _finish(u.widget("QFontComboBox", name=name or "font_combo"),
                   tooltip, style=style)


@nd("Простой текстовый редактор",
    inputs=[{"name": "text", "type": "text", "default": "", "multiline": True},
            ("placeholder", "text", ""), ("read_only", "bool", False),
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QPlainTextEdit"])
def plain_text_edit(text, placeholder, read_only, name, style):
    """QPlainTextEdit — редактор большого простого текста."""
    calls = []
    if txt(text):
        calls.append(f"setPlainText({_q(text)})")
    if txt(placeholder):
        calls.append(f"setPlaceholderText({_q(placeholder)})")
    if flag(read_only):
        calls.append("setReadOnly(True)")
    return _finish(u.widget("QPlainTextEdit", name=name or "plain_edit",
                            calls=calls), style=style)


@nd("Поле горячей клавиши",
    inputs=[("shortcut", "text", "Ctrl+S"), ("name", "text", ""),
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QKeySequenceEdit"])
def key_sequence_edit(shortcut, name, style):
    """QKeySequenceEdit — ввод сочетания клавиш."""
    calls = []
    if txt(shortcut):
        calls.append(f"setKeySequence(QtGui.QKeySequence({_q(shortcut)}))")
    return _finish(u.widget("QKeySequenceEdit", name=name or "key_edit",
                            calls=calls), style=style)


@nd("Ввод времени",
    inputs=[("time", "text", "12:00:00"), ("name", "text", ""),
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QTimeEdit", "время"])
def time_edit(time, name, style):
    """QTimeEdit — поле ввода времени."""
    calls = []
    if txt(time):
        calls.append("setTime(QtCore.QTime.fromString("
                     f"{_q(time)}, 'HH:mm:ss'))")
    return _finish(u.widget("QTimeEdit", name=name or "time_edit",
                            calls=calls), style=style)


@nd("Ввод даты и времени",
    inputs=[("date", "text", "2024-01-01"), ("time", "text", "09:00:00"),
            ("calendar_popup", "bool", True), ("name", "text", ""),
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QDateTimeEdit"])
def date_time_edit(date, time, calendar_popup, name, style):
    """QDateTimeEdit — поле ввода даты и времени."""
    calls = []
    if txt(date):
        calls.append("setDate(QtCore.QDate.fromString("
                     f"{_q(date)}, 'yyyy-MM-dd'))")
    if txt(time):
        calls.append("setTime(QtCore.QTime.fromString("
                     f"{_q(time)}, 'HH:mm:ss'))")
    if flag(calendar_popup, True):
        calls.append("setCalendarPopup(True)")
    return _finish(u.widget("QDateTimeEdit", name=name or "datetime_edit",
                            calls=calls), style=style)


# -------------------------------------------------------------- регуляторы

@nd("Круглый регулятор",
    inputs=[("minimum", "number", 0), ("maximum", "number", 100),
            ("value", "number", 50), ("notches", "bool", True),
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QDial"])
def dial(minimum, maximum, value, notches, name, style):
    """QDial — круглый регулятор."""
    calls = [f"setRange({int(num(minimum))}, {int(num(maximum, 100))})",
             f"setValue({int(num(value))})"]
    if flag(notches, True):
        calls.append("setNotchesVisible(True)")
    return _finish(u.widget("QDial", name=name or "dial", calls=calls),
                   style=style)


@nd("Полоса прокрутки",
    inputs=[{"name": "orientation", "type": "text",
             "default": "Горизонтально",
             "choices": ["Горизонтально", "Вертикально"]},
            ("minimum", "number", 0), ("maximum", "number", 100),
            ("value", "number", 0), ("name", "text", ""),
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QScrollBar"])
def scroll_bar(orientation, minimum, maximum, value, name, style):
    """QScrollBar — полоса прокрутки."""
    vertical = "вертик" in txt(orientation).lower()
    direction = "Vertical" if vertical else "Horizontal"
    calls = [f"setOrientation(QtCore.Qt.Orientation.{direction})",
             f"setRange({int(num(minimum))}, {int(num(maximum, 100))})",
             f"setValue({int(num(value))})"]
    return _finish(u.widget("QScrollBar", name=name or "scroll_bar",
                            calls=calls), style=style)


@nd("Цифровое табло",
    inputs=[("value", "number", 0), ("digits", "number", 5),
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QLCDNumber"])
def lcd_number(value, digits, name, style):
    """QLCDNumber — цифровое табло."""
    calls = [f"setDigitCount({max(1, int(num(digits, 5)))})",
             f"display({num(value)})"]
    return _finish(u.widget("QLCDNumber", name=name or "lcd", calls=calls),
                   style=style)


# ---------------------------------------------------------------- списки

@nd("Дерево",
    inputs=[{"name": "headers", "type": "text", "default": "Название, Значение",
             "hint": "Заголовки колонок через запятую"},
            {"name": "rows", "type": "text", "default": "",
             "multiline": True,
             "hint": "По строке на узел, колонки через запятую, "
                     "вложенность двумя пробелами"},
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QTreeWidget", "дерево"])
def tree_widget(headers, rows, name, style):
    """QTreeWidget — дерево с колонками."""
    heads = [h.strip() for h in txt(headers).split(",") if h.strip()]
    w = u.widget("QTreeWidget", name=name or "tree")
    if heads:
        w["extra"]["headers"] = heads
    tree_rows = []
    for line in txt(rows).splitlines():
        if not line.strip():
            continue
        level = (len(line) - len(line.lstrip(" "))) // 2
        cells = [c.strip() for c in line.strip().split(",")]
        tree_rows.append([level] + cells)
    if tree_rows:
        w["extra"]["tree_rows"] = tree_rows
    return _finish(w, style=style)


@nd("Список (QListView)",
    inputs=[("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QListView"])
def list_view(name, style):
    """QListView — список с моделью данных."""
    return _finish(u.widget("QListView", name=name or "list_view_model"),
                   style=style)


@nd("Колоночный список",
    inputs=[("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QColumnView"])
def column_view(name, style):
    """QColumnView — просмотр дерева колонками."""
    return _finish(u.widget("QColumnView", name=name or "column_view"),
                   style=style)


# ------------------------------------------------------------- контейнеры

@nd("Набор панелей",
    inputs=[("items", "list", None),
            {"name": "titles", "type": "text", "default": "",
             "hint": "Заголовки страниц через запятую"},
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QToolBox"])
def tool_box(items, titles, name, style):
    """QToolBox — вертикальный набор раскрывающихся панелей."""
    kids = _children(items)
    w = u.widget("QToolBox", name=name or "tool_box", children=kids)
    heads = [t.strip() for t in txt(titles).split(",") if t.strip()]
    w["extra"]["page_titles"] = heads or [f"Панель {i + 1}"
                                          for i in range(len(kids))]
    return _finish(w, style=style)


@nd("Переключаемые страницы",
    inputs=[("items", "list", None), ("current", "number", 0),
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QStackedWidget"])
def stacked_widget(items, current, name, style):
    """QStackedWidget — стопка страниц без вкладок."""
    kids = _children(items)
    w = u.widget("QStackedWidget", name=name or "stack", children=kids)
    w["extra"]["page_titles"] = [f"Страница {i + 1}" for i in range(len(kids))]
    index = int(num(current))
    if kids:
        w["calls"].append(f"setCurrentIndex({max(0, min(index, len(kids) - 1))})")
    return _finish(w, style=style)


@nd("Разделитель",
    inputs=[("items", "list", None),
            {"name": "orientation", "type": "text",
             "default": "Горизонтально",
             "choices": ["Горизонтально", "Вертикально"]},
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QSplitter"])
def splitter(items, orientation, name, style):
    """QSplitter — области с перетаскиваемой границей."""
    vertical = "вертик" in txt(orientation).lower()
    direction = "Vertical" if vertical else "Horizontal"
    w = u.widget("QSplitter", name=name or "splitter",
                 children=_children(items),
                 calls=[f"setOrientation(QtCore.Qt.Orientation.{direction})"])
    return _finish(w, style=style)


@nd("Область MDI",
    inputs=[("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QMdiArea"])
def mdi_area(name, style):
    """QMdiArea — область для дочерних окон."""
    return _finish(u.widget("QMdiArea", name=name or "mdi_area"), style=style)


@nd("Приставная панель",
    inputs=[("title", "text", "Панель"), ("items", "list", None),
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QDockWidget"])
def dock_widget(title, items, name, style):
    """QDockWidget — приставная панель главного окна."""
    kids = _children(items)
    w = u.widget("QDockWidget", name=name or "dock", children=kids,
                 calls=[f"setWindowTitle({_q(title)})"])
    if kids:
        w["extra"]["absolute_container"] = True
    return _finish(w, style=style)


@nd("Рамка",
    inputs=[("items", "list", None),
            {"name": "shape", "type": "text", "default": "Box",
             "choices": ["Box", "Panel", "StyledPanel", "HLine", "VLine",
                         "NoFrame"]},
            ("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QFrame", "рамка"])
def frame(items, shape, name, style):
    """QFrame — рамка или разделительная линия."""
    allowed = {"box": "Box", "panel": "Panel", "styledpanel": "StyledPanel",
               "hline": "HLine", "vline": "VLine", "noframe": "NoFrame"}
    key = allowed.get(txt(shape).strip().lower(), "Box")
    kids = _children(items)
    w = u.widget("QFrame", name=name or "frame", children=kids,
                 calls=[f"setFrameShape(QtWidgets.QFrame.Shape.{key})",
                        "setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)"])
    if kids:
        w["extra"]["absolute_container"] = True
    return _finish(w, style=style)


@nd("Графическая сцена",
    inputs=[("name", "text", ""), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["QGraphicsView"])
def graphics_view(name, style):
    """QGraphicsView — область для графической сцены."""
    return _finish(u.widget("QGraphicsView", name=name or "graphics_view",
                            calls=["setScene(QtWidgets.QGraphicsScene())"]),
                   style=style)
