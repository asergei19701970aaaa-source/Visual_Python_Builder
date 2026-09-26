"""Код runtime-слоя, встраиваемый в экспортированное PyQt-приложение."""

RUNTIME_CODE = r'''
def nf_number(value, fallback=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def nf_flag(value):
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "нет", "false", "off", "no")
    return bool(value)


def nf_widget_value(widget, mode="auto"):
    if mode == "checked" and hasattr(widget, "isChecked"):
        return widget.isChecked()
    if mode == "number" and hasattr(widget, "value"):
        return widget.value()
    if mode == "index" and hasattr(widget, "currentIndex"):
        return widget.currentIndex()
    if mode == "text":
        return get_text(widget)
    if hasattr(widget, "isChecked"):
        return widget.isChecked()
    if hasattr(widget, "value"):
        return widget.value()
    return get_text(widget)


def nf_formula(expression, a=0, b=0, c=0):
    import math
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"a": a, "b": b, "c": c, "abs": abs, "round": round,
                    "min": min, "max": max, "len": len})
    return eval(str(expression), {"__builtins__": {}}, allowed)


def nf_compare(a, operation, b):
    if operation == "равно": return a == b
    if operation == "не равно": return a != b
    if operation == "больше": return a > b
    if operation == "меньше": return a < b
    if operation == "больше или равно": return a >= b
    if operation == "меньше или равно": return a <= b
    if operation == "содержит": return b in a
    if operation == "И": return nf_flag(a) and nf_flag(b)
    if operation == "ИЛИ": return nf_flag(a) or nf_flag(b)
    return False


def nf_key_name(event):
    key = event.key()
    aliases = {
        QtCore.Qt.Key.Key_Left: "LEFT", QtCore.Qt.Key.Key_Right: "RIGHT",
        QtCore.Qt.Key.Key_Up: "UP", QtCore.Qt.Key.Key_Down: "DOWN",
        QtCore.Qt.Key.Key_Space: "SPACE", QtCore.Qt.Key.Key_Return: "ENTER",
        QtCore.Qt.Key.Key_Enter: "ENTER", QtCore.Qt.Key.Key_Escape: "ESC",
        QtCore.Qt.Key.Key_Tab: "TAB", QtCore.Qt.Key.Key_Backspace: "BACKSPACE",
    }
    if key in aliases:
        return aliases[key]
    text = event.text()
    return text.upper() if text else str(int(key))


def nf_grid(cols, rows, fill=0):
    return [[fill for _ in range(max(0, int(cols)))]
            for _ in range(max(0, int(rows)))]


def nf_grid_inside(grid, col, row):
    try:
        return 0 <= int(row) < len(grid) and 0 <= int(col) < len(grid[int(row)])
    except (TypeError, ValueError):
        return False


def nf_grid_get(grid, col, row, default=0):
    return grid[int(row)][int(col)] if nf_grid_inside(grid, col, row) else default


class NfPainter:
    """Небольшой безопасный набор команд рисования для runtime-нод."""
    def __init__(self, painter, widget):
        self.p = painter
        self.widget = widget

    def clear(self, color):
        self.p.fillRect(self.widget.rect(), QtGui.QColor(str(color)))

    def rect(self, x, y, w, h, color, outline=""):
        self.p.setBrush(QtGui.QBrush(QtGui.QColor(str(color))))
        pen = QtGui.QPen(QtGui.QColor(str(outline))) if outline else \
              QtGui.QPen(QtCore.Qt.PenStyle.NoPen)
        self.p.setPen(pen)
        self.p.drawRect(QtCore.QRectF(float(x), float(y), float(w), float(h)))

    def cell(self, col, row, size, color, gap=1):
        size, gap = float(size), float(gap)
        self.rect(float(col) * size + gap, float(row) * size + gap,
                  max(0, size - gap * 2), max(0, size - gap * 2), color)

    def ellipse(self, x, y, w, h, color):
        self.p.setPen(QtCore.Qt.PenStyle.NoPen)
        self.p.setBrush(QtGui.QBrush(QtGui.QColor(str(color))))
        self.p.drawEllipse(QtCore.QRectF(float(x), float(y), float(w), float(h)))

    def line(self, x1, y1, x2, y2, color, width=1):
        self.p.setPen(QtGui.QPen(QtGui.QColor(str(color)), int(width)))
        self.p.drawLine(QtCore.QPointF(float(x1), float(y1)),
                        QtCore.QPointF(float(x2), float(y2)))

    def text(self, x, y, text, color="#ffffff", size=12):
        font = self.p.font()
        font.setPointSize(max(1, int(size)))
        self.p.setFont(font)
        self.p.setPen(QtGui.QPen(QtGui.QColor(str(color))))
        self.p.drawText(QtCore.QPointF(float(x), float(y)), str(text))

    def grid(self, grid, cell_size, colors=None, gap=1):
        palette = colors or {}
        for row, values in enumerate(grid or []):
            for col, value in enumerate(values or []):
                color = palette.get(value, palette.get(str(value), value))
                if value not in (None, 0, False, ""):
                    self.cell(col, row, cell_size, color or "#4ecca3", gap)
'''.strip()


LIVE_CANVAS_CODE = r'''
class LiveCanvas(QtWidgets.QWidget):
    """Холст, который передаёт рисование, мышь и клавиши runtime-нодам."""
    def __init__(self, name, owner, columns=20, rows=20, cell_size=24,
                 background="#1c1f26"):
        super().__init__(owner)
        self.nf_name = str(name)
        self.nf_owner = owner
        self.columns = max(1, int(columns))
        self.rows = max(1, int(rows))
        self.cell_size = max(1, int(cell_size))
        self.background = str(background)
        self.setMinimumSize(self.columns * self.cell_size,
                            self.rows * self.cell_size)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QtGui.QColor(self.background))
        self.nf_owner._nf_draw_canvas(self.nf_name, NfPainter(painter, self))
        painter.end()

    def _send_mouse(self, kind, event):
        pos = event.position()
        self.setFocus()
        self.nf_owner._nf_canvas_mouse(
            self.nf_name, kind, pos.x(), pos.y(),
            int(pos.x() // self.cell_size), int(pos.y() // self.cell_size),
            str(event.button().name))

    def mousePressEvent(self, event): self._send_mouse("press", event)
    def mouseMoveEvent(self, event): self._send_mouse("move", event)
    def mouseReleaseEvent(self, event): self._send_mouse("release", event)
'''.strip()