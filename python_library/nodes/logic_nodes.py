"""Логика, сравнения и вывод результатов."""
from python_library.nodes._base import flag, library, num, txt

nd = library("Logic", "3. Логика", color="#7a5c2e")
out_nd = library("Output", "9. Вывод", color="#5c3a5c")


@nd("Флаг (да/нет)", inputs=[("value", "bool", False)],
    outputs=[("out", "bool")], tags=["bool"])
def boolean(value):
    """Константа-флаг."""
    return flag(value)


@nd("Больше чем", inputs=[("a", "number", 0), ("b", "number", 0)],
    outputs=[("out", "bool")], tags=[">"])
def greater(a, b):
    """a > b"""
    return num(a) > num(b)


@nd("Меньше чем", inputs=[("a", "number", 0), ("b", "number", 0)],
    outputs=[("out", "bool")], tags=["<"])
def less(a, b):
    """a < b"""
    return num(a) < num(b)


@nd("Равно", inputs=[("a", "any", None), ("b", "any", None)],
    outputs=[("out", "bool")], tags=["=="])
def equal(a, b):
    """Сравнение значений."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return num(a) == num(b)
    return txt(a) == txt(b)


@nd("В диапазоне", inputs=[("value", "number", 0), ("low", "number", 0),
                          ("high", "number", 10)],
    outputs=[("out", "bool")], tags=["between"])
def between(value, low, high):
    """Находится ли число в диапазоне."""
    lo, hi = sorted((num(low), num(high, 10)))
    return lo <= num(value) <= hi


@nd("И (AND)", inputs=[("a", "bool", False), ("b", "bool", False)],
    outputs=[("out", "bool")], tags=["and"])
def logic_and(a, b):
    """Оба условия истинны."""
    return flag(a) and flag(b)


@nd("ИЛИ (OR)", inputs=[("a", "bool", False), ("b", "bool", False)],
    outputs=[("out", "bool")], tags=["or"])
def logic_or(a, b):
    """Хотя бы одно условие истинно."""
    return flag(a) or flag(b)


@nd("НЕ (NOT)", inputs=[("value", "bool", False)],
    outputs=[("out", "bool")], tags=["not"])
def logic_not(value):
    """Инверсия флага."""
    return not flag(value)


@nd("Исключающее ИЛИ", inputs=[("a", "bool", False), ("b", "bool", False)],
    outputs=[("out", "bool")], tags=["xor"])
def logic_xor(a, b):
    """Истинно, когда верно ровно одно условие."""
    return flag(a) != flag(b)


@nd("Если (If)", inputs=[("condition", "bool", False), ("if_true", "any", None),
                        ("if_false", "any", None)],
    outputs=[("out", "any")], tags=["if", "ветвление"])
def if_else(condition, if_true, if_false):
    """Выбор одного из двух значений."""
    return if_true if flag(condition) else if_false


@nd("Пусто?", inputs=[("value", "any", None)],
    outputs=[("out", "bool")], tags=["empty"])
def is_empty(value):
    """Проверяет, пустое ли значение."""
    if value is None:
        return True
    if isinstance(value, (str, list, tuple, dict, set)):
        return len(value) == 0
    return False


@nd("Значение по умолчанию", inputs=[("value", "any", None),
                                 ("fallback", "any", "")],
    outputs=[("out", "any")], tags=["default"])
def default_value(value, fallback):
    """Если значение пустое — взять замену."""
    if value in (None, "", [], {}):
        return fallback
    return value


@nd("Выбор из трёх", inputs=[("index", "number", 0), ("a", "any", None),
                            ("b", "any", None), ("c", "any", None)],
    outputs=[("out", "any")], tags=["switch"])
def select3(index, a, b, c):
    """Выбирает a/b/c по номеру 0/1/2."""
    return [a, b, c][max(0, min(2, int(num(index))))]


@out_nd("Вывод (Output)", inputs=[("value", "any", None)],
        outputs=[("value", "any")], tags=["print", "результат"])
def output(value):
    """Терминальная нода: показывает результат на холсте."""
    return value


@out_nd("Заметка / комментарий",
        inputs=[{"name": "text", "type": "text", "default": "Пояснение…",
                 "multiline": True}],
        outputs=[("out", "text")], tags=["comment"])
def comment(text):
    """Нода-заметка для пояснений на схеме."""
    return txt(text)


@out_nd("Инспектор значения", inputs=[("value", "any", None)],
        outputs=[("type", "text"), ("preview", "text")], tags=["debug"])
def inspect_value(value):
    """Показывает тип и краткое содержимое значения."""
    preview = txt(value)
    if len(preview) > 300:
        preview = preview[:300] + "…"
    return type(value).__name__, preview