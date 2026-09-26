"""GUI: виджеты PyQt6. Каждая нода возвращает описание виджета."""
import ast
import json

from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, lst, num, txt

nd = library("Gui", "11. GUI: Виджеты", color="#2f5fa8")


def _q(value):
    return repr(txt(value))


def _common(w, tooltip="", enabled=True, visible=True, width=0, height=0,
            font=None, style=""):
    """Добавляет общие настройки к виджету."""
    if tooltip:
        w["tooltip"] = txt(tooltip)
    if not flag(enabled, True):
        w["calls"].append("setEnabled(False)")
    if not flag(visible, True):
        w["calls"].append("setVisible(False)")
    if num(width) > 0:
        w["calls"].append(f"setMinimumWidth({int(num(width))})")
    if num(height) > 0:
        w["calls"].append(f"setMinimumHeight({int(num(height))})")
    if isinstance(font, dict):
        w["extra"]["font"] = font
    if style:
        w["stylesheet"] = txt(style)
    return w


@nd("Кнопка", inputs=[("text", "text", "Нажми меня"), ("name", "text", ""),
                     ("tooltip", "text", ""), ("enabled", "bool", True),
                     ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["button", "кнопка"])
def button(text, name, tooltip, enabled, style):
    """QPushButton — обычная кнопка."""
    w = u.widget("QPushButton", name=name or f"btn_{u.ident(text, 'btn')}",
                 calls=[f"setText({_q(text)})"])
    return _common(w, tooltip, enabled, style=style)


@nd("Надпись", inputs=[("text", "text", "Привет!"), ("name", "text", ""),
                      {"name": "align", "type": "text", "default": "left",
                       "choices": ["left", "center", "right"]},
                      ("wrap", "bool", False), ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["label", "текст"])
def label(text, name, align, wrap, style):
    """QLabel — текстовая надпись."""
    amap = {"left": "AlignLeft", "center": "AlignCenter", "right": "AlignRight"}
    calls = [f"setText({_q(text)})",
             f"setAlignment(QtCore.Qt.AlignmentFlag.{amap.get(txt(align), 'AlignLeft')})"]
    if flag(wrap):
        calls.append("setWordWrap(True)")
    w = u.widget("QLabel", name=name or f"lbl_{u.ident(text, 'lbl')}", calls=calls)
    return _common(w, style=style)


@nd("Поле ввода", inputs=[("placeholder", "text", "Введите текст"),
                         ("value", "text", ""), ("name", "text", ""),
                         ("password", "bool", False), ("tooltip", "text", "")],
    outputs=[("widget", "widget")], tags=["input", "lineedit"])
def line_edit(placeholder, value, name, password, tooltip):
    """QLineEdit — однострочное поле ввода."""
    calls = [f"setPlaceholderText({_q(placeholder)})"]
    if txt(value):
        calls.append(f"setText({_q(value)})")
    if flag(password):
        calls.append("setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)")
    w = u.widget("QLineEdit", name=name or "input", calls=calls)
    return _common(w, tooltip)


@nd("Многострочное поле",
    inputs=[{"name": "value", "type": "text", "default": "", "multiline": True},
            ("placeholder", "text", ""), ("name", "text", ""),
            ("readonly", "bool", False)],
    outputs=[("widget", "widget")], tags=["textedit"])
def text_edit(value, placeholder, name, readonly):
    """QTextEdit — многострочный редактор текста."""
    calls = []
    if txt(value):
        calls.append(f"setPlainText({_q(value)})")
    if txt(placeholder):
        calls.append(f"setPlaceholderText({_q(placeholder)})")
    if flag(readonly):
        calls.append("setReadOnly(True)")
    return _common(u.widget("QTextEdit", name=name or "editor", calls=calls))


@nd("Флажок", inputs=[("text", "text", "Включить"), ("checked", "bool", False),
                    ("name", "text", ""), ("tooltip", "text", "")],
    outputs=[("widget", "widget")], tags=["checkbox"])
def checkbox(text, checked, name, tooltip):
    """QCheckBox — галочка."""
    calls = [f"setText({_q(text)})"]
    if flag(checked):
        calls.append("setChecked(True)")
    return _common(u.widget("QCheckBox", name=name or f"chk_{u.ident(text, 'chk')}",
                            calls=calls), tooltip)


@nd("Переключатель", inputs=[("text", "text", "Вариант"), ("checked", "bool", False),
                          ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["radio"])
def radio(text, checked, name):
    """QRadioButton — переключатель."""
    calls = [f"setText({_q(text)})"]
    if flag(checked):
        calls.append("setChecked(True)")
    return _common(u.widget("QRadioButton",
                            name=name or f"rad_{u.ident(text, 'rad')}", calls=calls))


@nd("Выпадающий список", inputs=[("items", "list", None), ("name", "text", ""),
                               ("editable", "bool", False),
                               ("tooltip", "text", "")],
    outputs=[("widget", "widget")], tags=["combobox"])
def combo_box(items, name, editable, tooltip):
    """QComboBox — выпадающий список."""
    values = [txt(v) for v in lst(items)] or ["Первый", "Второй"]
    calls = [f"addItems({values!r})"]
    if flag(editable):
        calls.append("setEditable(True)")
    return _common(u.widget("QComboBox", name=name or "combo", calls=calls), tooltip)


@nd("Список элементов", inputs=[("items", "list", None), ("name", "text", ""),
                             ("multi", "bool", False)],
    outputs=[("widget", "widget")], tags=["listwidget"])
def list_widget(items, name, multi):
    """QListWidget — список строк."""
    values = [txt(v) for v in lst(items)]
    calls = [f"addItems({values!r})"]
    if flag(multi):
        calls.append("setSelectionMode("
                     "QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)")
    return _common(u.widget("QListWidget", name=name or "list_view", calls=calls))


@nd("Числовое поле", inputs=[("value", "number", 0), ("minimum", "number", 0),
                            ("maximum", "number", 100), ("step", "number", 1),
                            ("decimals", "number", 0), ("name", "text", ""),
                            ("suffix", "text", "")],
    outputs=[("widget", "widget")], tags=["spinbox"])
def spin_box(value, minimum, maximum, step, decimals, name, suffix):
    """QSpinBox / QDoubleSpinBox — ввод числа."""
    dec = int(num(decimals))
    cls = "QDoubleSpinBox" if dec > 0 else "QSpinBox"
    conv = float if dec > 0 else int
    calls = [f"setRange({conv(num(minimum))}, {conv(num(maximum, 100))})",
             f"setSingleStep({conv(num(step, 1))})",
             f"setValue({conv(num(value))})"]
    if dec > 0:
        calls.append(f"setDecimals({dec})")
    if txt(suffix):
        calls.append(f"setSuffix({_q(suffix)})")
    return _common(u.widget(cls, name=name or "spin", calls=calls))


@nd("Ползунок", inputs=[("value", "number", 50), ("minimum", "number", 0),
                      ("maximum", "number", 100), ("name", "text", ""),
                      ("vertical", "bool", False)],
    outputs=[("widget", "widget")], tags=["slider"])
def slider(value, minimum, maximum, name, vertical):
    """QSlider — ползунок."""
    orient = "Vertical" if flag(vertical) else "Horizontal"
    calls = [f"setOrientation(QtCore.Qt.Orientation.{orient})",
             f"setRange({int(num(minimum))}, {int(num(maximum, 100))})",
             f"setValue({int(num(value, 50))})"]
    return _common(u.widget("QSlider", name=name or "slider", calls=calls))


@nd("Прогресс", inputs=[("value", "number", 30), ("maximum", "number", 100),
                      ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["progressbar"])
def progress_bar(value, maximum, name):
    """QProgressBar — индикатор выполнения."""
    calls = [f"setMaximum({int(num(maximum, 100))})",
             f"setValue({int(num(value, 30))})"]
    return _common(u.widget("QProgressBar", name=name or "progress", calls=calls))


@nd("Таблица", inputs=[("header", "list", None), ("rows", "list", None),
                      ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["table"])
def table(header, rows, name):
    """QTableWidget — таблица с данными."""
    head = [txt(v) for v in lst(header)]
    data = []
    for row in lst(rows):
        cells = row if isinstance(row, (list, tuple)) else [row]
        data.append([txt(c) for c in cells])
    cols = max([len(head)] + [len(r) for r in data] + [1])
    w = u.widget("QTableWidget", name=name or "table",
                 calls=[f"setColumnCount({cols})", f"setRowCount({len(data)})"])
    if head:
        w["calls"].append(f"setHorizontalHeaderLabels({head!r})")
    w["extra"]["table_rows"] = data
    return _common(w)


@nd("Дерево", inputs=[("header", "list", None), ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["tree"])
def tree(header, name):
    """QTreeWidget — деревовидный список."""
    head = [txt(v) for v in lst(header)] or ["Элемент"]
    return _common(u.widget("QTreeWidget", name=name or "tree",
                            calls=[f"setHeaderLabels({head!r})"]))


@nd("Календарь", inputs=[("name", "text", "")],
    outputs=[("widget", "widget")], tags=["calendar"])
def calendar(name):
    """QCalendarWidget — календарь."""
    return _common(u.widget("QCalendarWidget", name=name or "calendar"))


@nd("Поле даты", inputs=[("name", "text", ""), ("with_time", "bool", False)],
    outputs=[("widget", "widget")], tags=["date"])
def date_edit(name, with_time):
    """QDateEdit / QDateTimeEdit — выбор даты."""
    cls = "QDateTimeEdit" if flag(with_time) else "QDateEdit"
    calls = ["setCalendarPopup(True)"]
    calls.append("setDateTime(QtCore.QDateTime.currentDateTime())"
                 if flag(with_time) else
                 "setDate(QtCore.QDate.currentDate())")
    return _common(u.widget(cls, name=name or "date_input", calls=calls))


@nd("Картинка", inputs=[("path", "text", ""), ("name", "text", ""),
                      ("width", "number", 120)],
    outputs=[("widget", "widget")], tags=["image", "pixmap"])
def image(path, name, width):
    """QLabel с картинкой."""
    w = u.widget("QLabel", name=name or "picture")
    w["extra"]["image"] = {"path": txt(path), "width": int(num(width))}
    return _common(w)


@nd("Разделитель", inputs=[("vertical", "bool", False)],
    outputs=[("widget", "widget")], tags=["separator", "line"])
def separator(vertical):
    """Горизонтальная или вертикальная линия."""
    shape = "VLine" if flag(vertical) else "HLine"
    return u.widget("QFrame", name="line",
                    calls=[f"setFrameShape(QtWidgets.QFrame.Shape.{shape})",
                           "setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)"])


@nd("Группа", inputs=[("title", "text", "Группа"), ("content", "layout", None),
                    ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["groupbox"])
def group_box(title, content, name):
    """QGroupBox — рамка с заголовком вокруг компоновки."""
    w = u.widget("QGroupBox", name=name or f"group_{u.ident(title, 'g')}",
                 calls=[f"setTitle({_q(title)})"], content=content)
    return _common(w)


@nd("Область прокрутки", inputs=[("content", "layout", None), ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["scroll"])
def scroll_area(content, name):
    """QScrollArea — прокручиваемая область."""
    w = u.widget("QScrollArea", name=name or "scroll",
                 calls=["setWidgetResizable(True)"], content=content)
    w["extra"]["scroll"] = True
    return w


@nd("Вкладка", inputs=[("title", "text", "Вкладка"), ("content", "layout", None)],
    outputs=[("tab", "widget")], tags=["tab"])
def tab(title, content):
    """Одна вкладка для ноды 'Вкладки'."""
    return {"kind": "tab", "title": txt(title) or "Вкладка", "content": content}


@nd("Вкладки", inputs=[("tabs", "list", None), ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["tabwidget"])
def tab_widget(tabs, name):
    """QTabWidget — набор вкладок."""
    items = []
    for t in lst(tabs):
        if isinstance(t, dict) and t.get("kind") == "tab":
            items.append(t)
        elif isinstance(t, dict):
            items.append({"title": "Вкладка", "content": t})
    return u.widget("QTabWidget", name=name or "tabs", tabs=items)


@nd("Диаграмма (виджет)", inputs=[("chart", "chart", None), ("name", "text", ""),
                                ("height", "number", 220)],
    outputs=[("widget", "widget")], tags=["chart", "график"])
def chart_widget(chart, name, height):
    """Виджет-диаграмма (рисуется средствами QPainter)."""
    data = chart if isinstance(chart, dict) else {"chart": "bar", "labels": [],
                                                  "values": [], "title": ""}
    w = u.widget("ChartView", name=name or "chart", helper="ChartView", module="")
    w["extra"]["chart"] = data
    if num(height, 220) > 0:
        w["calls"].append(f"setMinimumHeight({int(num(height, 220))})")
    return w


@nd("Веб-просмотр текста", inputs=[{"name": "html", "type": "text",
                                       "default": "<h2>Привет</h2>",
                                       "multiline": True},
                                      ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["browser", "html"])
def text_browser(html, name):
    """QTextBrowser — просмотр HTML-текста."""
    return _common(u.widget("QTextBrowser", name=name or "browser",
                            calls=[f"setHtml({_q(html)})",
                                   "setOpenExternalLinks(True)"]))


@nd("Произвольный виджет",
    inputs=[("cls", "text", "QDial"), ("name", "text", ""),
            {"name": "calls", "type": "text", "default": "",
             "multiline": True,
             "hint": "По одному вызову на строку, напр. setRange(0, 10)"}],
    outputs=[("widget", "widget")], tags=["custom"])
def custom_widget(cls, name, calls):
    """Любой класс QtWidgets с ручными вызовами методов."""
    lines = [c.strip() for c in txt(calls).splitlines() if c.strip()]
    return u.widget(txt(cls) or "QWidget", name=name or "custom", calls=lines)

# --------------------------------------------------------------------------
# Универсальный виджет из Qt Designer.
# Все свойства из .ui приходят одним JSON-словарём в порт props.
# --------------------------------------------------------------------------

_TEXT_SETTERS = {
    "placeholderText": "setPlaceholderText", "prefix": "setPrefix",
    "suffix": "setSuffix", "currentText": "setCurrentText",
    "displayFormat": "setDisplayFormat", "windowTitle": "setWindowTitle",
    "statusTip": "setStatusTip", "whatsThis": "setWhatsThis",
    "shortcut": "setShortcut", "toolTip": "setToolTip",
    "accessibleName": "setAccessibleName",
}

_NUM_SETTERS = {
    "minimum": "setMinimum", "maximum": "setMaximum", "value": "setValue",
    "singleStep": "setSingleStep", "decimals": "setDecimals",
    "currentIndex": "setCurrentIndex", "maxLength": "setMaxLength",
    "digitCount": "setDigitCount", "tickInterval": "setTickInterval",
    "indent": "setIndent", "margin": "setMargin",
    "columnCount": "setColumnCount", "rowCount": "setRowCount",
}

_BOOL_SETTERS = {
    "checked": "setChecked", "checkable": "setCheckable",
    "readOnly": "setReadOnly", "wordWrap": "setWordWrap",
    "flat": "setFlat", "enabled": "setEnabled",
    "editable": "setEditable", "sortingEnabled": "setSortingEnabled",
    "notchesVisible": "setNotchesVisible", "calendarPopup": "setCalendarPopup",
    "textVisible": "setTextVisible", "openExternalLinks": "setOpenExternalLinks",
    "scaledContents": "setScaledContents", "tracking": "setTracking",
    "autoFillBackground": "setAutoFillBackground",
    "gridVisible": "setGridVisible", "movable": "setMovable",
    "tabsClosable": "setTabsClosable", "invertedAppearance": "setInvertedAppearance",
}

_ENUM_SETTERS = {
    "alignment": ("setAlignment", "QtCore.Qt.AlignmentFlag"),
    "orientation": ("setOrientation", "QtCore.Qt.Orientation"),
    "frameShape": ("setFrameShape", "QtWidgets.QFrame.Shape"),
    "frameShadow": ("setFrameShadow", "QtWidgets.QFrame.Shadow"),
    "tickPosition": ("setTickPosition", "QtWidgets.QSlider.TickPosition"),
    "echoMode": ("setEchoMode", "QtWidgets.QLineEdit.EchoMode"),
    "standardButtons": ("setStandardButtons",
                        "QtWidgets.QDialogButtonBox.StandardButton"),
    "textFormat": ("setTextFormat", "QtCore.Qt.TextFormat"),
    "tabPosition": ("setTabPosition", "QtWidgets.QTabWidget.TabPosition"),
    "selectionMode": ("setSelectionMode",
                      "QtWidgets.QAbstractItemView.SelectionMode"),
}

DESIGNER_CLASSES = {
    "QPushButton", "QToolButton", "QCommandLinkButton", "QDialogButtonBox",
    "QLabel", "QLineEdit", "QTextEdit", "QPlainTextEdit", "QTextBrowser",
    "QCheckBox", "QRadioButton", "QComboBox", "QFontComboBox",
    "QListWidget", "QListView", "QTreeWidget", "QTreeView", "QTableWidget",
    "QTableView", "QColumnView", "QUndoView",
    "QGroupBox", "QFrame", "QWidget", "Line", "QTabWidget", "QToolBox",
    "QStackedWidget", "QSplitter",
    "QSpinBox", "QDoubleSpinBox", "QTimeEdit", "QDateEdit", "QDateTimeEdit",
    "QSlider", "QDial", "QScrollBar", "QLCDNumber", "QProgressBar",
    "QCalendarWidget", "QKeySequenceEdit", "QGraphicsView", "QOpenGLWidget",
    "QQuickWidget", "QWebEngineView", "QScrollArea", "QMdiArea",
    "QDockWidget", "QToolBar",
}

_ITEM_HOLDERS = ("QComboBox", "QFontComboBox", "QListWidget")


def _as_bool(raw):
    """Мягкое приведение свойства .ui к True/False/None."""
    if isinstance(raw, bool):
        return raw
    text = txt(raw).strip().lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off"):
        return False
    return None


def _as_number(raw):
    """Число из свойства .ui или None."""
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return raw
    text = txt(raw).strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _enum_names(raw):
    """Имена констант из записей вида 'Qt::AlignLeft|Qt::AlignTop'."""
    names = []
    for chunk in txt(raw).replace("|", " ").split():
        part = chunk.split("::")[-1].strip()
        if not part:
            continue
        for prefix in ("Align", "Q"):
            if part.startswith(prefix) and prefix == "Align":
                break
        if part.replace("_", "").isalnum():
            names.append(part)
    return names


def _parse_props(raw):
    """Словарь свойств из JSON/литерала Python. Без eval."""
    if isinstance(raw, dict):
        return dict(raw)
    text = txt(raw).strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        try:
            data = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return {}
    return dict(data) if isinstance(data, dict) else {}


def _parse_size(raw):
    """Пара (ширина, высота) из строки или списка. Без eval."""
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        try:
            return int(raw[0]), int(raw[1])
        except (TypeError, ValueError):
            return None
    text = txt(raw).strip()
    if not text or text in ("None", "''"):
        return None
    try:
        data = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        numbers = [p for p in text.replace("(", " ").replace(")", " ")
                   .replace(",", " ").split() if p.lstrip("-").isdigit()]
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        return None
    if isinstance(data, (list, tuple)) and len(data) >= 2:
        try:
            return int(data[0]), int(data[1])
        except (TypeError, ValueError):
            return None
    return None


def _designer_font(raw):
    """Описание шрифта для генератора кода."""
    data = _parse_props(raw)
    if not data:
        return None
    font = {}
    if txt(data.get("family")):
        font["family"] = txt(data["family"])
    size = _as_number(data.get("pointsize") or data.get("pointSize"))
    if size:
        font["size"] = int(size)
    for key in ("bold", "italic", "underline", "strikeout"):
        state = _as_bool(data.get(key))
        if state:
            font[key] = True
    return font or None


def _split_items(raw):
    """Список элементов из списка или текста с запятыми."""
    if isinstance(raw, (list, tuple)):
        return [txt(v) for v in raw if txt(v)]
    text = txt(raw)
    if not text:
        return []
    sep = "\n" if "\n" in text else ","
    return [p.strip() for p in text.split(sep) if p.strip()]


@nd("Designer: виджет",
    inputs=[("class_name", "text", "QWidget"), ("name", "text", "widget"),
            ("text", "text", ""), ("items", "text", ""),
            ("children", "list", None), ("orientation", "text", ""),
            ("x", "number", 0), ("y", "number", 0),
            ("width", "number", 100), ("height", "number", 30),
            ("toolTip", "text", ""), ("styleSheet", "text", ""),
            ("minimum", "text", ""), ("maximum", "text", ""),
            ("value", "text", ""), ("checked", "text", ""),
            ("enabled", "text", ""), ("visible", "text", ""),
            ("currentIndex", "text", ""), ("minSize", "text", ""),
            ("maxSize", "text", ""), ("font", "text", ""),
            {"name": "props", "type": "text", "default": "",
             "multiline": True,
             "hint": "Все свойства из .ui в виде JSON"},
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["designer", "absolute", "ui"])
def designer_widget(class_name="QWidget", name="widget", text="", items="",
                    children=None, orientation="", x=0, y=0, width=100,
                    height=30, toolTip="", styleSheet="", minimum="",
                    maximum="", value="", checked="", enabled="", visible="",
                    currentIndex="", minSize="", maxSize="", font="",
                    props="", style=""):
    """Виджет из Qt Designer: координаты, размеры и все свойства из .ui."""
    cls = txt(class_name) or "QWidget"
    if cls not in DESIGNER_CLASSES:
        cls = "QWidget"
    original_cls = cls
    module = "QtWidgets"
    if cls == "Line":
        cls = "QFrame"
    elif cls == "QWebEngineView":
        module = "QtWebEngineWidgets"
    elif cls == "QOpenGLWidget":
        module = "QtOpenGLWidgets"
    elif cls == "QQuickWidget":
        module = "QtQuickWidgets"

    data = _parse_props(props)
    # Отдельные входы ноды дополняют, но не затирают словарь props.
    legacy = {"text": text, "toolTip": toolTip, "styleSheet": styleSheet,
              "minimum": minimum, "maximum": maximum, "value": value,
              "checked": checked, "enabled": enabled, "visible": visible,
              "currentIndex": currentIndex, "orientation": orientation}
    for key, raw in legacy.items():
        if key not in data and txt(raw):
            data[key] = txt(raw)

    calls = [f"setGeometry({int(num(x))}, {int(num(y))}, "
             f"{int(num(width, 100))}, {int(num(height, 30))})"]

    # --- текстовые свойства с учётом класса ---
    main_text = txt(data.get("text") or "")
    if main_text:
        if cls in ("QPushButton", "QToolButton", "QCommandLinkButton",
                   "QLabel", "QCheckBox", "QRadioButton", "QLineEdit"):
            calls.append(f"setText({_q(main_text)})")
        elif cls == "QGroupBox":
            calls.append(f"setTitle({_q(main_text)})")
        elif cls in ("QTextEdit", "QPlainTextEdit", "QTextBrowser"):
            calls.append(f"setPlainText({_q(main_text)})")
        else:
            calls.append(f"setWindowTitle({_q(main_text)})")
    if txt(data.get("title")) and cls in ("QGroupBox", "QDockWidget"):
        calls.append(f"setTitle({_q(data['title'])})")
    if txt(data.get("plainText")) and cls in ("QTextEdit", "QPlainTextEdit",
                                              "QTextBrowser"):
        calls.append(f"setPlainText({_q(data['plainText'])})")
    if txt(data.get("html")) and cls in ("QTextEdit", "QTextBrowser"):
        calls.append(f"setHtml({_q(data['html'])})")
    for key, setter in _TEXT_SETTERS.items():
        if txt(data.get(key)):
            calls.append(f"{setter}({_q(data[key])})")

    # --- числа, флаги, перечисления ---
    for key, setter in _NUM_SETTERS.items():
        if key not in data:
            continue
        number = _as_number(data.get(key))
        if number is None:
            continue
        if key == "decimals" and cls != "QDoubleSpinBox":
            continue
        as_float = cls == "QDoubleSpinBox" and key in (
            "minimum", "maximum", "value", "singleStep")
        calls.append(f"{setter}({number if as_float else int(number)})")
    for key, setter in _BOOL_SETTERS.items():
        state = _as_bool(data.get(key))
        if state is not None:
            calls.append(f"{setter}({state})")
    for key, (setter, prefix) in _ENUM_SETTERS.items():
        if key not in data:
            continue
        names = _enum_names(data.get(key))
        if not names:
            continue
        if key == "orientation" and cls not in ("QSlider", "QScrollBar",
                                                "QSplitter", "QProgressBar",
                                                "QDial"):
            continue
        expression = " | ".join(f"{prefix}.{n}" for n in names)
        calls.append(f"{setter}({expression})")

    # --- видимость и размеры ---
    if _as_bool(data.get("visible")) is False:
        calls.append("hide()")
    for key, setter in (("minimumSize", "setMinimumSize"),
                        ("maximumSize", "setMaximumSize")):
        size = _parse_size(data.get(key))
        if size:
            calls.append(f"{setter}({size[0]}, {size[1]})")
    for raw, setter in ((minSize, "setMinimumSize"), (maxSize, "setMaximumSize")):
        size = _parse_size(raw)
        if size and f"{setter}({size[0]}, {size[1]})" not in calls:
            calls.append(f"{setter}({size[0]}, {size[1]})")

    # --- элементы списков ---
    item_list = _split_items(data.get("__items__") or items)
    if item_list and cls in _ITEM_HOLDERS:
        calls.append(f"addItems({item_list!r})")

    # --- дата и время ---
    if txt(data.get("date")) and cls in ("QDateEdit", "QDateTimeEdit",
                                         "QCalendarWidget"):
        calls.append("setDate(QtCore.QDate.fromString("
                     f"{_q(data['date'])}, 'yyyy-MM-dd'))")
    if txt(data.get("time")) and cls in ("QTimeEdit", "QDateTimeEdit"):
        calls.append("setTime(QtCore.QTime.fromString("
                     f"{_q(data['time'])}, 'HH:mm:ss'))")

    # --- особые случаи классов ---
    if original_cls == "Line":
        vertical = "Vertical" in txt(data.get("orientation"))
        shape = "VLine" if vertical else "HLine"
        calls.append(f"setFrameShape(QtWidgets.QFrame.Shape.{shape})")
        calls.append("setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)")
    if cls in ("QDial", "QSlider", "QScrollBar", "QProgressBar") \
            and "minimum" not in data and "maximum" not in data:
        calls.append("setRange(0, 100)")
    if cls == "QDialogButtonBox" and "standardButtons" not in data:
        calls.append("setStandardButtons("
                     "QtWidgets.QDialogButtonBox.StandardButton.Ok | "
                     "QtWidgets.QDialogButtonBox.StandardButton.Cancel)")
    if cls == "QGraphicsView":
        calls.append("setScene(QtWidgets.QGraphicsScene())")
    if original_cls == "QWebEngineView":
        url = txt(data.get("url")) or "about:blank"
        calls.append(f"setUrl(QtCore.QUrl({_q(url)}))")

    child_nodes = [c for c in lst(children) if isinstance(c, dict)]
    w = _common(u.widget(cls, name=name or u.ident(cls), calls=calls,
                         module=module, children=child_nodes), style=style)

    # --- дополнительные данные для генератора ---
    headers = data.get("__headers__")
    if isinstance(headers, (list, tuple)) and headers:
        w["extra"]["headers"] = [txt(h) for h in headers]
    rows = data.get("__rows__")
    if isinstance(rows, (list, tuple)) and rows:
        if cls in ("QTreeWidget", "QTreeView"):
            w["extra"]["tree_rows"] = [list(r) for r in rows]
        else:
            w["extra"]["table_rows"] = [[txt(c) for c in r] for r in rows]
    pages = data.get("__pages__")
    if isinstance(pages, (list, tuple)) and pages:
        w["extra"]["page_titles"] = [txt(p) for p in pages]
    if txt(data.get("pixmap")) and cls == "QLabel":
        w["extra"]["image"] = {"path": txt(data["pixmap"]), "width": 0}
    font_spec = _designer_font(data.get("font") or font)
    if font_spec:
        w["extra"]["font"] = font_spec
    if cls == "QScrollArea":
        w["extra"]["scroll"] = True
    if child_nodes and cls in ("QGroupBox", "QFrame", "QScrollArea",
                              "QDockWidget", "QWidget") \
            and "page_titles" not in w["extra"]:
        w["extra"]["absolute_container"] = True
    return w

@nd("Designer: абсолютный контейнер", inputs=[("items", "list", None), ("name", "text", "central")],
    outputs=[("widget", "widget")], tags=["designer", "absolute", "container"])
def designer_container(items, name):
    """Контейнер без layout: виджеты внутри стоят по координатам из Qt Designer."""
    w = u.widget("QWidget", name=name or "central", children=[w for w in lst(items) if isinstance(w, dict)])
    w["extra"]["absolute_container"] = True
    return w


@nd("Встроенный браузер", inputs=[("url", "text", "https://www.qt.io"), ("name", "text", "web")], outputs=[("widget", "widget")], tags=["browser", "webengine", "интернет"])
def web_engine_view(url, name):
    """Настоящий QWebEngineView. Требуется пакет PyQt6-WebEngine."""
    return u.widget("QWebEngineView", name=name or "web", module="QtWebEngineWidgets", calls=[f"setUrl(QtCore.QUrl({_q(url)}))"])
