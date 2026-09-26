"""Готовые классы-движки для игровых нод.

Ноды не содержат кода игры: они только собирают настройки (словарь),
а генератор вставляет в итоговый файл готовый виджет-движок
и настраивает его этим словарём.
"""

TETRIS_WIDGET = '''
import random

TETRIS_SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
}

TETRIS_COLORS = {
    "I": "#29b6f6", "O": "#ffd54f", "T": "#ab47bc", "J": "#5c6bc0",
    "L": "#ffa726", "S": "#66bb6a", "Z": "#ef5350",
}


def tetris_rotate(shape):
    """Поворот фигуры на 90 градусов по часовой стрелке."""
    return [list(row) for row in zip(*shape[::-1])]


def tetris_fits(board, shape, px, py, cols, rows):
    """Можно ли поставить фигуру в точку (px, py)."""
    for r, row in enumerate(shape):
        for c, value in enumerate(row):
            if not value:
                continue
            nr, nc = py + r, px + c
            if nc < 0 or nc >= cols or nr >= rows:
                return False
            if nr >= 0 and board[nr][nc]:
                return False
    return True


def tetris_clear_lines(board, cols):
    """Убирает заполненные строки. Возвращает (поле, сколько убрали)."""
    kept = [row for row in board if not all(row)]
    removed = len(board) - len(kept)
    for _ in range(removed):
        kept.insert(0, [None] * cols)
    return kept, removed


def tetris_key_codes(names):
    """Имена клавиш ("Left", "Space", "P") -> коды Qt."""
    codes = []
    for name in names or []:
        text = str(name).strip()
        if not text:
            continue
        key = getattr(QtCore.Qt.Key, "Key_" + text, None)
        if key is None:
            key = getattr(QtCore.Qt.Key, "Key_" + text.upper(), None)
        if key is None and len(text) == 1:
            key = getattr(QtCore.Qt.Key, "Key_" + text.upper(), None)
        if key is not None:
            codes.append(key)
    return codes


class TetrisBoard(QtWidgets.QWidget):
    """Игровое поле: хранит стакан, фигуру и рисует их."""

    changed = QtCore.pyqtSignal() if hasattr(QtCore, "pyqtSignal") else QtCore.Signal()

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        config = dict(config or {})
        field = dict(config.get("field") or {})
        pieces = dict(config.get("pieces") or {})
        speed = dict(config.get("speed") or {})
        scoring = dict(config.get("scoring") or {})
        controls = dict(config.get("controls") or {})

        self.cols = max(4, int(field.get("cols") or 10))
        self.rows = max(6, int(field.get("rows") or 20))
        self.cell = max(8, int(field.get("cell") or 30))
        self.background = field.get("background") or "#141822"
        self.grid_color = field.get("grid") or "#232a38"
        self.border_color = field.get("border") or "#3a4458"
        self.ghost = bool(field.get("ghost", True))

        names = [n for n in (pieces.get("names") or list(TETRIS_SHAPES))
                 if n in TETRIS_SHAPES]
        self.names = names or list(TETRIS_SHAPES)
        self.colors = dict(TETRIS_COLORS)
        self.colors.update(pieces.get("colors") or {})

        self.base_ms = max(30, int(speed.get("base_ms") or 500))
        self.step_ms = int(speed.get("step_ms") or 40)
        self.min_ms = max(20, int(speed.get("min_ms") or 80))
        self.lines_per_level = max(1, int(speed.get("lines_per_level") or 10))
        self.start_level = max(1, int(speed.get("start_level") or 1))

        self.line_points = [int(v) for v in
                            (scoring.get("line_points") or [0, 100, 300, 700, 1500])]
        self.soft_drop_points = int(scoring.get("soft_drop") or 1)
        self.hard_drop_points = int(scoring.get("hard_drop") or 2)

        self.keys_left = tetris_key_codes(controls.get("left") or ["Left", "A"])
        self.keys_right = tetris_key_codes(controls.get("right") or ["Right", "D"])
        self.keys_rotate = tetris_key_codes(controls.get("rotate") or ["Up", "W"])
        self.keys_soft = tetris_key_codes(controls.get("soft_drop") or ["Down", "S"])
        self.keys_hard = tetris_key_codes(controls.get("hard_drop") or ["Space"])
        self.keys_pause = tetris_key_codes(controls.get("pause") or ["P"])
        self.keys_restart = tetris_key_codes(controls.get("restart") or ["R"])

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(self.cols * self.cell + 2, self.rows * self.cell + 2)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.speed_factor = 1.0
        self.reset()

    # ------------------------------------------------------------- состояние
    def reset(self):
        """Новая игра."""
        self.board = [[None] * self.cols for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.level = self.start_level
        self.paused = False
        self.over = False
        self.next_name = random.choice(self.names)
        self.spawn()
        self.apply_interval()
        self.timer.start()
        self.emit_changed()
        self.update()

    def interval(self):
        """Интервал падения в миллисекундах для текущего уровня."""
        value = self.base_ms - self.step_ms * (self.level - 1)
        value = value / max(0.1, float(self.speed_factor or 1.0))
        return int(max(self.min_ms, value))

    def apply_interval(self):
        self.timer.setInterval(self.interval())

    def set_speed_factor(self, factor):
        """Регулятор скорости: больше значение — быстрее падение."""
        self.speed_factor = max(0.1, float(factor or 1.0))
        self.apply_interval()
        self.emit_changed()

    def emit_changed(self):
        try:
            self.changed.emit()
        except Exception:
            pass

    def spawn(self):
        """Выпускает новую фигуру сверху."""
        self.name = self.next_name
        self.next_name = random.choice(self.names)
        self.shape = [list(row) for row in TETRIS_SHAPES[self.name]]
        self.color = self.colors.get(self.name, "#8a94a6")
        self.px = self.cols // 2 - len(self.shape[0]) // 2
        self.py = 0
        if not tetris_fits(self.board, self.shape, self.px, self.py,
                           self.cols, self.rows):
            self.over = True
            self.timer.stop()

    # ------------------------------------------------------------------ ходы
    def tick(self):
        if self.over or self.paused:
            return
        if not self.move(0, 1):
            self.lock()
        self.update()

    def move(self, dx, dy):
        if self.over or self.paused:
            return False
        if tetris_fits(self.board, self.shape, self.px + dx, self.py + dy,
                       self.cols, self.rows):
            self.px += dx
            self.py += dy
            self.update()
            return True
        return False

    def rotate(self):
        if self.over or self.paused:
            return
        turned = tetris_rotate(self.shape)
        for shift in (0, -1, 1, -2, 2):
            if tetris_fits(self.board, turned, self.px + shift, self.py,
                           self.cols, self.rows):
                self.shape = turned
                self.px += shift
                self.update()
                return

    def soft_drop(self):
        if self.move(0, 1):
            self.score += self.soft_drop_points
            self.emit_changed()
        else:
            self.lock()

    def hard_drop(self):
        if self.over or self.paused:
            return
        moved = 0
        while self.move(0, 1):
            moved += 1
        self.score += moved * self.hard_drop_points
        self.lock()

    def drop_position(self):
        """Где фигура окажется при мгновенном сбросе (тень)."""
        y = self.py
        while tetris_fits(self.board, self.shape, self.px, y + 1,
                         self.cols, self.rows):
            y += 1
        return y

    def lock(self):
        """Фиксирует фигуру и сжигает строки."""
        for r, row in enumerate(self.shape):
            for c, value in enumerate(row):
                if value and 0 <= self.py + r < self.rows:
                    self.board[self.py + r][self.px + c] = self.color
        self.board, removed = tetris_clear_lines(self.board, self.cols)
        if removed:
            index = min(removed, len(self.line_points) - 1)
            self.score += self.line_points[index] * self.level
            self.lines += removed
            self.level = self.start_level + self.lines // self.lines_per_level
            self.apply_interval()
        self.spawn()
        self.emit_changed()
        self.update()

    def toggle_pause(self):
        if self.over:
            return
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
        else:
            self.timer.start()
        self.emit_changed()
        self.update()

    def start(self):
        if self.over:
            self.reset()
            return
        self.paused = False
        self.timer.start()
        self.emit_changed()

    # -------------------------------------------------------------- клавиатура
    def keyPressEvent(self, event):
        key = event.key()
        if key in self.keys_restart:
            self.reset()
        elif key in self.keys_pause:
            self.toggle_pause()
        elif key in self.keys_left:
            self.move(-1, 0)
        elif key in self.keys_right:
            self.move(1, 0)
        elif key in self.keys_rotate:
            self.rotate()
        elif key in self.keys_soft:
            self.soft_drop()
        elif key in self.keys_hard:
            self.hard_drop()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------- рисование
    def cell_rect(self, col, row):
        return QtCore.QRectF(col * self.cell + 1, row * self.cell + 1,
                             self.cell - 2, self.cell - 2)

    def paint_cell(self, painter, col, row, color, alpha=255):
        tint = QtGui.QColor(color)
        tint.setAlpha(alpha)
        painter.setBrush(QtGui.QBrush(tint))
        painter.setPen(QtGui.QPen(QtGui.QColor(self.background), 1))
        painter.drawRoundedRect(self.cell_rect(col, row), 3, 3)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QtGui.QColor(self.background))

        painter.setPen(QtGui.QPen(QtGui.QColor(self.grid_color), 1))
        for col in range(self.cols + 1):
            x = col * self.cell
            painter.drawLine(x, 0, x, self.rows * self.cell)
        for row in range(self.rows + 1):
            y = row * self.cell
            painter.drawLine(0, y, self.cols * self.cell, y)

        for row in range(self.rows):
            for col in range(self.cols):
                color = self.board[row][col]
                if color:
                    self.paint_cell(painter, col, row, color)

        if not self.over:
            if self.ghost:
                ghost_y = self.drop_position()
                for r, line in enumerate(self.shape):
                    for c, value in enumerate(line):
                        if value and ghost_y + r >= 0:
                            self.paint_cell(painter, self.px + c, ghost_y + r,
                                            self.color, 60)
            for r, line in enumerate(self.shape):
                for c, value in enumerate(line):
                    if value and self.py + r >= 0:
                        self.paint_cell(painter, self.px + c, self.py + r,
                                        self.color)

        painter.setPen(QtGui.QPen(QtGui.QColor(self.border_color), 2))
        painter.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
        painter.drawRect(0, 0, self.cols * self.cell, self.rows * self.cell)

        if self.over or self.paused:
            overlay = QtGui.QColor("#000000")
            overlay.setAlpha(150)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(QtGui.QBrush(overlay))
            painter.drawRect(self.rect())
            font = painter.font()
            font.setPointSize(max(12, self.cell // 2))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtGui.QPen(QtGui.QColor("#f5f7fa")))
            text = "Игра окончена" if self.over else "Пауза"
            painter.drawText(self.rect(),
                             QtCore.Qt.AlignmentFlag.AlignCenter, text)
        painter.end()


class TetrisWidget(QtWidgets.QWidget):
    """Игра Целиком: поле, панель счёта, регулятор скорости и кнопки."""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = dict(config or {})
        panel = dict(self.config.get("panel") or {})
        speed = dict(self.config.get("speed") or {})
        controls = dict(self.config.get("controls") or {})

        self.board = TetrisBoard(self.config, self)
        self.next_view = None
        self.labels = {}

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)
        root.addWidget(self.board)

        side = QtWidgets.QVBoxLayout()
        side.setSpacing(10)

        title = str(panel.get("title") or "Тетрис")
        if title:
            caption = QtWidgets.QLabel(title, self)
            caption.setStyleSheet("font-size: 20px; font-weight: 600;")
            side.addWidget(caption)

        for key, text in (("score", "Счёт"), ("lines", "Линии"),
                          ("level", "Уровень"), ("speed", "Скорость")):
            if not panel.get(key, True):
                continue
            label = QtWidgets.QLabel(f"{text}: 0", self)
            label.setStyleSheet("font-size: 14px;")
            self.labels[key] = (label, text)
            side.addWidget(label)

        if panel.get("next", True):
            side.addWidget(QtWidgets.QLabel("Следующая фигура:", self))
            self.next_view = TetrisNextView(self.board, self)
            side.addWidget(self.next_view)

        if speed.get("slider", True):
            side.addWidget(QtWidgets.QLabel("Регулировка скорости:", self))
            self.slider = QtWidgets.QSlider(
                QtCore.Qt.Orientation.Horizontal, self)
            self.slider.setRange(5, 30)
            self.slider.setValue(10)
            self.slider.setToolTip("Влево — медленнее, вправо — быстрее")
            self.slider.valueChanged.connect(self.on_speed_changed)
            side.addWidget(self.slider)

            self.level_box = QtWidgets.QSpinBox(self)
            self.level_box.setPrefix("Стартовый уровень: ")
            self.level_box.setRange(1, 20)
            self.level_box.setValue(max(1, int(speed.get("start_level") or 1)))
            self.level_box.valueChanged.connect(self.on_start_level_changed)
            side.addWidget(self.level_box)

        if panel.get("buttons", True):
            row = QtWidgets.QHBoxLayout()
            self.btn_start = QtWidgets.QPushButton("Старт", self)
            self.btn_pause = QtWidgets.QPushButton("Пауза", self)
            self.btn_new = QtWidgets.QPushButton("Новая игра", self)
            self.btn_start.clicked.connect(self.on_start)
            self.btn_pause.clicked.connect(self.on_pause)
            self.btn_new.clicked.connect(self.on_new_game)
            for button in (self.btn_start, self.btn_pause, self.btn_new):
                row.addWidget(button)
            side.addLayout(row)

        if panel.get("help", True):
            hints = [
                "← → — движение",
                "↑ — поворот",
                "↓ — ускорить",
                "Пробел — сбросить",
                "P — пауза,  R — заново",
            ]
            custom = controls.get("help")
            if isinstance(custom, (list, tuple)) and custom:
                hints = [str(line) for line in custom]
            help_label = QtWidgets.QLabel("\\n".join(hints), self)
            help_label.setStyleSheet("color: #98a2b3; font-size: 12px;")
            side.addWidget(help_label)

        side.addStretch(1)
        root.addLayout(side)

        self.board.changed.connect(self.refresh)
        self.refresh()
        QtCore.QTimer.singleShot(0, self.board.setFocus)

    # ------------------------------------------------------------ обработчики
    def on_speed_changed(self, value):
        self.board.set_speed_factor(float(value) / 10.0)
        self.board.setFocus()

    def on_start_level_changed(self, value):
        self.board.start_level = int(value)
        self.board.level = max(self.board.level, int(value))
        self.board.apply_interval()
        self.refresh()
        self.board.setFocus()

    def on_start(self):
        self.board.start()
        self.board.setFocus()

    def on_pause(self):
        self.board.toggle_pause()
        self.board.setFocus()

    def on_new_game(self):
        self.board.reset()
        self.board.setFocus()

    def refresh(self):
        """Обновляет панель информации."""
        values = {
            "score": self.board.score,
            "lines": self.board.lines,
            "level": self.board.level,
            "speed": f"{self.board.interval()} мс",
        }
        for key, (label, text) in self.labels.items():
            label.setText(f"{text}: {values.get(key, 0)}")
        if self.next_view is not None:
            self.next_view.update()


class TetrisNextView(QtWidgets.QWidget):
    """Предпросмотр следующей фигуры."""

    def __init__(self, board, parent=None):
        super().__init__(parent)
        self.board = board
        self.setFixedSize(4 * 24 + 8, 4 * 24 + 8)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QtGui.QColor(self.board.background))
        name = getattr(self.board, "next_name", None)
        if not name:
            painter.end()
            return
        shape = TETRIS_SHAPES.get(name) or []
        color = QtGui.QColor(self.board.colors.get(name, "#8a94a6"))
        size = 24
        offset_x = (self.width() - len(shape[0]) * size) / 2 if shape else 0
        offset_y = (self.height() - len(shape) * size) / 2 if shape else 0
        painter.setPen(QtGui.QPen(QtGui.QColor(self.board.background), 1))
        painter.setBrush(QtGui.QBrush(color))
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                if value:
                    painter.drawRoundedRect(
                        QtCore.QRectF(offset_x + c * size + 1,
                                      offset_y + r * size + 1,
                                      size - 2, size - 2), 3, 3)
        painter.end()
'''.strip()
