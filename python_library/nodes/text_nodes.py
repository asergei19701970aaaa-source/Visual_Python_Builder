"""Текст: создание, склейка, поиск, замена, форматирование, регулярки."""
import re

from python_library.nodes._base import library, lst, num, txt

nd = library("Text", "2. Текст", color="#2f6f55")


@nd("Текст", inputs=[{"name": "value", "type": "text", "default": "",
                          "multiline": True}],
    outputs=[("out", "text")], tags=["string", "строка"])
def text(value):
    """Константа-текст (можно многострочный)."""
    return txt(value)


@nd("Склейка", inputs=[("a", "text", ""), ("b", "text", ""),
                     ("sep", "text", " ")],
    outputs=[("out", "text")], tags=["concat"])
def concat(a, b, sep):
    """Соединяет две строки через разделитель."""
    return f"{txt(a)}{txt(sep)}{txt(b)}"


@nd("Шаблон", inputs=[{"name": "template", "type": "text",
                          "default": "Привет, {a}!", "multiline": True,
                          "hint": "Подстановки {a} {b} {c}"},
                     ("a", "any", ""), ("b", "any", ""), ("c", "any", "")],
    outputs=[("out", "text")], tags=["format"])
def template(template, a, b, c):
    """Подставляет значения в шаблон."""
    try:
        return txt(template).format(a=txt(a), b=txt(b), c=txt(c))
    except (KeyError, IndexError, ValueError) as exc:
        raise ValueError(f"Ошибка шаблона: {exc}")


@nd("Длина", inputs=[("value", "any", "")], outputs=[("length", "number")],
    tags=["len"])
def length(value):
    """Длина строки или списка."""
    if value is None:
        return 0.0
    if isinstance(value, (list, tuple, dict, str)):
        return float(len(value))
    return float(len(txt(value)))


@nd("Разбить", inputs=[("value", "text", ""), ("sep", "text", ",")],
    outputs=[("items", "list")], tags=["split"])
def split(value, sep):
    """Разбивает текст на список."""
    return [p.strip() for p in txt(value).split(txt(sep) or ",")]


@nd("Собрать из списка", inputs=[("items", "list", None), ("sep", "text", ", ")],
    outputs=[("out", "text")], tags=["join"])
def join(items, sep):
    """Собирает список в строку."""
    return txt(sep).join(txt(v) for v in lst(items))


@nd("Верхний регистр", inputs=[("value", "text", "")],
    outputs=[("out", "text")], tags=["upper"])
def upper(value):
    """ВСЁ ЗАГЛАВНЫМИ."""
    return txt(value).upper()


@nd("Нижний регистр", inputs=[("value", "text", "")],
    outputs=[("out", "text")], tags=["lower"])
def lower(value):
    """всё строчными."""
    return txt(value).lower()


@nd("С большой буквы", inputs=[("value", "text", "")],
    outputs=[("out", "text")], tags=["capitalize"])
def capitalize(value):
    """Первая буква заглавная."""
    s = txt(value)
    return s[:1].upper() + s[1:]


@nd("Убрать пробелы", inputs=[("value", "text", "")],
    outputs=[("out", "text")], tags=["strip", "trim"])
def strip(value):
    """Удаляет пробелы в начале и конце."""
    return txt(value).strip()


@nd("Замена", inputs=[("value", "text", ""), ("old", "text", ""),
                     ("new", "text", "")],
    outputs=[("out", "text")], tags=["replace"])
def replace(value, old, new):
    """Заменяет подстроку."""
    return txt(value).replace(txt(old), txt(new))


@nd("Содержит?", inputs=[("value", "text", ""), ("needle", "text", "")],
    outputs=[("out", "bool")], tags=["contains"])
def contains(value, needle):
    """Есть ли подстрока в тексте."""
    return txt(needle) in txt(value)


@nd("Найти позицию", inputs=[("value", "text", ""), ("needle", "text", "")],
    outputs=[("index", "number")], tags=["find"])
def find(value, needle):
    """Позиция подстроки (-1 если нет)."""
    return float(txt(value).find(txt(needle)))


@nd("Подстрока", inputs=[("value", "text", ""), ("start", "number", 0),
                       ("count", "number", 5)],
    outputs=[("out", "text")], tags=["slice"])
def substring(value, start, count):
    """Вырезает часть строки."""
    s = txt(value)
    i, n = int(num(start)), int(num(count, 5))
    return s[i:i + n] if n > 0 else s[i:]


@nd("Перевернуть", inputs=[("value", "text", "")],
    outputs=[("out", "text")], tags=["reverse"])
def reverse(value):
    """Текст наоборот."""
    return txt(value)[::-1]


@nd("Повторить", inputs=[("value", "text", "ab"), ("times", "number", 3)],
    outputs=[("out", "text")], tags=["repeat"])
def repeat(value, times):
    """Повторяет текст N раз."""
    return txt(value) * max(0, int(num(times, 1)))


@nd("Выравнивание", inputs=[("value", "text", ""), ("width", "number", 10),
                          {"name": "mode", "type": "text", "default": "left",
                           "choices": ["left", "right", "center"]},
                          ("filler", "text", " ")],
    outputs=[("out", "text")], tags=["pad"])
def pad(value, width, mode, filler):
    """Добивает текст до нужной ширины."""
    s, w = txt(value), int(num(width, 10))
    f = (txt(filler) or " ")[0]
    if mode == "right":
        return s.rjust(w, f)
    if mode == "center":
        return s.center(w, f)
    return s.ljust(w, f)


@nd("Количество вхождений", inputs=[("value", "text", ""),
                               ("needle", "text", "a")],
    outputs=[("count", "number")], tags=["count"])
def count(value, needle):
    """Сколько раз встречается подстрока."""
    return float(txt(value).count(txt(needle) or " "))


@nd("Регулярка: найти всё",
    inputs=[("value", "text", ""), ("pattern", "text", r"\d+")],
    outputs=[("items", "list"), ("count", "number")], tags=["regex"])
def regex_findall(value, pattern):
    """Все совпадения регулярного выражения."""
    found = re.findall(txt(pattern) or r"\d+", txt(value))
    flat = [m if isinstance(m, str) else "".join(m) for m in found]
    return flat, float(len(flat))


@nd("Регулярка: замена",
    inputs=[("value", "text", ""), ("pattern", "text", r"\s+"),
            ("replacement", "text", " ")],
    outputs=[("out", "text")], tags=["regex"])
def regex_replace(value, pattern, replacement):
    """Замена по регулярному выражению."""
    return re.sub(txt(pattern) or r"\s+", txt(replacement), txt(value))


@nd("Регулярка: проверка",
    inputs=[("value", "text", ""), ("pattern", "text", r"^\w+@\w+\.\w+$")],
    outputs=[("ok", "bool")], tags=["regex", "валидация"])
def regex_match(value, pattern):
    """Подходит ли текст под шаблон."""
    return bool(re.match(txt(pattern) or ".*", txt(value)))


@nd("Формат числа", inputs=[("value", "number", 0), ("digits", "number", 2),
                          ("suffix", "text", "")],
    outputs=[("out", "text")], tags=["format"])
def format_number(value, digits, suffix):
    """Число в текст с заданной точностью."""
    d = max(0, int(num(digits, 2)))
    return f"{num(value):.{d}f}{txt(suffix)}"


@nd("Перенос строки", inputs=[("a", "text", ""), ("b", "text", "")],
    outputs=[("out", "text")], tags=["newline"])
def newline(a, b):
    """Склеивает две строки через перевод строки."""
    return txt(a) + "\n" + txt(b)


@nd("Транслит", inputs=[("value", "text", "Привет")],
    outputs=[("out", "text")], tags=["translit", "латиница"])
def translit(value):
    """Русский текст латиницей (удобно для имён виджетов)."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya", " ": "_",
    }
    out = []
    for ch in txt(value):
        low = ch.lower()
        piece = table.get(low, ch if ch.isalnum() or ch in "_-." else "")
        out.append(piece.upper() if ch.isupper() and piece else piece)
    return "".join(out)