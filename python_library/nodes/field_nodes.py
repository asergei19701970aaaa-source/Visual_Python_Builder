"""Маленькие универсальные правила для клеточных полей.

Ноды подходят для игр с падающими блоками, головоломок,
редакторов карт и любых задач, где объект из клеток
двигается по полю. Ни одна нода не меняет входные данные:
каждая возвращает новый результат.
"""
from __future__ import annotations

import json
import random

from python_library.nodes._base import flag, library, num, txt

nd = library("Field", "19. Клеточные поля: правила", color="#4a6fa5")

YES = "да"
NO = "нет"


# ------------------------------------------------------------ помощники
def _int(value, fallback=0):
    try:
        return int(round(num(value, fallback)))
    except (TypeError, ValueError, OverflowError):
        return int(fallback)


def _cell(value):
    """Приводит значение клетки к числу, если это возможно."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else value
    text = txt(value).strip()
    try:
        number = float(text.replace(",", "."))
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


def _is_empty(cell, empty):
    return cell == empty or txt(cell).strip() == txt(empty).strip()


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


def _normalize(points):
    if not points:
        return []
    left = min(p[0] for p in points)
    top = min(p[1] for p in points)
    return [[x - left, y - top] for x, y in points]


def _is_field(value):
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(isinstance(row, list) for row in value)
    )


def _copy(field):
    return [list(row) for row in field] if _is_field(field) else []


def _fits(field, points, dx, dy, empty):
    if not _is_field(field):
        return False
    height = len(field)
    for x, y in points:
        column, row = x + dx, y + dy
        width = len(field[row]) if 0 <= row < height else len(field[0])
        if column < 0 or column >= width or row >= height:
            return False
        if row < 0:
            continue
        if not _is_empty(field[row][column], empty):
            return False
    return True


def _stamp(field, points, dx, dy, value):
    result = _copy(field)
    for x, y in points:
        column, row = x + dx, y + dy
        if 0 <= row < len(result) and 0 <= column < len(result[row]):
            result[row][column] = value
    return result


def _drop(field, points, dx, dy, empty):
    if not points or not _fits(field, points, dx, dy, empty):
        return 0
    distance = 0
    limit = len(field) + 8
    while distance < limit and _fits(field, points, dx, dy + distance + 1, empty):
        distance += 1
    return distance


def _keys(text):
    result = []
    for part in txt(text).replace(";", ",").split(","):
        part = part.strip().lower()
        if part.startswith("key_"):
            part = part[4:]
        if part:
            result.append(part)
    return result


def _parse_shapes(text):
    shapes = []
    for chunk in txt(text).split("|"):
        chunk = chunk.strip()
        if not chunk:
            continue
        head, separator, body = chunk.partition(":")
        if not separator:
            head, body = "", head
        name, _, value = head.partition("/")
        points = _normalize(_points(body))
        if not points:
            continue
        number = len(shapes) + 1
        shapes.append((
            name.strip() or f"Фигура {number}",
            _cell(value) if value.strip() else number,
            points,
        ))
    return shapes


# ----------------------------------------------------------------- ноды
@nd(
    "Поле нужного размера",
    inputs=[
        ("field", "any", None),
        ("columns", "number", 10),
        ("rows", "number", 20),
        ("empty", "any", 0),
        ("filled_rows", "number", 0),
        ("fill_value", "any", 8),
        ("seed", "number", 1),
    ],
    outputs=[("field", "list"), ("created", "bool")],
    tags=["поле", "создать поле", "новое поле", "мусорные строки"],
    purpose="Отдаёт готовое поле. Если поля ещё нет,\nсоздаёт новое нужного размера.",
    howto=(
        "Подключите к «field» память с полем. Пока память пуста,\n"
        "нода создаёт поле columns × rows. filled_rows заполняет\n"
        "нижние строки блоками с дырками. seed делает случайное\n"
        "заполнение одинаковым при каждом чтении."
    ),
    example="Очистите память поля, и нода сразу создаст новое поле.",
    mistakes="Размер меняется только для нового поля.\nГотовое поле нода не меняет.",
)
def ensure_field(field, columns, rows, empty, filled_rows, fill_value, seed):
    if _is_field(field):
        return field, False
    width = max(1, min(200, _int(columns, 10)))
    height = max(1, min(200, _int(rows, 20)))
    blank = _cell(empty)
    grid = [[blank for _ in range(width)] for _ in range(height)]
    count = max(0, min(height - 1, _int(filled_rows, 0)))
    generator = random.Random(_int(seed, 1))
    block = _cell(fill_value)
    for row in range(height - count, height):
        line = [block] * width
        holes = 1 if width < 6 else 2
        for column in generator.sample(range(width), k=min(holes, width)):
            line[column] = blank
        grid[row] = line
    return grid, True


@nd(
    "Фигура из набора",
    inputs=[
        ("shapes", "text", "A/1: 0,0; 1,0; 0,1; 1,1"),
        ("index", "number", 0),
    ],
    outputs=[
        ("points", "list"), ("value", "any"),
        ("count", "number"), ("name", "text"),
    ],
    tags=["фигура", "набор фигур", "блоки", "shape"],
    purpose="Берёт одну фигуру из текстового набора.",
    howto=(
        "Набор записывается так: Имя/цвет: x,y; x,y | Имя/цвет: ...\n"
        "Фигуры разделяет черта |. «цвет» — число для палитры.\n"
        "index выбирает фигуру; слишком большой номер идёт по кругу."
    ),
    example="O/2: 0,0; 1,0; 0,1; 1,1 — квадрат цвета 2.",
    mistakes="Координаты начинаются с нуля. Пустой набор даёт одну клетку.",
)
def shape_from_set(shapes, index):
    parsed = _parse_shapes(shapes) or [("Клетка", 1, [[0, 0]])]
    name, value, points = parsed[_int(index, 0) % len(parsed)]
    return points, value, len(parsed), name


@nd(
    "Повернуть фигуру",
    inputs=[("points", "list", None), ("turns", "number", 0)],
    outputs=[("points", "list")],
    tags=["поворот", "фигура", "rotate"],
    purpose="Поворачивает фигуру по часовой стрелке\nвокруг её центра.",
    howto="turns — число четвертей оборота. 4 поворота дают исходную фигуру.",
    example="turns = 1 превращает горизонтальную палку в вертикальную.",
)
def rotate_shape(points, turns):
    base = _normalize(_points(points))
    if not base:
        return []
    center_x = max(p[0] for p in base)
    center_y = max(p[1] for p in base)
    count = _int(turns, 0) % 4
    result = []
    for x, y in base:
        big_x, big_y = 2 * x, 2 * y
        for _ in range(count):
            big_x, big_y = center_x - (big_y - center_y), center_y + (big_x - center_x)
        result.append([big_x // 2, big_y // 2])
    return result


@nd(
    "Помещается на поле?",
    inputs=[
        ("field", "list", None), ("points", "list", None),
        ("offset_x", "number", 0), ("offset_y", "number", 0),
        ("empty", "any", 0),
    ],
    outputs=[("answer", "text"), ("ok", "bool")],
    tags=["столкновение", "проверка", "поместится", "collision"],
    purpose="Отвечает «да», если все клетки фигуры\nсвободны и не выходят за стены и дно.",
    howto=(
        "Подключите поле, фигуру и её положение. Ответ «да» или «нет»\n"
        "удобно сравнивать в ноде «Условие» со словом да."
    ),
    example="Проверить сдвиг влево: offset_x = текущий столбец − 1.",
    mistakes="Клетки выше верхнего края считаются свободными.",
)
def fits(field, points, offset_x, offset_y, empty):
    ok = _fits(field, _points(points), _int(offset_x), _int(offset_y), _cell(empty))
    return (YES if ok else NO), ok


@nd(
    "Насколько опустится фигура",
    inputs=[
        ("field", "list", None), ("points", "list", None),
        ("offset_x", "number", 0), ("offset_y", "number", 0),
        ("empty", "any", 0),
    ],
    outputs=[("rows", "number")],
    tags=["падение", "сброс", "тень", "drop"],
    purpose="Считает, на сколько строк фигура может\nупасть до препятствия.",
    howto="Прибавьте результат к строке фигуры, чтобы сбросить её вниз.",
)
def drop_distance(field, points, offset_x, offset_y, empty):
    return _drop(field, _points(points), _int(offset_x), _int(offset_y), _cell(empty))


@nd(
    "Впечатать фигуру в поле",
    inputs=[
        ("field", "list", None), ("points", "list", None),
        ("offset_x", "number", 0), ("offset_y", "number", 0),
        ("value", "any", 1),
    ],
    outputs=[("field", "list")],
    tags=["записать", "закрепить", "поставить", "stamp"],
    purpose="Возвращает копию поля, где клетки фигуры\nзаписаны значением value.",
    howto="Исходное поле не меняется. Результат запишите в память.",
)
def stamp(field, points, offset_x, offset_y, value):
    return _stamp(field, _points(points), _int(offset_x), _int(offset_y), _cell(value))


@nd(
    "Убрать заполненные строки",
    inputs=[("field", "list", None), ("empty", "any", 0)],
    outputs=[("field", "list"), ("removed", "number")],
    tags=["линии", "строки", "очистка", "lines"],
    purpose="Убирает строки без пустых клеток и\nдобавляет пустые строки сверху.",
    howto="removed — сколько строк убрано. По нему считают очки.",
)
def remove_full_rows(field, empty):
    if not _is_field(field):
        return [], 0
    blank = _cell(empty)
    kept = [list(row) for row in field if any(_is_empty(c, blank) for c in row)]
    removed = len(field) - len(kept)
    width = len(field[0])
    return [[blank] * width for _ in range(removed)] + kept, removed


@nd(
    "Показать фигуру и тень",
    inputs=[
        ("field", "list", None), ("points", "list", None),
        ("offset_x", "number", 0), ("offset_y", "number", 0),
        ("value", "any", 1), ("show_shadow", "bool", True),
        ("shadow_value", "any", 9), ("empty", "any", 0),
    ],
    outputs=[("field", "list")],
    tags=["показать", "тень", "отрисовка", "ghost"],
    purpose="Готовит поле для экрана: фигура поверх поля\nи, по желанию, её тень на месте падения.",
    howto="Результат подключите к входу «Поле» холста.",
)
def overlay(field, points, offset_x, offset_y, value, show_shadow, shadow_value, empty):
    blank = _cell(empty)
    shape = _points(points)
    dx, dy = _int(offset_x), _int(offset_y)
    result = _copy(field)
    if flag(show_shadow) and shape:
        distance = _drop(field, shape, dx, dy, blank)
        shade = _cell(shadow_value)
        for x, y in shape:
            column, row = x + dx, y + dy + distance
            if 0 <= row < len(result) and 0 <= column < len(result[row]):
                if _is_empty(result[row][column], blank):
                    result[row][column] = shade
    return _stamp(result, shape, dx, dy, _cell(value))


@nd(
    "Столбец по центру",
    inputs=[("field", "list", None), ("points", "list", None)],
    outputs=[("column", "number")],
    tags=["центр", "появление", "spawn"],
    purpose="Находит столбец, где фигура стоит по центру поля.",
    howto="Используйте как стартовый столбец новой фигуры.",
)
def center_column(field, points):
    width = len(field[0]) if _is_field(field) else 10
    shape = _points(points)
    if not shape:
        return width // 2
    left = min(p[0] for p in shape)
    size = max(p[0] for p in shape) - left + 1
    return (width - size) // 2 - left


@nd(
    "Маленькое поле с фигурой",
    inputs=[
        ("points", "list", None), ("value", "any", 1),
        ("columns", "number", 4), ("rows", "number", 4),
        ("empty", "any", 0),
    ],
    outputs=[("field", "list")],
    tags=["следующая фигура", "превью", "preview"],
    purpose="Рисует фигуру в центре маленького поля.",
    howto="Подключите к второму холсту, чтобы показать следующую фигуру.",
)
def shape_preview(points, value, columns, rows, empty):
    width = max(1, _int(columns, 4))
    height = max(1, _int(rows, 4))
    blank = _cell(empty)
    grid = [[blank] * width for _ in range(height)]
    shape = _normalize(_points(points))
    if not shape:
        return grid
    size_x = max(p[0] for p in shape) + 1
    size_y = max(p[1] for p in shape) + 1
    return _stamp(grid, shape, (width - size_x) // 2, (height - size_y) // 2, _cell(value))


@nd(
    "Очки за ход",
    inputs=[
        ("rows", "number", 0), ("level", "number", 1),
        ("table", "text", "0,100,300,500,800"),
        ("drop_rows", "number", 0), ("drop_bonus", "number", 2),
    ],
    outputs=[("points", "number")],
    tags=["очки", "счёт", "score"],
    purpose="Считает очки: таблица по числу строк × уровень\nплюс бонус за клетки сброса.",
    howto=(
        "table — очки за 0, 1, 2, 3, 4 строки через запятую.\n"
        "drop_rows × drop_bonus добавляется за быстрый сброс."
    ),
    example="2 строки на уровне 3: 300 × 3 = 900 очков.",
)
def score_gain(rows, level, table, drop_rows, drop_bonus):
    values = [_int(p) for p in txt(table).replace(";", ",").split(",") if p.strip()]
    values = values or [0, 100, 300, 500, 800]
    count = max(0, _int(rows))
    base = values[min(count, len(values) - 1)]
    return base * max(1, _int(level, 1)) + max(0, _int(drop_rows)) * max(0, _int(drop_bonus))


@nd(
    "Уровень по строкам",
    inputs=[
        ("lines", "number", 0), ("start_level", "number", 1),
        ("lines_per_level", "number", 10),
    ],
    outputs=[("level", "number")],
    tags=["уровень", "сложность", "level"],
    purpose="Уровень растёт на 1 после каждых lines_per_level строк.",
    howto="Уровень = start_level + lines // lines_per_level.",
)
def level_from_lines(lines, start_level, lines_per_level):
    start = max(1, _int(start_level, 1))
    step = max(1, _int(lines_per_level, 10))
    return start + max(0, _int(lines)) // step


@nd(
    "Задержка по уровню",
    inputs=[
        ("level", "number", 1), ("start_level", "number", 1),
        ("start_ms", "number", 800), ("step_ms", "number", 60),
        ("minimum_ms", "number", 80),
    ],
    outputs=[("interval", "number")],
    tags=["скорость", "интервал", "таймер", "speed"],
    purpose="Считает интервал таймера: чем выше уровень,\nтем быстрее.",
    howto="interval = start_ms − (level − start_level) × step_ms, но не меньше minimum_ms.",
)
def step_interval(level, start_level, start_ms, step_ms, minimum_ms):
    levels = max(0, _int(level, 1) - max(1, _int(start_level, 1)))
    value = _int(start_ms, 800) - levels * max(0, _int(step_ms, 60))
    return max(max(1, _int(minimum_ms, 80)), value)


@nd(
    "Клавиша → команда",
    inputs=[
        ("key", "text", ""),
        ("left_keys", "text", "Left,A"),
        ("right_keys", "text", "Right,D"),
        ("rotate_keys", "text", "Up,W"),
        ("down_keys", "text", "Down,S"),
        ("drop_keys", "text", "Space,X"),
        ("pause_keys", "text", "P"),
        ("restart_keys", "text", "R"),
    ],
    outputs=[("command", "text")],
    tags=["клавиши", "управление", "команда", "keys"],
    purpose=(
        "Переводит нажатую клавишу в слово-команду:\n"
        "влево, вправо, поворот, вниз, сброс, пауза, заново."
    ),
    howto="Клавиши для каждой команды перечислите через запятую.",
    mistakes="Новые клавиши добавьте и в свойство «Разрешённые клавиши» ноды «Клавиатура».",
)
def key_command(key, left_keys, right_keys, rotate_keys, down_keys,
                drop_keys, pause_keys, restart_keys):
    pressed = _keys(key)
    if not pressed:
        return ""
    table = (
        ("влево", left_keys), ("вправо", right_keys),
        ("поворот", rotate_keys), ("вниз", down_keys),
        ("сброс", drop_keys), ("пауза", pause_keys),
        ("заново", restart_keys),
    )
    for command, keys in table:
        if pressed[0] in _keys(keys):
            return command
    return ""


@nd(
    "Выбор из четырёх вариантов",
    inputs=[
        ("index", "number", 0),
        ("option_0", "text", ""), ("option_1", "text", ""),
        ("option_2", "text", ""), ("option_3", "text", ""),
    ],
    outputs=[("value", "text"), ("data", "any")],
    tags=["выбор", "вариант", "список", "choose"],
    purpose="Отдаёт вариант с номером index (0–3).",
    howto=(
        "Подключите «Текущий индекс» выпадающего списка.\n"
        "data — тот же вариант, прочитанный как JSON, если это JSON."
    ),
    mistakes="Пустой вариант заменяется вариантом 0.",
)
def choose(index, option_0, option_1, option_2, option_3):
    options = [option_0, option_1, option_2, option_3]
    value = options[max(0, min(3, _int(index, 0)))]
    if txt(value).strip() == "":
        value = option_0
    data = value
    if isinstance(value, str) and value.strip()[:1] in ("{", "["):
        try:
            data = json.loads(value)
        except ValueError:
            data = value
    return txt(value), data


@nd(
    "Сложить два числа",
    inputs=[("a", "number", 0), ("b", "number", 0)],
    outputs=[("result", "number")],
    tags=["плюс", "сумма", "прибавить"],
    purpose="a + b. Пустое значение считается нулём.",
    howto="Для вычитания задайте b отрицательным, например −1.",
)
def add(a, b):
    value = num(a, 0) + num(b, 0)
    return int(value) if float(value).is_integer() else value


@nd(
    "База плюс минус",
    inputs=[("base", "number", 0), ("plus", "number", 0), ("minus", "number", 0)],
    outputs=[("result", "number")],
    tags=["смещение", "позиция", "счётчики"],
    purpose="base + plus − minus.",
    howto="Удобно для позиции: старт + шаги вправо − шаги влево.",
)
def offset(base, plus, minus):
    value = num(base, 0) + num(plus, 0) - num(minus, 0)
    return int(value) if float(value).is_integer() else value


@nd(
    "Да или нет",
    inputs=[("value", "any", False)],
    outputs=[("answer", "text")],
    tags=["флаг", "логика", "условие"],
    purpose="Превращает флажок или число в слово «да» или «нет».",
    howto="Ответ сравнивайте в ноде «Условие» со словом да.",
)
def yes_no(value):
    return YES if flag(value) else NO


@nd(
    "Текст по шаблону",
    inputs=[
        ("template", "text", "{0}"),
        ("value_1", "any", ""), ("value_2", "any", ""),
        ("value_3", "any", ""),
    ],
    outputs=[("text", "text")],
    tags=["текст", "шаблон", "формат"],
    purpose="Вставляет значения в шаблон {0}, {1}, {2}.",
    howto="Пустое значение показывается как 0. Целые числа — без .0.",
)
def fill_template(template, value_1, value_2, value_3):
    def show(value):
        if value is None or txt(value).strip() == "":
            return "0"
        return txt(_cell(value))
    values = [show(value_1), show(value_2), show(value_3)]
    try:
        return txt(template).format(*values)
    except (IndexError, KeyError, ValueError):
        return txt(template)
