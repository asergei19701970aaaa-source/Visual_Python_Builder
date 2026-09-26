"""Списки и наборы данных."""
from python_library.nodes._base import flag, library, lst, num, nums, txt

nd = library("List", "4. Списки", color="#5a3f7a")


@nd("Список из текста",
    inputs=[{"name": "value", "type": "text", "default": "1, 2, 3",
             "hint": "Элементы через запятую"}],
    outputs=[("items", "list")], tags=["list"])
def list_from_text(value):
    """Создаёт список из строки с запятыми."""
    return [p.strip() for p in txt(value).split(",") if p.strip()]


@nd("Собрать список",
    inputs=[("a", "any", None), ("b", "any", None), ("c", "any", None),
            ("d", "any", None), ("e", "any", None), ("f", "any", None)],
    outputs=[("items", "list")], tags=["pack"])
def pack(a, b, c, d, e, f):
    """Собирает до шести значений в один список."""
    return [v for v in (a, b, c, d, e, f) if v not in (None, "")]


@nd("Объединить списки", inputs=[("first", "list", None),
                                ("second", "list", None)],
    outputs=[("items", "list")], tags=["merge"])
def merge(first, second):
    """Склеивает два списка."""
    return lst(first) + lst(second)


@nd("Элемент по номеру", inputs=[("items", "list", None),
                               ("index", "number", 0)],
    outputs=[("item", "any")], tags=["index"])
def item_at(items, index):
    """Берёт элемент списка по номеру (0 — первый)."""
    data = lst(items)
    if not data:
        raise ValueError("Пустой список")
    return data[int(num(index)) % len(data)]


@nd("Длина списка", inputs=[("items", "list", None)],
    outputs=[("count", "number")], tags=["len"])
def count(items):
    """Сколько элементов в списке."""
    return float(len(lst(items)))


@nd("Сортировка", inputs=[("items", "list", None), ("reverse", "bool", False),
                         ("as_number", "bool", False)],
    outputs=[("items", "list")], tags=["sort"])
def sort(items, reverse, as_number):
    """Сортирует список (как текст или как числа)."""
    key = (lambda v: num(v)) if flag(as_number) else (lambda v: txt(v))
    return sorted(lst(items), key=key, reverse=flag(reverse))


@nd("Перевернуть список", inputs=[("items", "list", None)],
    outputs=[("items", "list")], tags=["reverse"])
def reverse(items):
    """Порядок наоборот."""
    return list(reversed(lst(items)))


@nd("Уникальные", inputs=[("items", "list", None)],
    outputs=[("items", "list")], tags=["unique"])
def unique(items):
    """Убирает дубликаты, сохраняя порядок."""
    seen, out = set(), []
    for v in lst(items):
        k = txt(v)
        if k not in seen:
            seen.add(k)
            out.append(v)
    return out


@nd("Фильтр по тексту", inputs=[("items", "list", None),
                            ("needle", "text", ""), ("invert", "bool", False)],
    outputs=[("items", "list"), ("count", "number")], tags=["filter"])
def filter_text(items, needle, invert):
    """Оставляет элементы, содержащие подстроку."""
    key = txt(needle)
    result = [v for v in lst(items) if (key in txt(v)) != flag(invert)]
    return result, float(len(result))


@nd("Фильтр чисел", inputs=[("items", "list", None), ("low", "number", 0),
                         ("high", "number", 100)],
    outputs=[("items", "list")], tags=["filter"])
def filter_range(items, low, high):
    """Оставляет числа в заданном диапазоне."""
    lo, hi = sorted((num(low), num(high, 100)))
    return [v for v in nums(items) if lo <= v <= hi]


@nd("Карта: умножить", inputs=[("items", "list", None),
                             ("factor", "number", 2), ("offset", "number", 0)],
    outputs=[("items", "list")], tags=["map"])
def map_scale(items, factor, offset):
    """Каждый элемент * factor + offset."""
    k, b = num(factor, 2), num(offset)
    return [v * k + b for v in nums(items)]


@nd("Карта: шаблон текста",
    inputs=[("items", "list", None),
            {"name": "template", "type": "text", "default": "- {v}",
             "hint": "{v} — значение, {i} — номер"}],
    outputs=[("items", "list"), ("text", "text")], tags=["map", "format"])
def map_template(items, template):
    """Применяет шаблон к каждому элементу."""
    tpl = txt(template) or "{v}"
    out = []
    for i, v in enumerate(lst(items)):
        try:
            out.append(tpl.format(v=txt(v), i=i))
        except (KeyError, IndexError, ValueError):
            out.append(txt(v))
    return out, "\n".join(out)


@nd("Срез списка", inputs=[("items", "list", None), ("start", "number", 0),
                         ("count", "number", 5)],
    outputs=[("items", "list")], tags=["slice"])
def slice_list(items, start, count):
    """Берёт часть списка."""
    data = lst(items)
    i, n = int(num(start)), int(num(count, 5))
    return data[i:i + n] if n > 0 else data[i:]


@nd("Диапазон чисел", inputs=[("start", "number", 0), ("stop", "number", 10),
                            ("step", "number", 1)],
    outputs=[("items", "list")], tags=["range"])
def number_range(start, stop, step):
    """Генерирует список чисел."""
    a, b = num(start), num(stop, 10)
    s = num(step, 1) or 1.0
    out, cur, guard = [], a, 0
    while (cur < b if s > 0 else cur > b) and guard < 100000:
        out.append(cur)
        cur += s
        guard += 1
    return out


@nd("Перемешать", inputs=[("items", "list", None), ("seed", "number", 0)],
    outputs=[("items", "list")], tags=["shuffle"])
def shuffle(items, seed):
    """Случайный порядок элементов."""
    import random
    data = lst(items)
    random.Random(int(num(seed))).shuffle(data)
    return data


@nd("Содержит элемент?", inputs=[("items", "list", None),
                                ("value", "any", "")],
    outputs=[("out", "bool"), ("index", "number")], tags=["contains"])
def contains(items, value):
    """Есть ли элемент в списке и на какой позиции."""
    data = [txt(v) for v in lst(items)]
    key = txt(value)
    return (key in data), float(data.index(key) if key in data else -1)


@nd("Первый / последний", inputs=[("items", "list", None)],
    outputs=[("first", "any"), ("last", "any")], tags=["first", "last"])
def first_last(items):
    """Первый и последний элементы."""
    data = lst(items)
    if not data:
        raise ValueError("Пустой список")
    return data[0], data[-1]


@nd("Группировка / подсчёт", inputs=[("items", "list", None)],
    outputs=[("counts", "dict"), ("text", "text")], tags=["group"])
def group_count(items):
    """Считает, сколько раз встречается каждый элемент."""
    from collections import Counter
    counter = Counter(txt(v) for v in lst(items))
    return dict(counter), "\n".join(f"{k}: {v}" for k, v in counter.most_common())