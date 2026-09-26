"""Игры: блоки для сборки Тетриса целиком на нодах.

Ноды описывают настройки игры (поле, фигуры, скорость, управление,
очки, панель), а генератор собирает из этого готовое приложение PyQt6.
Ручной код в схеме не нужен.
"""
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, num, txt

nd = library("Game", "17. Игры: Тетрис", color="#2f8f6f")

PIECE_NAMES = ("I", "O", "T", "J", "L", "S", "Z")
DEFAULT_COLORS = {
    "I": "#29b6f6", "O": "#ffd54f", "T": "#ab47bc", "J": "#5c6bc0",
    "L": "#ffa726", "S": "#66bb6a", "Z": "#ef5350",
}


def _keys(value, fallback):
    """Разбирает список клавиш: 'Left, A' -> ['Left', 'A']."""
    if isinstance(value, (list, tuple)):
        items = [txt(v).strip() for v in value]
    else:
        raw = txt(value).replace(";", ",").replace("|", ",")
        items = [part.strip() for part in raw.split(",")]
    items = [item for item in items if item]
    return items or list(fallback)


def _dict(value):
    """Мягко берёт словарь настроек."""
    return dict(value) if isinstance(value, dict) else {}


@nd("Игровое поле",
    inputs=[("cols", "number", 10), ("rows", "number", 20),
            ("cell", "number", 30), ("background", "color", "#141822"),
            ("grid", "color", "#232a38"), ("border", "color", "#3a4458"),
            ("ghost", "bool", True)],
    outputs=[("field", "dict")], tags=["тетрис", "поле", "tetris"])
def field(cols, rows, cell, background, grid, border, ghost):
    """Размеры стакана и цвета. Ghost — подсказка места падения."""
    return {
        "cols": max(4, int(num(cols, 10))),
        "rows": max(6, int(num(rows, 20))),
        "cell": max(8, int(num(cell, 30))),
        "background": txt(background) or "#141822",
        "grid": txt(grid) or "#232a38",
        "border": txt(border) or "#3a4458",
        "ghost": flag(ghost),
    }


@nd("Набор фигур",
    inputs=[("names", "text", "I, O, T, J, L, S, Z"),
            ("color_i", "color", "#29b6f6"), ("color_o", "color", "#ffd54f"),
            ("color_t", "color", "#ab47bc"), ("color_j", "color", "#5c6bc0"),
            ("color_l", "color", "#ffa726"), ("color_s", "color", "#66bb6a"),
            ("color_z", "color", "#ef5350")],
    outputs=[("pieces", "dict")], tags=["тетрис", "фигуры"])
def pieces(names, color_i, color_o, color_t, color_j, color_l, color_s,
           color_z):
    """Какие фигуры участвуют в игре и какого они цвета."""
    chosen = [n.upper() for n in _keys(names, PIECE_NAMES)]
    chosen = [n for n in chosen if n in PIECE_NAMES] or list(PIECE_NAMES)
    colors = dict(DEFAULT_COLORS)
    given = {"I": color_i, "O": color_o, "T": color_t, "J": color_j,
             "L": color_l, "S": color_s, "Z": color_z}
    for name, value in given.items():
        if txt(value):
            colors[name] = txt(value)
    return {"names": chosen, "colors": colors}


@nd("Скорость игры",
    inputs=[("start_level", "number", 1), ("base_ms", "number", 500),
            ("step_ms", "number", 40), ("min_ms", "number", 80),
            ("lines_per_level", "number", 10), ("slider", "bool", True)],
    outputs=[("speed", "dict")], tags=["тетрис", "скорость", "уровень"])
def speed(start_level, base_ms, step_ms, min_ms, lines_per_level, slider):
    """Стартовая скорость падения и её рост с уровнями."""
    return {
        "start_level": max(1, int(num(start_level, 1))),
        "base_ms": max(50, int(num(base_ms, 500))),
        "step_ms": max(0, int(num(step_ms, 40))),
        "min_ms": max(20, int(num(min_ms, 80))),
        "lines_per_level": max(1, int(num(lines_per_level, 10))),
        "slider": flag(slider),
    }


@nd("Управление",
    inputs=[("left", "text", "Left, A"), ("right", "text", "Right, D"),
            ("rotate", "text", "Up, W"), ("soft_drop", "text", "Down, S"),
            ("hard_drop", "text", "Space"), ("pause", "text", "P"),
            ("restart", "text", "R"), ("show_help", "bool", True)],
    outputs=[("controls", "dict")], tags=["тетрис", "клавиши"])
def controls(left, right, rotate, soft_drop, hard_drop, pause, restart,
             show_help):
    """Клавиши управления. Несколько клавиш перечисляются через запятую."""
    data = {
        "left": _keys(left, ["Left", "A"]),
        "right": _keys(right, ["Right", "D"]),
        "rotate": _keys(rotate, ["Up", "W"]),
        "soft_drop": _keys(soft_drop, ["Down", "S"]),
        "hard_drop": _keys(hard_drop, ["Space"]),
        "pause": _keys(pause, ["P"]),
        "restart": _keys(restart, ["R"]),
    }
    if flag(show_help):
        data["help"] = [
            "Влево/вправо: " + ", ".join(data["left"] + data["right"]),
            "Поворот: " + ", ".join(data["rotate"]),
            "Ускорить: " + ", ".join(data["soft_drop"]),
            "Сбросить: " + ", ".join(data["hard_drop"]),
            "Пауза: " + ", ".join(data["pause"])
            + ",  Заново: " + ", ".join(data["restart"]),
        ]
    return data


@nd("Подсчёт очков",
    inputs=[("single", "number", 100), ("double", "number", 300),
            ("triple", "number", 700), ("tetris", "number", 1500),
            ("soft_drop", "number", 1), ("hard_drop", "number", 2)],
    outputs=[("scoring", "dict")], tags=["тетрис", "очки"])
def scoring(single, double, triple, tetris, soft_drop, hard_drop):
    """Сколько очков дают 1–4 сожжённых линии и сброс фигуры."""
    return {
        "line_points": [0, int(num(single, 100)), int(num(double, 300)),
                        int(num(triple, 700)), int(num(tetris, 1500))],
        "soft_drop": int(num(soft_drop, 1)),
        "hard_drop": int(num(hard_drop, 2)),
    }


@nd("Панель игры",
    inputs=[("title", "text", "Тетрис"), ("score", "bool", True),
            ("lines", "bool", True), ("level", "bool", True),
            ("speed", "bool", True), ("next", "bool", True),
            ("buttons", "bool", True), ("help", "bool", True)],
    outputs=[("panel", "dict")], tags=["тетрис", "панель"])
def panel(title, score, lines, level, speed, next, buttons, help):
    """Что показывать справа от стакана."""
    return {
        "title": txt(title),
        "score": flag(score),
        "lines": flag(lines),
        "level": flag(level),
        "speed": flag(speed),
        "next": flag(next),
        "buttons": flag(buttons),
        "help": flag(help),
    }


@nd("Тетрис (игра)",
    inputs=[("field", "dict", None), ("pieces", "dict", None),
            ("speed", "dict", None), ("controls", "dict", None),
            ("scoring", "dict", None), ("panel", "dict", None),
            ("name", "text", "tetris")],
    outputs=[("widget", "widget")], tags=["тетрис", "игра", "game"])
def tetris(field, pieces, speed, controls, scoring, panel, name):
    """Готовый виджет игры: поле, панель, кнопки и клавиатура."""
    config = {
        "field": _dict(field),
        "pieces": _dict(pieces),
        "speed": _dict(speed),
        "controls": _dict(controls),
        "scoring": _dict(scoring),
        "panel": _dict(panel),
    }
    return u.widget("QWidget", name=txt(name) or "tetris",
                    helper="TetrisWidget", extra={"game": config})
