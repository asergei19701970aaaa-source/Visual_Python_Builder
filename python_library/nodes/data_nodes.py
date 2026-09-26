"""Данные: словари, JSON, CSV, преобразования типов, таблицы и графики."""
import csv
import io
import json
from pathlib import Path
import re

from python_library.nodes._base import flag, library, lst, num, nums, txt

nd = library("Data", "5. Данные", color="#3d6f7a")


@nd("Словарь из текста",
    inputs=[{"name": "value", "type": "text",
             "default": "имя = Анна\nвозраст = 30", "multiline": True,
             "hint": "Строки вида ключ = значение"}],
    outputs=[("data", "dict")], tags=["dict"])
def dict_from_text(value):
    """Собирает словарь из строк 'ключ = значение'."""
    out = {}
    for line in txt(value).splitlines():
        if not line.strip():
            continue
        sep = "=" if "=" in line else (":" if ":" in line else None)
        if sep is None:
            continue
        k, v = line.split(sep, 1)
        out[k.strip()] = v.strip()
    return out


@nd("Значение по ключу", inputs=[("data", "dict", None), ("key", "text", ""),
                               ("fallback", "any", "")],
    outputs=[("value", "any")], tags=["dict", "get"])
def dict_get(data, key, fallback):
    """Берёт значение из словаря."""
    if not isinstance(data, dict):
        return fallback
    return data.get(txt(key), fallback)


@nd("Записать ключ", inputs=[("data", "dict", None), ("key", "text", "key"),
                           ("value", "any", "")],
    outputs=[("data", "dict")], tags=["dict", "set"])
def dict_set(data, key, value):
    """Добавляет или меняет ключ в словаре."""
    out = dict(data) if isinstance(data, dict) else {}
    out[txt(key) or "key"] = value
    return out


@nd("Ключи и значения", inputs=[("data", "dict", None)],
    outputs=[("keys", "list"), ("values", "list")], tags=["dict"])
def dict_items(data):
    """Разбирает словарь на два списка."""
    if not isinstance(data, dict):
        return [], []
    return list(data.keys()), list(data.values())


@nd("JSON → данные",
    inputs=[{"name": "value", "type": "text", "default": '{"a": 1}',
             "multiline": True}],
    outputs=[("data", "any")], tags=["json", "parse"])
def json_parse(value):
    """Разбирает JSON-текст."""
    try:
        return json.loads(txt(value) or "null")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Неверный JSON: {exc}")


@nd("Данные → JSON", inputs=[("data", "any", None), ("indent", "number", 2)],
    outputs=[("text", "text")], tags=["json", "dump"])
def json_dump(data, indent):
    """Превращает данные в JSON-текст."""
    return json.dumps(data, ensure_ascii=False, indent=int(num(indent, 2)),
                      default=str)


@nd("CSV → таблица",
    inputs=[{"name": "value", "type": "text",
             "default": "имя;возраст\nАнна;30", "multiline": True},
            ("delimiter", "text", ";")],
    outputs=[("rows", "list"), ("header", "list")], tags=["csv"])
def csv_parse(value, delimiter):
    """Читает CSV-текст в список строк."""
    delim = (txt(delimiter) or ";")[0]
    reader = csv.reader(io.StringIO(txt(value)), delimiter=delim)
    rows = [r for r in reader if r]
    header = rows[0] if rows else []
    return rows[1:], header


@nd("Таблица → CSV", inputs=[("rows", "list", None), ("header", "list", None),
                          ("delimiter", "text", ";")],
    outputs=[("text", "text")], tags=["csv"])
def csv_dump(rows, header, delimiter):
    """Собирает CSV-текст."""
    delim = (txt(delimiter) or ";")[0]
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delim, lineterminator="\n")
    head = lst(header)
    if head:
        writer.writerow([txt(v) for v in head])
    for row in lst(rows):
        cells = row if isinstance(row, (list, tuple)) else [row]
        writer.writerow([txt(c) for c in cells])
    return buf.getvalue()


@nd("В число", inputs=[("value", "any", "0")], outputs=[("out", "number")],
    tags=["convert"])
def to_number(value):
    """Преобразует значение в число."""
    return num(value)


@nd("В текст", inputs=[("value", "any", None)], outputs=[("out", "text")],
    tags=["convert"])
def to_text(value):
    """Преобразует значение в текст."""
    return txt(value)


@nd("В флаг", inputs=[("value", "any", None)], outputs=[("out", "bool")],
    tags=["convert"])
def to_bool(value):
    """Преобразует значение в да/нет."""
    return flag(value)


@nd(
    "В список",
    inputs=[
        ("value", "any", None),
        ("separator", "text", ","),
        {
            "name": "dict_mode",
            "type": "text",
            "default": "values",
            "choices": ["keys", "values", "items"],
            "hint": "Что брать из словаря: ключи, значения или пары",
        },
    ],
    outputs=[("out", "list")],
    tags=["convert", "list"],
)
def to_list(value, separator, dict_mode):
    """Превращает коллекцию, JSON или разделённый текст в обычный список."""
    def from_dict(mapping):
        mode = txt(dict_mode) or "values"
        if mode == "keys":
            return list(mapping.keys())
        if mode == "items":
            return [[key, item] for key, item in mapping.items()]
        return list(mapping.values())

    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value, key=repr)
    if isinstance(value, dict):
        return from_dict(value)
    if isinstance(value, str):
        source = value.strip()
        if not source:
            return []
        try:
            parsed = json.loads(source)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return from_dict(parsed)
        delimiter = txt(separator)
        if not delimiter:
            raise ValueError("Разделитель текста не может быть пустым.")
        return [
            item.strip()
            for item in source.split(delimiter)
            if item.strip()
        ]
    return [value]


@nd(
    "В словарь",
    inputs=[
        ("value", "any", None),
        ("item_separator", "text", "\n"),
        ("key_value_separator", "text", "="),
    ],
    outputs=[("out", "dict")],
    tags=["convert", "dict"],
)
def to_dict(value, item_separator, key_value_separator):
    """Превращает JSON, пары или строки «ключ=значение» в словарь."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, (list, tuple)):
        result = {}
        for index, item in enumerate(value, 1):
            if (
                not isinstance(item, (list, tuple))
                or len(item) != 2
            ):
                raise ValueError(
                    f"Элемент списка №{index} должен быть парой [ключ, значение]."
                )
            result[str(item[0])] = item[1]
        return result
    if isinstance(value, str):
        source = value.strip()
        if not source:
            return {}
        try:
            parsed = json.loads(source)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return to_dict(
                parsed, item_separator, key_value_separator
            )
        item_sep = txt(item_separator)
        pair_sep = txt(key_value_separator)
        if not item_sep or not pair_sep:
            raise ValueError("Разделители словаря не могут быть пустыми.")
        result = {}
        for index, part in enumerate(source.split(item_sep), 1):
            if not part.strip():
                continue
            if pair_sep not in part:
                raise ValueError(
                    f"В элементе №{index} нет разделителя «{pair_sep}»."
                )
            key, item = part.split(pair_sep, 1)
            key = key.strip()
            if not key:
                raise ValueError(f"В элементе №{index} пустой ключ.")
            result[key] = item.strip()
        return result
    raise ValueError(
        "В словарь можно преобразовать JSON, текст или список пар."
    )


@nd(
    "В цвет",
    inputs=[("value", "any", "#000000")],
    outputs=[("out", "color")],
    tags=["convert", "color"],
)
def to_color(value):
    """Проверяет и нормализует имя цвета, HEX, RGB-кортеж или целое число."""
    if isinstance(value, bool):
        raise ValueError("Логическое значение не является цветом.")
    if isinstance(value, int):
        if not 0 <= value <= 0xFFFFFF:
            raise ValueError("Числовой цвет должен быть от 0 до 16777215.")
        return f"#{value:06X}"
    if isinstance(value, (list, tuple)) and len(value) in {3, 4}:
        channels = []
        for channel in value:
            number = int(channel)
            if not 0 <= number <= 255:
                raise ValueError("Каналы цвета должны быть от 0 до 255.")
            channels.append(number)
        return "#" + "".join(f"{number:02X}" for number in channels)
    source = txt(value).strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3,8}", source) and len(source) in {4, 7, 9}:
        return source.upper()
    rgb = re.fullmatch(
        r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)",
        source,
        re.IGNORECASE,
    )
    if rgb:
        channels = [int(item) for item in rgb.groups()]
        if any(item > 255 for item in channels):
            raise ValueError("Каналы RGB должны быть от 0 до 255.")
        return "#" + "".join(f"{item:02X}" for item in channels)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9 _-]*", source):
        return source
    raise ValueError(
        "Цвет задаётся как #RRGGBB, имя, rgb(r,g,b), число или список каналов."
    )


@nd(
    "В путь к файлу",
    inputs=[
        ("value", "any", ""),
        ("expand_user", "bool", True),
        ("absolute", "bool", False),
    ],
    outputs=[("out", "file")],
    tags=["convert", "file", "path"],
)
def to_file(value, expand_user, absolute):
    """Превращает значение в нормализованный путь без проверки существования."""
    source = txt(value).strip()
    if not source:
        return ""
    path = Path(source)
    if flag(expand_user):
        path = path.expanduser()
    if flag(absolute):
        path = path.absolute()
    return str(path)


@nd("Данные для диаграммы",
    inputs=[("labels", "list", None), ("values", "list", None),
            {"name": "kind", "type": "text", "default": "bar",
             "choices": ["bar", "line", "pie"]},
            ("title", "text", "Диаграмма")],
    outputs=[("chart", "chart")], tags=["chart", "график"])
def chart_data(labels, values, kind, title):
    """Готовит набор данных для виджета-диаграммы."""
    vals = nums(values)
    labs = [txt(v) for v in lst(labels)] or [str(i + 1) for i in range(len(vals))]
    while len(labs) < len(vals):
        labs.append(str(len(labs) + 1))
    return {"chart": txt(kind) or "bar", "title": txt(title),
            "labels": labs[:len(vals)], "values": vals}


@nd("Текстовая таблица", inputs=[("rows", "list", None),
                              ("header", "list", None)],
    outputs=[("text", "text")], tags=["table"])
def table_text(rows, header):
    """Рисует простую текстовую таблицу."""
    data = []
    head = [txt(v) for v in lst(header)]
    if head:
        data.append(head)
    for row in lst(rows):
        cells = row if isinstance(row, (list, tuple)) else [row]
        data.append([txt(c) for c in cells])
    if not data:
        return ""
    width = max(len(r) for r in data)
    data = [r + [""] * (width - len(r)) for r in data]
    cols = [max(len(r[i]) for r in data) for i in range(width)]
    lines = [" | ".join(cell.ljust(cols[i]) for i, cell in enumerate(r))
             for r in data]
    if head:
        lines.insert(1, "-+-".join("-" * c for c in cols))
    return "\n".join(lines)