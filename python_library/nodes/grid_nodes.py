"""Маленькие универсальные операции над координатами и 2D-полями."""
from __future__ import annotations

import json

from python_library.nodes._base import flag, library, num, txt


nd = library("Grid", "18. Координаты и 2D-поля", color="#397b75")


def _points(value):
    if isinstance(value, str):
        raw = value.strip()
        try:
            value = json.loads(raw) if raw else []
        except (ValueError, TypeError):
            value = [
                pair.strip().split(",")
                for pair in raw.replace("|", ";").split(";")
                if pair.strip()
            ]
    result = []
    for item in value if isinstance(value, (list, tuple)) else []:
        if isinstance(item, dict):
            x, y = item.get("x", 0), item.get("y", 0)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            x, y = item[0], item[1]
        else:
            continue
        try:
            result.append([int(float(x)), int(float(y))])
        except (TypeError, ValueError):
            continue
    return result


@nd(
    "Набор координат",
    inputs=[("value", "any", "[[0,0],[1,0],[0,1]]")],
    outputs=[("points", "list"), ("count", "number")],
    tags=["координаты", "точки", "клетки", "shape", "map"],
    purpose="Создаёт единый список координат из текста, JSON или списка.",
    howto=(
        "Введите пары [[x,y], ...] либо текст 0,0; 1,0; 0,1. "
        "Результат подключайте к преобразованию, проверке или записи поля."
    ),
    example="[[0,0],[1,0],[0,1],[1,1]] — квадрат из четырёх клеток.",
    mistakes="Координаты начинаются с нуля. Неверные пары пропускаются.",
)
def point_set(value):
    points = _points(value)
    return points, len(points)


@nd(
    "Преобразовать координаты",
    inputs=[
        ("points", "list", None),
        ("offset_x", "number", 0),
        ("offset_y", "number", 0),
        {
            "name": "rotation",
            "type": "text",
            "default": "0",
            "choices": ["0", "90", "180", "270"],
        },
        ("mirror_x", "bool", False),
        ("mirror_y", "bool", False),
    ],
    outputs=[("points", "list")],
    tags=["сдвиг", "поворот", "отражение", "координаты"],
    purpose="Сдвигает, поворачивает и отражает любой набор точек.",
    howto=(
        "Подайте список точек, выберите поворот вокруг начала координат, "
        "затем задайте смещение."
    ),
    example="Фигура [[0,0],[1,0]] с offset_x=5 окажется в колонках 5 и 6.",
    see_also="Набор координат; Границы координат; Можно разместить на поле?",
)
def transform_points(points, offset_x, offset_y, rotation, mirror_x, mirror_y):
    result = []
    dx, dy = int(num(offset_x, 0)), int(num(offset_y, 0))
    angle = int(num(rotation, 0)) % 360
    for x, y in _points(points):
        if flag(mirror_x):
            x = -x
        if flag(mirror_y):
            y = -y
        if angle == 90:
            x, y = -y, x
        elif angle == 180:
            x, y = -x, -y
        elif angle == 270:
            x, y = y, -x
        result.append([x + dx, y + dy])
    return result


@nd(
    "Границы координат",
    inputs=[("points", "list", None)],
    outputs=[
        ("minimum_x", "number"), ("minimum_y", "number"),
        ("maximum_x", "number"), ("maximum_y", "number"),
        ("width", "number"), ("height", "number"),
    ],
    tags=["bounds", "размер", "область", "координаты"],
    purpose="Находит занимаемый прямоугольник набора координат.",
    howto="Подключите любой список точек. Пустой список возвращает нули.",
)
def point_bounds(points):
    values = _points(points)
    if not values:
        return 0, 0, 0, 0, 0, 0
    xs, ys = [p[0] for p in values], [p[1] for p in values]
    left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
    return left, top, right, bottom, right - left + 1, bottom - top + 1


@nd(
    "Можно разместить на поле?",
    inputs=[
        ("grid", "list", None),
        ("points", "list", None),
        ("offset_x", "number", 0),
        ("offset_y", "number", 0),
        ("empty", "any", 0),
        ("outside_blocked", "bool", True),
    ],
    outputs=[
        ("can_place", "bool"),
        ("collisions", "list"),
        ("inside_count", "number"),
    ],
    tags=["столкновение", "поле", "карта", "размещение", "collision"],
    purpose=(
        "Проверяет, свободны ли указанные клетки двумерного массива. "
        "Не изменяет поле."
    ),
    howto=(
        "Подайте Grid, относительные точки и положение. Полученный флаг "
        "используйте в условии перед записью."
    ),
    example="Проверить, можно ли поставить объект в колонке 4, строке 10.",
    mistakes=(
        "При outside_blocked=True любая точка за границей считается столкновением."
    ),
)
def can_place(grid, points, offset_x, offset_y, empty, outside_blocked):
    rows = grid if isinstance(grid, (list, tuple)) else []
    dx, dy = int(num(offset_x, 0)), int(num(offset_y, 0))
    collisions, inside_count = [], 0
    for px, py in _points(points):
        column, row = px + dx, py + dy
        inside = (
            0 <= row < len(rows)
            and isinstance(rows[row], (list, tuple))
            and 0 <= column < len(rows[row])
        )
        if not inside:
            if flag(outside_blocked, True):
                collisions.append([column, row])
            continue
        inside_count += 1
        if rows[row][column] != empty:
            collisions.append([column, row])
    return not collisions, collisions, inside_count


@nd(
    "Значения клеток",
    inputs=[
        ("grid", "list", None),
        ("points", "list", None),
        ("offset_x", "number", 0),
        ("offset_y", "number", 0),
        ("fallback", "any", None),
    ],
    outputs=[("values", "list")],
    tags=["прочитать клетки", "поле", "матрица", "карта"],
    purpose="Читает сразу несколько клеток двумерного поля.",
    howto="Подайте поле и список координат; отсутствующие клетки дают fallback.",
)
def cell_values(grid, points, offset_x, offset_y, fallback):
    rows = grid if isinstance(grid, (list, tuple)) else []
    dx, dy = int(num(offset_x, 0)), int(num(offset_y, 0))
    result = []
    for px, py in _points(points):
        column, row = px + dx, py + dy
        if (
            0 <= row < len(rows)
            and isinstance(rows[row], (list, tuple))
            and 0 <= column < len(rows[row])
        ):
            result.append(rows[row][column])
        else:
            result.append(fallback)
    return result