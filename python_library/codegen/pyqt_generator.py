"""Генератор кода PyQt6 из описания окна (uispec).

Главная функция — generate_window_module(spec) -> {'code', 'warnings', 'helpers'}.
Код собирается как обычный текст, PyQt6 здесь не требуется.
"""

HELPER_CODE = '''
def get_text(widget):
    """Универсальное чтение текста из разных виджетов."""
    for name in ("text", "toPlainText", "currentText", "value"):
        method = getattr(widget, name, None)
        if callable(method):
            return str(method())
    return ""


def set_text(widget, value):
    """Универсальная запись текста в виджет."""
    for name in ("setPlainText", "setText", "setCurrentText"):
        method = getattr(widget, name, None)
        if callable(method):
            method(str(value))
            return True
    return False


def safe_eval(expression):
    """Безопасное вычисление арифметического выражения."""
    import math
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"abs": abs, "round": round, "min": min, "max": max})
    return eval(str(expression), {"__builtins__": {}}, allowed)
'''.strip()

PAINT_CANVAS = '''
class PaintCanvas(QtWidgets.QWidget):
    """Холст, рисующий список фигур средствами QPainter."""

    def __init__(self, shapes=None, background="#1c1f26", parent=None):
        super().__init__(parent)
        self.shapes = list(shapes or [])
        self.background = background

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QtGui.QColor(self.background))
        for item in self.shapes:
            self._draw(painter, item)
        painter.end()

    def _pen(self, style):
        stroke = (style or {}).get("stroke") or ""
        width = int((style or {}).get("width") or 0)
        if not stroke or width <= 0:
            return QtGui.QPen(QtCore.Qt.PenStyle.NoPen)
        return QtGui.QPen(QtGui.QColor(stroke), width)

    def _brush(self, style):
        fill = (style or {}).get("fill") or ""
        if not fill:
            return QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush)
        return QtGui.QBrush(QtGui.QColor(fill))

    def _draw(self, painter, item):
        kind = item.get("shape")
        style = item.get("style") or {}
        painter.setPen(self._pen(style))
        painter.setBrush(self._brush(style))
        if kind == "rect":
            rect = QtCore.QRectF(item.get("x", 0), item.get("y", 0),
                                 item.get("w", 10), item.get("h", 10))
            radius = float(item.get("radius") or 0)
            if radius > 0:
                painter.drawRoundedRect(rect, radius, radius)
            else:
                painter.drawRect(rect)
        elif kind == "ellipse":
            painter.drawEllipse(QtCore.QRectF(item.get("x", 0), item.get("y", 0),
                                              item.get("w", 10), item.get("h", 10)))
        elif kind == "line":
            painter.drawLine(QtCore.QPointF(item.get("x1", 0), item.get("y1", 0)),
                             QtCore.QPointF(item.get("x2", 0), item.get("y2", 0)))
        elif kind == "polygon":
            points = [QtCore.QPointF(p[0], p[1])
                      for p in item.get("points") or [] if len(p) >= 2]
            if points:
                painter.drawPolygon(QtGui.QPolygonF(points))
        elif kind == "text":
            font = painter.font()
            font.setPointSize(int(item.get("size") or 12))
            font.setBold(bool(item.get("bold")))
            painter.setFont(font)
            color = style.get("fill") or "#ffffff"
            painter.setPen(QtGui.QPen(QtGui.QColor(color)))
            painter.drawText(QtCore.QPointF(item.get("x", 0), item.get("y", 0)),
                             str(item.get("text", "")))
        elif kind == "grid":
            step = int(item.get("step") or 25)
            pen = self._pen(style)
            painter.setPen(pen)
            width, height = self.width(), self.height()
            x = 0
            while x <= width:
                painter.drawLine(x, 0, x, height)
                x += step
            y = 0
            while y <= height:
                painter.drawLine(0, y, width, y)
                y += step
'''.strip()

CHART_VIEW = '''
class ChartView(QtWidgets.QWidget):
    """Простая диаграмма (столбцы, линия или круговая)."""

    COLORS = ["#3d7eff", "#5fd39a", "#ffc14d", "#c792ea", "#ff6b6b",
              "#4ecdc4", "#f39c12", "#9b59b6"]

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = dict(data or {})

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QtGui.QColor("#262b34"))
        values = [float(v) for v in self.data.get("values") or []]
        labels = [str(v) for v in self.data.get("labels") or []]
        title = str(self.data.get("title") or "")
        kind = self.data.get("chart") or "bar"
        painter.setPen(QtGui.QPen(QtGui.QColor("#e6e9ef")))
        if title:
            painter.drawText(10, 18, title)
        if not values:
            painter.drawText(10, 40, "Нет данных")
            painter.end()
            return
        top = 30
        area = QtCore.QRectF(40, top, max(10, self.width() - 60),
                             max(10, self.height() - top - 30))
        if kind == "pie":
            total = sum(abs(v) for v in values) or 1.0
            start = 0
            size = min(area.width(), area.height())
            box = QtCore.QRectF(area.x(), area.y(), size, size)
            for i, value in enumerate(values):
                span = int(360 * 16 * abs(value) / total)
                painter.setBrush(QtGui.QBrush(
                    QtGui.QColor(self.COLORS[i % len(self.COLORS)])))
                painter.setPen(QtGui.QPen(QtGui.QColor("#1c1f26")))
                painter.drawPie(box, start, span)
                start += span
        elif kind == "line":
            high, low = max(values), min(values + [0])
            span = (high - low) or 1.0
            step = area.width() / max(1, len(values) - 1)
            painter.setPen(QtGui.QPen(QtGui.QColor(self.COLORS[0]), 2))
            previous = None
            for i, value in enumerate(values):
                x = area.x() + i * step
                y = area.bottom() - (value - low) / span * area.height()
                point = QtCore.QPointF(x, y)
                if previous is not None:
                    painter.drawLine(previous, point)
                previous = point
        else:
            high = max(values + [0]) or 1.0
            low = min(values + [0])
            span = (high - low) or 1.0
            width = area.width() / max(1, len(values)) * 0.7
            step = area.width() / max(1, len(values))
            for i, value in enumerate(values):
                height = (value - low) / span * area.height()
                x = area.x() + i * step + (step - width) / 2
                y = area.bottom() - height
                painter.setBrush(QtGui.QBrush(
                    QtGui.QColor(self.COLORS[i % len(self.COLORS)])))
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.drawRect(QtCore.QRectF(x, y, width, height))
                if i < len(labels):
                    painter.setPen(QtGui.QPen(QtGui.QColor("#98a2b3")))
                    painter.drawText(QtCore.QRectF(x - 10, area.bottom() + 4,
                                                   width + 20, 18),
                                     QtCore.Qt.AlignmentFlag.AlignCenter,
                                     labels[i])
        painter.end()
'''.strip()


from python_library.codegen.game_helpers import TETRIS_WIDGET
from python_library.codegen.runtime_support import LIVE_CANVAS_CODE, RUNTIME_CODE


class _Emitter:
    """Собирает строки кода для метода _build_ui."""

    def __init__(self):
        self.lines = []
        self.warnings = []
        self.helpers = set()
        self.used_names = {}

    def add(self, line=""):
        self.lines.append(line)

    def unique(self, name, fallback="widget"):
        base = name or fallback
        if base not in self.used_names:
            self.used_names[base] = 1
            return base
        self.used_names[base] += 1
        new_name = f"{base}_{self.used_names[base]}"
        self.warnings.append(
            f"Имя '{base}' используется несколько раз, переименовано в '{new_name}'")
        return new_name


def _emit_widget(spec, emitter, indent="        "):
    """Создаёт код виджета, возвращает его имя (self.<name>)."""
    name = emitter.unique(spec.get("name") or "widget")
    spec["name"] = name
    cls = spec.get("cls") or "QWidget"
    helper = spec.get("helper")
    extra = spec.get("extra") or {}
    if helper == "LiveCanvas":
        emitter.helpers.add("LiveCanvas")
        columns = int(extra.get("columns") or 20)
        rows = int(extra.get("rows") or 20)
        cell_size = int(extra.get("cell_size") or 24)
        background = str(extra.get("background") or "#1c1f26")
        emitter.add(
            f"{indent}self.{name} = LiveCanvas({name!r}, self, {columns}, "
            f"{rows}, {cell_size}, {background!r})")
    elif helper == "PaintCanvas":
        emitter.helpers.add("PaintCanvas")
        shapes = extra.get("shapes") or []
        background = (extra.get("canvas") or {}).get("background", "#1c1f26")
        emitter.add(f"{indent}self.{name} = PaintCanvas({shapes!r}, "
                    f"{background!r}, self)")
    elif helper == "TetrisWidget":
        emitter.helpers.add("TetrisWidget")
        emitter.add(f"{indent}self.{name} = TetrisWidget("
                    f"{extra.get('game') or {}!r}, self)")
    elif helper == "ChartView":
        emitter.helpers.add("ChartView")
        emitter.add(f"{indent}self.{name} = ChartView({extra.get('chart') or {}!r}, "
                    "self)")
    else:
        module = spec.get("module") or "QtWidgets"
        prefix = f"{module}." if module else ""
        emitter.add(f"{indent}self.{name} = {prefix}{cls}(self)")

    for call in spec.get("calls") or []:
        emitter.add(f"{indent}self.{name}.{call}")
    if spec.get("tooltip"):
        emitter.add(f"{indent}self.{name}.setToolTip({spec['tooltip']!r})")
    if spec.get("stylesheet"):
        emitter.add(f"{indent}self.{name}.setStyleSheet({spec['stylesheet']!r})")
    font = extra.get("font")
    if isinstance(font, dict):
        emitter.add(f"{indent}_font = QtGui.QFont({font.get('family', 'Segoe UI')!r}, "
                    f"{int(font.get('size', 12))})")
        emitter.add(f"{indent}_font.setBold({bool(font.get('bold'))})")
        emitter.add(f"{indent}_font.setItalic({bool(font.get('italic'))})")
        emitter.add(f"{indent}_font.setUnderline({bool(font.get('underline'))})")
        emitter.add(f"{indent}self.{name}.setFont(_font)")
    picture = extra.get("image")
    if isinstance(picture, dict) and picture.get("path"):
        emitter.add(f"{indent}_pixmap = QtGui.QPixmap({picture['path']!r})")
        if int(picture.get("width") or 0) > 0:
            emitter.add(f"{indent}_pixmap = _pixmap.scaledToWidth("
                        f"{int(picture['width'])}, "
                        "QtCore.Qt.TransformationMode.SmoothTransformation)")
        emitter.add(f"{indent}self.{name}.setPixmap(_pixmap)")
    headers = extra.get("headers")
    if isinstance(headers, (list, tuple)) and headers:
        heads = [str(h) for h in headers]
        if cls in ("QTreeWidget", "QTreeView"):
            emitter.add(f"{indent}self.{name}.setHeaderLabels({heads!r})")
        elif cls in ("QTableWidget", "QTableView"):
            emitter.add(f"{indent}self.{name}.setColumnCount({len(heads)})")
            emitter.add(f"{indent}self.{name}."
                        f"setHorizontalHeaderLabels({heads!r})")

    rows = extra.get("table_rows")
    if isinstance(rows, (list, tuple)) and rows:
        cells = [[str(c) for c in row] for row in rows]
        width = max(len(row) for row in cells)
        emitter.add(f"{indent}self.{name}.setRowCount({len(cells)})")
        emitter.add(f"{indent}if self.{name}.columnCount() < {width}:")
        emitter.add(f"{indent}    self.{name}.setColumnCount({width})")
        emitter.add(f"{indent}for _row, _cells in enumerate({cells!r}):")
        emitter.add(f"{indent}    for _col, _value in enumerate(_cells):")
        emitter.add(f"{indent}        self.{name}.setItem(_row, _col, "
                    "QtWidgets.QTableWidgetItem(str(_value)))")

    tree_rows = extra.get("tree_rows")
    if isinstance(tree_rows, (list, tuple)) and tree_rows:
        prepared = [[int(row[0] or 0)] + [str(c) for c in row[1:]]
                    for row in tree_rows if row]
        emitter.add(f"{indent}_stack = {{}}")
        emitter.add(f"{indent}for _row in {prepared!r}:")
        emitter.add(f"{indent}    _level, _texts = _row[0], "
                    "[str(v) for v in _row[1:]]")
        emitter.add(f"{indent}    _item = QtWidgets.QTreeWidgetItem(_texts)")
        emitter.add(f"{indent}    _parent = _stack.get(_level - 1)")
        emitter.add(f"{indent}    if _level > 0 and _parent is not None:")
        emitter.add(f"{indent}        _parent.addChild(_item)")
        emitter.add(f"{indent}    else:")
        emitter.add(f"{indent}        self.{name}.addTopLevelItem(_item)")
        emitter.add(f"{indent}    _stack[_level] = _item")
        emitter.add(f"{indent}self.{name}.expandAll()")

    content = spec.get("content")
    if isinstance(content, dict):
        if extra.get("scroll"):
            inner = emitter.unique(f"{name}_inner")
            emitter.add(f"{indent}self.{inner} = QtWidgets.QWidget()")
            child = _emit_any(content, emitter, indent)
            if child:
                emitter.add(f"{indent}self.{inner}.setLayout({child})")
            emitter.add(f"{indent}self.{name}.setWidget(self.{inner})")
        else:
            child = _emit_any(content, emitter, indent)
            if child:
                emitter.add(f"{indent}self.{name}.setLayout({child})")
    page_titles = [str(t) for t in (extra.get("page_titles") or [])]
    for page_index, child_spec in enumerate(spec.get("children") or []):
        if page_titles and cls in ("QTabWidget", "QToolBox",
                                   "QStackedWidget"):
            child = _emit_any(child_spec, emitter, indent)
            if not child:
                continue
            title = page_titles[page_index] if page_index < len(page_titles) \
                else f"Страница {page_index + 1}"
            if child_spec.get("kind") == "layout":
                wrap = emitter.unique(f"{name}_page")
                emitter.add(f"{indent}self.{wrap} = QtWidgets.QWidget(self)")
                emitter.add(f"{indent}self.{wrap}.setLayout({child})")
                child = f"self.{wrap}"
            if cls == "QStackedWidget":
                emitter.add(f"{indent}self.{name}.addWidget({child})")
            elif cls == "QToolBox":
                emitter.add(f"{indent}self.{name}.addItem({child}, {title!r})")
            else:
                emitter.add(f"{indent}self.{name}.addTab({child}, {title!r})")
            continue
        child = _emit_any(child_spec, emitter, indent)
        if child:
            if extra.get("absolute_container"):
                emitter.add(f"{indent}{child}.setParent(self.{name})")
                emitter.add(f"{indent}{child}.show()")
            elif child_spec.get("kind") == "layout":
                _wrap = emitter.unique(f"{name}_wrap")
                emitter.add(f"{indent}self.{_wrap} = QtWidgets.QWidget(self)")
                emitter.add(f"{indent}self.{_wrap}.setLayout({child})")
                emitter.add(f"{indent}self.{name}.addWidget(self.{_wrap})")
            else:
                emitter.add(f"{indent}self.{name}.addWidget({child})")
    for tab in spec.get("tabs") or []:
        page = emitter.unique(f"{name}_page")
        emitter.add(f"{indent}self.{page} = QtWidgets.QWidget()")
        inner = tab.get("content")
        if isinstance(inner, dict):
            built = _emit_any(inner, emitter, indent)
            if built:
                emitter.add(f"{indent}self.{page}.setLayout({built})")
        emitter.add(f"{indent}self.{name}.addTab(self.{page}, "
                    f"{str(tab.get('title') or 'Вкладка')!r})")
    return f"self.{name}"


def _emit_layout(spec, emitter, indent="        "):
    """Создаёт код компоновки и возвращает имя переменной."""
    name = emitter.unique(spec.get("name") or "layout")
    cls = spec.get("cls") or "QVBoxLayout"
    ref = f"self.{name}"
    emitter.add(f"{indent}{ref} = QtWidgets.{cls}()")
    for call in spec.get("calls") or []:
        emitter.add(f"{indent}{ref}.{call}")

    for child in spec.get("children") or []:
        if not isinstance(child, dict):
            continue
        if child.get("kind") == "spacer":
            if child.get("mode") == "spacing":
                emitter.add(f"{indent}{ref}.addSpacing({int(child.get('size') or 0)})")
            else:
                emitter.add(f"{indent}{ref}.addStretch(1)")
            continue
        built = _emit_any(child, emitter, indent)
        if not built:
            continue
        adder = "addLayout" if child.get("kind") == "layout" else "addWidget"
        emitter.add(f"{indent}{ref}.{adder}({built})")

    for cell in spec.get("grid") or []:
        item = cell.get("item")
        if not isinstance(item, dict):
            continue
        built = _emit_any(item, emitter, indent)
        if not built:
            continue
        adder = "addLayout" if item.get("kind") == "layout" else "addWidget"
        emitter.add(f"{indent}{ref}.{adder}({built}, {int(cell.get('row') or 0)}, "
                    f"{int(cell.get('col') or 0)}, "
                    f"{int(cell.get('rowspan') or 1)}, "
                    f"{int(cell.get('colspan') or 1)})")

    for row in spec.get("form") or []:
        item = row.get("item")
        if not isinstance(item, dict):
            continue
        built = _emit_any(item, emitter, indent)
        if built:
            emitter.add(f"{indent}{ref}.addRow({str(row.get('label') or '')!r}, "
                        f"{built})")
    return ref


def _emit_any(spec, emitter, indent="        "):
    """Разбирает, что перед нами: виджет, компоновка или отступ."""
    if not isinstance(spec, dict):
        return None
    kind = spec.get("kind")
    if kind == "widget":
        return _emit_widget(spec, emitter, indent)
    if kind == "layout":
        return _emit_layout(spec, emitter, indent)
    if kind == "tab":
        return _emit_any(spec.get("content"), emitter, indent)
    if kind == "spacer":
        return None
    emitter.warnings.append(f"Неизвестный элемент интерфейса: {kind}")
    return None


def _collect_widget_names(spec, found):
    if not isinstance(spec, dict):
        return
    
    # 1. Если это виджет и у него есть имя — фиксируем его
    if spec.get("kind") == "widget" and spec.get("name"):
        found.add(spec["name"])
        
    # 2. Проверяем абсолютно все ключи, где могут скрываться вложенные элементы
    # Проверяем одиночные вложенные свойства
    for key in ("content", "item"):
        if isinstance(spec.get(key), dict):
            _collect_widget_names(spec[key], found)
            
    # Проверяем списки элементов (включая разметку, сетки, формы и табы)
    for key in ("children", "tabs", "grid", "form"):
        for item in spec.get(key) or []:
            if isinstance(item, dict):
                # Извлекаем чистый словарь элемента, минуя возможные None в подсистемах
                target_item = item.get("item") or item.get("content") or item
                if isinstance(target_item, dict):
                    _collect_widget_names(target_item, found)

def _slot_body(actions, emitter, indent="        "):
    lines = []
    for act in actions or []:
        if not isinstance(act, dict):
            continue
        for imp in act.get("imports") or []:
            emitter.helpers.add(("import", imp))
        code = str(act.get("code") or "pass")
        for line in code.splitlines():
            lines.append(f"{indent}{line}" if line.strip() else "")
    if not lines:
        lines.append(f"{indent}pass")
    return lines


def generate_window_module(spec):
    """Собирает исходный текст модуля ui_main.py."""
    if not isinstance(spec, dict) or spec.get("kind") != "window":
        raise ValueError("Ожидается описание окна (нода 'Окно приложения')")

    emitter = _Emitter()
    all_bindings = [b for b in spec.get("bindings") or []
                    if isinstance(b, dict)]
    runtime_items = [b for b in all_bindings
                     if str(b.get("kind", "")).startswith("runtime_")]
    states = [b for b in runtime_items if b.get("kind") == "runtime_state"]
    events = [b for b in runtime_items if b.get("kind") == "runtime_event"]
    for index, event in enumerate(events):
        event["_slot"] = f"_nf_event_{index}"
    has_runtime = bool(runtime_items)
    body = []
    content = spec.get("content")
    root = _emit_any(content, emitter, "        ") if content else None
    build_lines = list(emitter.lines)
    # Сам по себе живой холст тоже нуждается в пустых runtime-обработчиках.
    has_runtime = has_runtime or "LiveCanvas" in emitter.helpers

    window_cls = spec.get("cls") or "QMainWindow"
    is_main = window_cls == "QMainWindow"

    header = [
        '"""Интерфейс приложения. Файл создан автоматически в NodeFlow Studio."""',
        "",
        "try:",
        "    from PyQt6 import QtCore, QtGui, QtWidgets",
        "    try: from PyQt6 import QtWebEngineWidgets",
        "    except Exception: QtWebEngineWidgets = None",
        "    try: from PyQt6 import QtOpenGLWidgets",
        "    except Exception: QtOpenGLWidgets = None",
        "    try: from PyQt6 import QtQuickWidgets",
        "    except Exception: QtQuickWidgets = None",
        "    try: from PyQt6 import QtSvgWidgets",
        "    except Exception: QtSvgWidgets = None",
        "    try: from PyQt6 import QtPrintSupport",
        "    except Exception: QtPrintSupport = None",
        "except Exception:",
        "    from PySide6 import QtCore, QtGui, QtWidgets",
        "    try: from PySide6 import QtWebEngineWidgets",
        "    except Exception: QtWebEngineWidgets = None",
        "    try: from PySide6 import QtOpenGLWidgets",
        "    except Exception: QtOpenGLWidgets = None",
        "    try: from PySide6 import QtQuickWidgets",
        "    except Exception: QtQuickWidgets = None",
        "    try: from PySide6 import QtSvgWidgets",
        "    except Exception: QtSvgWidgets = None",
        "    try: from PySide6 import QtPrintSupport",
        "    except Exception: QtPrintSupport = None",
    ]
    extra_imports = sorted({i[1] for i in emitter.helpers
                            if isinstance(i, tuple) and i[0] == "import"})
    header.extend(extra_imports)
    header.append("")
    header.append("")
    header.append(HELPER_CODE)
    header.append("")
    if has_runtime or "LiveCanvas" in emitter.helpers:
        header.append("")
        header.append(RUNTIME_CODE)
        header.append("")
    if "LiveCanvas" in emitter.helpers:
        header.append("")
        header.append(LIVE_CANVAS_CODE)
        header.append("")
    if "PaintCanvas" in emitter.helpers:
        header.append("")
        header.append(PAINT_CANVAS)
        header.append("")
    if "ChartView" in emitter.helpers:
        header.append("")
        header.append(CHART_VIEW)
        header.append("")
    if "TetrisWidget" in emitter.helpers:
        header.append("")
        header.append(TETRIS_WIDGET)
        header.append("")

    body.append("")
    body.append(f"class MainWindow(QtWidgets.{window_cls}):")
    body.append('    """Главное окно приложения."""')
    body.append("")
    body.append("    def __init__(self, parent=None):")
    body.append("        super().__init__(parent)")
    if has_runtime or "LiveCanvas" in emitter.helpers:
        body.append("        self._nf_state = {}")
        body.append("        self._nf_timers = {}")
        body.append("        self._nf_keys = set()")
        body.append("        self._nf_mouse = {'x': 0, 'y': 0, 'col': 0, 'row': 0, 'button': ''}")
    body.append(f"        self.setWindowTitle({str(spec.get('title') or '')!r})")
    body.append(f"        self.resize({int(spec.get('width') or 800)}, "
                f"{int(spec.get('height') or 600)})")
    window_extra = spec.get("extra") or {}
    if int(window_extra.get("minimum_width") or 0) > 0:
        body.append(
            f"        self.setMinimumWidth({int(window_extra['minimum_width'])})")
    if int(window_extra.get("minimum_height") or 0) > 0:
        body.append(
            f"        self.setMinimumHeight({int(window_extra['minimum_height'])})")
    if int(window_extra.get("maximum_width") or 16777215) < 16777215:
        body.append(
            f"        self.setMaximumWidth({int(window_extra['maximum_width'])})")
    if int(window_extra.get("maximum_height") or 16777215) < 16777215:
        body.append(
            f"        self.setMaximumHeight({int(window_extra['maximum_height'])})")
    opacity = float(window_extra.get("opacity", 1.0) or 0.0)
    if opacity < 1.0:
        body.append(f"        self.setWindowOpacity({max(0.0, opacity)!r})")
    if window_extra.get("always_on_top"):
        body.append(
            "        self.setWindowFlag("
            "QtCore.Qt.WindowType.WindowStaysOnTopHint, True)")
    if window_extra.get("frameless"):
        body.append(
            "        self.setWindowFlag("
            "QtCore.Qt.WindowType.FramelessWindowHint, True)")
    if window_extra.get("font_family") or window_extra.get("font_size"):
        body.append(
            f"        self.setFont(QtGui.QFont("
            f"{str(window_extra.get('font_family') or 'Segoe UI')!r}, "
            f"{int(window_extra.get('font_size') or 10)}))")
    if spec.get("icon"):
        body.append(f"        self.setWindowIcon(QtGui.QIcon({spec['icon']!r}))")
    if spec.get("stylesheet"):
        body.append(f"        self.setStyleSheet({spec['stylesheet']!r})")
    if not spec.get("resizable", True):
        body.append("        self.setFixedSize(self.size())")
    body.append("        self._build_ui()")
    body.append("        self._connect_signals()")
    if has_runtime:
        body.append("        self._setup_runtime()")
    if is_main and spec.get("menus"):
        body.append("        self._build_menus()")
    if is_main and spec.get("statusbar"):
        body.append(f"        self.statusBar().showMessage("
                    f"{str(spec['statusbar'])!r})")
    if spec.get("center", True):
        body.append("        self._center_on_screen()")
    body.append("")
    body.append("    def _build_ui(self):")
    body.append('        """Создаёт и раскладывает все виджеты."""')
    if build_lines:
        body.extend(build_lines)
    else:
        body.append("        pass")
    if root:
        if isinstance(content, dict) and content.get("kind") == "layout":
            if is_main:
                body.append("        central = QtWidgets.QWidget(self)")
                body.append(f"        central.setLayout({root})")
                body.append("        self.setCentralWidget(central)")
            else:
                body.append(f"        self.setLayout({root})")
        else:
            if is_main:
                body.append(f"        self.setCentralWidget({root})")
            else:
                body.append("        _wrapper = QtWidgets.QVBoxLayout()")
                body.append(f"        _wrapper.addWidget({root})")
                body.append("        self.setLayout(_wrapper)")
    initial_actions = [
        action for action in spec.get("initial_actions") or []
        if isinstance(action, dict)
    ]
    if initial_actions:
        body.extend(_slot_body(initial_actions, emitter))
    body.append("")

    known = set()
    _collect_widget_names(content, known)

    body.append("    def _connect_signals(self):")
    body.append('        """Подключает сигналы виджетов к обработчикам."""')
    bindings = [b for b in all_bindings if b.get("kind") == "binding"]
    valid = []
    for b in bindings:
        widget = b.get("widget")
        if widget not in known:
            emitter.warnings.append(
                f"Связь для '{widget}' пропущена: виджет не найден в окне")
            continue
        valid.append(b)
        body.append(f"        self.{widget}.{b.get('signal')}.connect("
                    f"self.{b.get('slot')})")
    if not valid:
        body.append("        pass")
    body.append("")

    if has_runtime:
        body.append("    def _setup_runtime(self):")
        body.append('        """Создаёт память, таймеры и стартовые события."""')
        for state in states:
            name = str(state.get("name") or "value")
            initial = str(state.get("initial") or "None")
            body.append(f"        self._nf_state[{name!r}] = {initial}")
        for event in events:
            event_type = event.get("event")
            slot = event["_slot"]
            if event_type == "timer":
                name = str(event.get("name") or slot)
                interval = max(1, int(event.get("interval") or 1000))
                body.append(f"        _timer = QtCore.QTimer(self)")
                body.append(f"        _timer.setInterval({interval})")
                body.append(f"        _timer.timeout.connect(self.{slot})")
                body.append(f"        self._nf_timers[{name!r}] = _timer")
                if event.get("autostart", True):
                    body.append("        _timer.start()")
            elif event_type == "start":
                body.append(f"        QtCore.QTimer.singleShot(0, self.{slot})")
        if not states and not events:
            body.append("        pass")
        body.append("")

        body.extend([
            "    def nf_get(self, name, default=None):",
            "        return self._nf_state.get(str(name), default)",
            "",
            "    def nf_set(self, name, value):",
            "        self._nf_state[str(name)] = value",
            "        return value",
            "",
            "    def nf_change(self, name, operation, value=None):",
            "        name = str(name)",
            "        old = self._nf_state.get(name, 0)",
            "        if operation == 'записать': new = value",
            "        elif operation == 'прибавить': new = nf_number(old) + nf_number(value)",
            "        elif operation == 'вычесть': new = nf_number(old) - nf_number(value)",
            "        elif operation == 'умножить': new = nf_number(old) * nf_number(value)",
            "        elif operation == 'переключить': new = not nf_flag(old)",
            "        elif operation == 'добавить в список': new = list(old or []) + [value]",
            "        elif operation == 'очистить список': new = []",
            "        else: new = value",
            "        self._nf_state[name] = new",
            "        return new",
            "",
            "    def nf_timer(self, name, operation='запустить', interval=None):",
            "        timer = self._nf_timers.get(str(name))",
            "        if timer is None: return False",
            "        if interval is not None: timer.setInterval(max(1, int(interval)))",
            "        if operation == 'остановить': timer.stop()",
            "        elif operation == 'переключить': timer.stop() if timer.isActive() else timer.start()",
            "        else: timer.start()",
            "        return timer.isActive()",
            "",
            "    def nf_grid_change(self, name, operation, col=0, row=0, value=0):",
            "        grid = self._nf_state.get(str(name), [])",
            "        col, row = int(col), int(row)",
            "        if operation == 'записать ячейку' and nf_grid_inside(grid, col, row):",
            "            grid[row][col] = value",
            "        elif operation == 'очистить ячейку' and nf_grid_inside(grid, col, row):",
            "            grid[row][col] = 0",
            "        elif operation == 'удалить строку' and 0 <= row < len(grid):",
            "            width = len(grid[row]); grid.pop(row); grid.insert(0, [value] * width)",
            "        elif operation == 'очистить поле':",
            "            for r in range(len(grid)): grid[r] = [value] * len(grid[r])",
            "        self._nf_state[str(name)] = grid",
            "        return grid",
            "",
            "    def nf_show(self, target, value, prefix=''):",
            "        widget = getattr(self, str(target), None)",
            "        if widget is not None: return set_text(widget, str(prefix) + str(value))",
            "        if hasattr(self, 'statusBar'): self.statusBar().showMessage(str(prefix) + str(value))",
            "        return False",
            "",
        ])

        key_events = [e for e in events if e.get("event") == "key"]
        body.append("    def keyPressEvent(self, event):")
        body.append("        _name = nf_key_name(event)")
        body.append("        self._nf_keys.add(_name)")
        for event in key_events:
            if event.get("mode", "press") != "press":
                continue
            keys = [str(k).upper() for k in event.get("keys") or []]
            condition = "True" if not keys else f"_name in {keys!r}"
            body.append(f"        if {condition}: self.{event['_slot']}()")
        body.append("        super().keyPressEvent(event)")
        body.append("")
        body.append("    def keyReleaseEvent(self, event):")
        body.append("        _name = nf_key_name(event)")
        body.append("        self._nf_keys.discard(_name)")
        for event in key_events:
            if event.get("mode") != "release":
                continue
            keys = [str(k).upper() for k in event.get("keys") or []]
            condition = "True" if not keys else f"_name in {keys!r}"
            body.append(f"        if {condition}: self.{event['_slot']}()")
        body.append("        super().keyReleaseEvent(event)")
        body.append("")

        mouse_events = [e for e in events if e.get("event") == "mouse"]
        body.append("    def _nf_canvas_mouse(self, canvas, kind, x, y, col, row, button):")
        body.append("        self._nf_mouse.update(x=x, y=y, col=col, row=row, button=button)")
        for event in mouse_events:
            canvas = str(event.get("canvas") or "")
            mode = str(event.get("mode") or "press")
            condition = f"kind == {mode!r}"
            if canvas:
                condition += f" and canvas == {canvas!r}"
            body.append(f"        if {condition}: self.{event['_slot']}()")
        if not mouse_events:
            body.append("        pass")
        body.append("")

        draw_events = [e for e in events if e.get("event") == "draw"]
        body.append("    def _nf_draw_canvas(self, canvas, draw):")
        for event in draw_events:
            canvas = str(event.get("canvas") or "")
            condition = "True" if not canvas else f"canvas == {canvas!r}"
            body.append(f"        if {condition}: self.{event['_slot']}(draw)")
        if not draw_events:
            body.append("        pass")
        body.append("")

        close_events = [e for e in events if e.get("event") == "close"]
        body.append("    def closeEvent(self, event):")
        for close_event in close_events:
            body.append(f"        self.{close_event['_slot']}()")
        body.append("        for _timer in self._nf_timers.values(): _timer.stop()")
        body.append("        super().closeEvent(event)")
        body.append("")

    if spec.get("center", True):
        body.append("    def _center_on_screen(self):")
        body.append('        """Центрирует окно на экране."""')
        body.append("        screen = QtWidgets.QApplication.primaryScreen()")
        body.append("        if screen is None:")
        body.append("            return")
        body.append("        geometry = self.frameGeometry()")
        body.append("        geometry.moveCenter(screen.availableGeometry().center())")
        body.append("        self.move(geometry.topLeft())")
        body.append("")

    menus = [m for m in spec.get("menus") or [] if isinstance(m, dict)]
    menu_slots = []
    if is_main and menus:
        body.append("    def _build_menus(self):")
        body.append('        """Создаёт главное меню окна."""')
        body.append("        menubar = self.menuBar()")
        for m_index, menu in enumerate(menus):
            var = f"menu_{m_index}"
            body.append(f"        {var} = menubar.addMenu("
                        f"{str(menu.get('title') or 'Меню')!r})")
            for i_index, item in enumerate(menu.get("items") or []):
                if not isinstance(item, dict):
                    continue
                if item.get("separator"):
                    body.append(f"        {var}.addSeparator()")
                    continue
                slot = f"on_menu_{m_index}_{i_index}"
                action_var = f"action_{m_index}_{i_index}"
                body.append(f"        {action_var} = {var}.addAction("
                            f"{str(item.get('text') or 'Пункт')!r})")
                if item.get("shortcut"):
                    body.append(f"        {action_var}.setShortcut("
                                f"{str(item['shortcut'])!r})")
                body.append(f"        {action_var}.triggered.connect(self.{slot})")
                menu_slots.append((slot, item.get("actions") or [],
                                   item.get("text")))
        body.append("")

    for b in valid:
        signal = str(b.get("signal") or "clicked")
        arg = "*args" if signal not in ("clicked",) else "checked=False"
        body.append(f"    def {b.get('slot')}(self, {arg}):")
        body.append(f'        """Обработчик сигнала {signal} виджета '
                    f'{b.get("widget")}."""')
        if signal == "clicked":
            body.append("        _nf_signal_value = checked")
        else:
            body.append(
                "        _nf_signal_value = args[0] if args else None")
        body.extend(_slot_body(b.get("actions"), emitter))
        body.append("")

    for slot, actions, label in menu_slots:
        body.append(f"    def {slot}(self, checked=False):")
        body.append(f'        """Пункт меню: {label}."""')
        body.extend(_slot_body(actions, emitter))
        body.append("")

    for event in events:
        arg = "draw" if event.get("event") == "draw" else ""
        body.append(f"    def {event['_slot']}(self{', ' + arg if arg else ''}):")
        body.append(f'        """Runtime-событие: {event.get("event")}."""')
        body.extend(_slot_body(event.get("actions"), emitter))
        body.append("")

    # добавленные импорты могли появиться после сборки шапки
    late_imports = sorted({i[1] for i in emitter.helpers
                           if isinstance(i, tuple) and i[0] == "import"})
    for imp in late_imports:
        if imp not in header:
            header.insert(3, imp)

    code = "\n".join(header + body).rstrip() + "\n"
    return {"code": code, "warnings": emitter.warnings,
            "helpers": sorted(h for h in emitter.helpers if isinstance(h, str))}


def generate_main_module(spec):
    """Собирает точку входа main.py для готового приложения."""
    app_name = spec.get("app_name") or "MyApp"
    is_dialog = (spec.get("cls") or "QMainWindow") == "QDialog"
    show = "window.exec()" if is_dialog else "window.show()\n    sys.exit(app.exec())"
    return f'''"""Точка входа приложения {app_name}.

Запуск:      python main.py
Сборка .exe: pyinstaller --onefile --windowed --name {app_name} main.py
"""
import os
import sys

from PyQt6 import QtWidgets

from ui_main import MainWindow


def main():
    """Запускает приложение."""
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName({app_name!r})
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as handle:
            app.setStyleSheet(handle.read())
    window = MainWindow()
    {show}


if __name__ == "__main__":
    main()
'''