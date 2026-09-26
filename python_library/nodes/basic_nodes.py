"""Базовые библиотеки нод: математика, текст, логика, списки,
данные, дата/время, файлы, система и вывод."""
import csv
import datetime as _dt
import io
import json
import math
import os
import platform
import random
import re
import statistics
import uuid

from python_library.nodes._base import flag, library, lst, num, nums, txt

M = library("Math", "1. Математика", "#3f5f8f")
T = library("Text", "2. Текст", "#2f6f55")
L = library("Logic", "3. Логика", "#7a5c2e")
LS = library("List", "4. Списки", "#5a3f7a")
D = library("Data", "5. Данные", "#3d6f7a")
DT = library("Date", "6. Дата и время", "#4a5f7a")
F = library("File", "7. Файлы", "#6a5a3a")
S = library("Sys", "8. Случайное и система", "#4a4a55")
O = library("Output", "9. Вывод", "#5c3a5c")

N = ("number",)


# ======================= 1. Математика =======================
@M("Число", [("value", "number", 0)], [("out", "number")], tags=["константа"])
def number(value):
    """Простое числовое значение."""
    return num(value)


@M("Сложение (+)", [("a", "number", 0), ("b", "number", 0)],
   [("out", "number")])
def add(a, b):
    """Сумма двух чисел."""
    return num(a) + num(b)


@M("Вычитание (−)", [("a", "number", 0), ("b", "number", 0)],
   [("out", "number")])
def sub(a, b):
    """Разность двух чисел."""
    return num(a) - num(b)


@M("Умножение (×)", [("a", "number", 0), ("b", "number", 1)],
   [("out", "number")])
def mul(a, b):
    """Произведение двух чисел."""
    return num(a) * num(b)


@M("Деление (÷)", [("a", "number", 0), ("b", "number", 1)],
   [("out", "number")])
def div(a, b):
    """Деление; деление на ноль даёт ошибку."""
    divisor = num(b)
    if divisor == 0:
        raise ValueError("Деление на ноль")
    return num(a) / divisor


@M("Целое деление", [("a", "number", 0), ("b", "number", 1)],
   [("out", "number")])
def floordiv(a, b):
    """Целая часть от деления."""
    divisor = num(b)
    if divisor == 0:
        raise ValueError("Деление на ноль")
    return float(num(a) // divisor)


@M("Остаток (%)", [("a", "number", 0), ("b", "number", 1)],
   [("out", "number")])
def modulo(a, b):
    """Остаток от деления."""
    divisor = num(b)
    if divisor == 0:
        raise ValueError("Деление на ноль")
    return num(a) % divisor


@M("Степень", [("a", "number", 2), ("b", "number", 2)],
   [("out", "number")])
def power(a, b):
    """Возведение в степень."""
    return num(a) ** num(b)


@M("Корень", [("a", "number", 0)], [("out", "number")])
def sqrt(a):
    """Квадратный корень."""
    value = num(a)
    if value < 0:
        raise ValueError("Корень из отрицательного числа")
    return math.sqrt(value)


@M("Модуль", [("a", "number", 0)], [("out", "number")])
def absolute(a):
    """Абсолютное значение."""
    return abs(num(a))


@M("Округление", [("a", "number", 0), ("digits", "number", 0)],
   [("out", "number")])
def round_number(a, digits):
    """Округляет до заданного числа знаков."""
    return round(num(a), int(num(digits)))


@M("Вниз и вверх", [("a", "number", 0)],
   [("floor", "number"), ("ceil", "number")])
def floor_ceil(a):
    """Округление вниз и вверх."""
    value = num(a)
    return {"floor": float(math.floor(value)), "ceil": float(math.ceil(value))}


@M("Минимум и максимум", [("a", "number", 0), ("b", "number", 0)],
   [("min", "number"), ("max", "number")])
def min_max(a, b):
    """Меньшее и большее из двух чисел."""
    first, second = num(a), num(b)
    return {"min": min(first, second), "max": max(first, second)}


@M("Сумма списка", [("values", "list")], [("out", "number")])
def total(values):
    """Сумма всех чисел списка."""
    return float(sum(nums(values)))


@M("Среднее", [("values", "list")], [("out", "number")])
def average(values):
    """Среднее арифметическое."""
    items = nums(values)
    return float(sum(items) / len(items)) if items else 0.0


@M("Медиана и разброс", [("values", "list")],
   [("median", "number"), ("stdev", "number")])
def median_stdev(values):
    """Медиана и стандартное отклонение."""
    items = nums(values)
    if not items:
        return {"median": 0.0, "stdev": 0.0}
    spread = statistics.pstdev(items) if len(items) > 1 else 0.0
    return {"median": float(statistics.median(items)), "stdev": float(spread)}


@M("Процент", [("value", "number", 0), ("percent", "number", 10)],
   [("out", "number")])
def percent(value, percent):
    """Процент от числа."""
    return num(value) * num(percent) / 100.0


@M("Интерполяция", [("a", "number", 0), ("b", "number", 1),
                    ("t", "number", 0.5)], [("out", "number")])
def lerp(a, b, t):
    """Плавный переход между двумя числами."""
    start, end, factor = num(a), num(b), num(t)
    return start + (end - start) * factor


@M("Ограничить", [("value", "number", 0), ("minimum", "number", 0),
                  ("maximum", "number", 100)], [("out", "number")])
def clamp(value, minimum, maximum):
    """Зажимает значение в диапазон."""
    low, high = num(minimum), num(maximum)
    if low > high:
        low, high = high, low
    return max(low, min(high, num(value)))


@M("Перевести диапазон",
   [("value", "number", 0), ("in_min", "number", 0), ("in_max", "number", 1),
    ("out_min", "number", 0), ("out_max", "number", 100)],
   [("out", "number")])
def remap(value, in_min, in_max, out_min, out_max):
    """Пересчитывает значение из одного диапазона в другой."""
    low, high = num(in_min), num(in_max)
    if high == low:
        return num(out_min)
    ratio = (num(value) - low) / (high - low)
    return num(out_min) + ratio * (num(out_max) - num(out_min))


@M("Синус и косинус", [("angle", "number", 0),
                        {"name": "units", "type": "text", "default": "градусы",
                         "choices": ["градусы", "радианы"]}],
   [("sin", "number"), ("cos", "number")])
def sin_cos(angle, units):
    """Синус и косинус угла."""
    value = num(angle)
    if txt(units) != "радианы":
        value = math.radians(value)
    return {"sin": math.sin(value), "cos": math.cos(value)}


@M("Тангенс", [("angle", "number", 0)], [("out", "number")])
def tangent(angle):
    """Тангенс угла в градусах."""
    return math.tan(math.radians(num(angle)))


@M("Логарифм", [("value", "number", 1), ("base", "number", 10)],
   [("out", "number")])
def logarithm(value, base):
    """Логарифм числа по основанию."""
    number_value, base_value = num(value), num(base, 10)
    if number_value <= 0 or base_value <= 1:
        raise ValueError("Неверные аргументы логарифма")
    return math.log(number_value, base_value)


@M("Экспонента", [("value", "number", 1)], [("out", "number")])
def exponent(value):
    """e в степени value."""
    return math.exp(num(value))


@M("Константы", [{"name": "which", "type": "text", "default": "pi",
                   "choices": ["pi", "e", "tau", "золотое сечение"]}],
   [("out", "number")])
def constants(which):
    """Известные математические константы."""
    return {"pi": math.pi, "e": math.e, "tau": math.tau,
            "золотое сечение": (1 + 5 ** 0.5) / 2}.get(txt(which), math.pi)


@M("Факториал", [("value", "number", 5)], [("out", "number")])
def factorial(value):
    """Факториал целого числа (до 170)."""
    count = int(num(value))
    if count < 0 or count > 170:
        raise ValueError("Допустимы значения от 0 до 170")
    return float(math.factorial(count))


@M("Гипотенуза", [("a", "number", 3), ("b", "number", 4)],
   [("out", "number")])
def hypot(a, b):
    """Длина гипотенузы."""
    return math.hypot(num(a), num(b))


@M("Формула",
   [{"name": "expression", "type": "text", "default": "a + b * 2",
     "hint": "доступны a, b, c и функции math"},
    ("a", "number", 0), ("b", "number", 0), ("c", "number", 0)],
   [("out", "number")])
def formula(expression, a, b, c):
    """Вычисляет арифметическое выражение с a, b, c."""
    scope = {name: getattr(math, name) for name in dir(math)
             if not name.startswith("_")}
    scope.update({"a": num(a), "b": num(b), "c": num(c), "abs": abs,
                  "round": round, "min": min, "max": max})
    return float(eval(str(expression or "0"), {"__builtins__": {}}, scope))


# ======================= 2. Текст =======================
@T("Текст", [{"name": "value", "type": "text", "default": "", "multiline": True}],
   [("out", "text")])
def text(value):
    """Простой текстовый блок."""
    return txt(value)


@T("Соединить", [("a", "text", ""), ("b", "text", ""),
                 ("separator", "text", "")], [("out", "text")])
def concat(a, b, separator):
    """Склеивает две строки."""
    return f"{txt(a)}{txt(separator)}{txt(b)}"


@T("Шаблон", [{"name": "template", "type": "text",
                "default": "Привет, {a}! Вам {b} лет.", "multiline": True},
              ("a", "any", ""), ("b", "any", ""), ("c", "any", "")],
   [("out", "text")])
def template(template, a, b, c):
    """Подставляет значения в шаблон вместо {a}, {b}, {c}."""
    result = txt(template)
    for name, value in (("a", a), ("b", b), ("c", c)):
        result = result.replace("{" + name + "}", txt(value))
    return result


@T("Длина", [("value", "text", "")], [("out", "number")])
def length(value):
    """Количество символов."""
    return float(len(txt(value)))


@T("Разбить", [("value", "text", ""), ("separator", "text", " ")],
   [("out", "list")])
def split(value, separator):
    """Разбивает текст на список."""
    sep = txt(separator) or " "
    return [part for part in txt(value).split(sep)]


@T("Объединить список", [("values", "list"), ("separator", "text", ", ")],
   [("out", "text")])
def join(values, separator):
    """Собирает список в строку."""
    return txt(separator).join(txt(item) for item in lst(values))


@T("ВЕРХНИЙ регистр", [("value", "text", "")], [("out", "text")])
def upper(value):
    """Приводит текст к верхнему регистру."""
    return txt(value).upper()


@T("нижний регистр", [("value", "text", "")], [("out", "text")])
def lower(value):
    """Приводит текст к нижнему регистру."""
    return txt(value).lower()


@T("С большой буквы", [("value", "text", "")], [("out", "text")])
def capitalize(value):
    """Первая буква заглавная."""
    return txt(value).capitalize()


@T("Убрать пробелы", [("value", "text", "")], [("out", "text")])
def strip(value):
    """Удаляет пробелы в начале и конце."""
    return txt(value).strip()


@T("Заменить", [("value", "text", ""), ("old", "text", ""),
                ("new", "text", "")], [("out", "text")])
def replace(value, old, new):
    """Заменяет подстроку."""
    if not txt(old):
        return txt(value)
    return txt(value).replace(txt(old), txt(new))


@T("Содержит", [("value", "text", ""), ("part", "text", "")],
   [("out", "bool")])
def contains(value, part):
    """Есть ли подстрока в тексте."""
    return txt(part) in txt(value)


@T("Найти позицию", [("value", "text", ""), ("part", "text", "")],
   [("out", "number")])
def find(value, part):
    """Позиция подстроки (-1 если нет)."""
    return float(txt(value).find(txt(part)))


@T("Подстрока", [("value", "text", ""), ("start", "number", 0),
                  ("count", "number", 5)], [("out", "text")])
def substring(value, start, count):
    """Вырезает часть текста."""
    begin = int(num(start))
    size = int(num(count))
    return txt(value)[begin:begin + size]


@T("Перевернуть", [("value", "text", "")], [("out", "text")])
def reverse(value):
    """Текст в обратном порядке."""
    return txt(value)[::-1]


@T("Повторить", [("value", "text", ""), ("times", "number", 2)],
   [("out", "text")])
def repeat(value, times):
    """Повторяет текст N раз."""
    count = max(0, min(10000, int(num(times))))
    return txt(value) * count


@T("Выровнять", [("value", "text", ""), ("width", "number", 10),
                 ("fill", "text", " "),
                 {"name": "side", "type": "text", "default": "слева",
                  "choices": ["слева", "справа", "по центру"]}],
   [("out", "text")])
def pad(value, width, fill, side):
    """Добавляет символы до нужной длины."""
    source = txt(value)
    size = int(num(width))
    char = (txt(fill) or " ")[0]
    mode = txt(side)
    if mode == "справа":
        return source.rjust(size, char)
    if mode == "по центру":
        return source.center(size, char)
    return source.ljust(size, char)


@T("Сколько раз", [("value", "text", ""), ("part", "text", "")],
   [("out", "number")])
def count(value, part):
    """Сколько раз встречается подстрока."""
    needle = txt(part)
    return float(txt(value).count(needle)) if needle else 0.0


@T("Найти по шаблону", [("value", "text", ""),
                        ("pattern", "text", "\\d+")], [("out", "list")])
def regex_findall(value, pattern):
    """Все совпадения регулярного выражения."""
    return [str(m) for m in re.findall(txt(pattern), txt(value))]


@T("Замена по шаблону", [("value", "text", ""),
                         ("pattern", "text", "\\s+"), ("new", "text", " ")],
   [("out", "text")])
def regex_replace(value, pattern, new):
    """Замена по регулярному выражению."""
    return re.sub(txt(pattern), txt(new), txt(value))


@T("Проверка по шаблону", [("value", "text", ""),
                          ("pattern", "text", "^\\d+$")], [("out", "bool")])
def regex_match(value, pattern):
    """Подходит ли текст под шаблон."""
    return re.match(txt(pattern), txt(value)) is not None


@T("Формат числа", [("value", "number", 0), ("digits", "number", 2),
                     ("suffix", "text", "")], [("out", "text")])
def format_number(value, digits, suffix):
    """Число с заданным числом знаков и подписью."""
    places = max(0, int(num(digits)))
    return f"{num(value):.{places}f}{txt(suffix)}"


@T("Многострочный текст", [("a", "text", ""), ("b", "text", ""),
                          ("c", "text", "")], [("out", "text")])
def newline(a, b, c):
    """Собирает строки с переносами."""
    parts = [txt(item) for item in (a, b, c) if txt(item)]
    return "\n".join(parts)


@T("Транслит", [("value", "text", "")], [("out", "text")])
def translit(value):
    """Переводит русские буквы в латиницу."""
    from python_library.registry import _slug
    return _slug(txt(value))


# ======================= 3. Логика =======================
@L("Логическое значение", [("value", "bool", False)], [("out", "bool")])
def boolean(value):
    """Да/нет."""
    return flag(value)


@L("Больше (>)", [("a", "number", 0), ("b", "number", 0)],
   [("out", "bool")])
def greater(a, b):
    """a больше b."""
    return num(a) > num(b)


@L("Меньше (<)", [("a", "number", 0), ("b", "number", 0)],
   [("out", "bool")])
def less(a, b):
    """a меньше b."""
    return num(a) < num(b)


@L("Равно (=)", [("a", "any", ""), ("b", "any", "")], [("out", "bool")])
def equal(a, b):
    """Значения равны (сравнение как текста)."""
    return txt(a) == txt(b)


@L("В диапазоне", [("value", "number", 0), ("minimum", "number", 0),
                   ("maximum", "number", 10)], [("out", "bool")])
def between(value, minimum, maximum):
    """Значение попадает в диапазон."""
    return num(minimum) <= num(value) <= num(maximum)


@L("И (AND)", [("a", "bool", False), ("b", "bool", False)], [("out", "bool")])
def logic_and(a, b):
    """Оба условия истинны."""
    return flag(a) and flag(b)


@L("ИЛИ (OR)", [("a", "bool", False), ("b", "bool", False)],
   [("out", "bool")])
def logic_or(a, b):
    """Хотя бы одно условие истинно."""
    return flag(a) or flag(b)


@L("НЕ (NOT)", [("a", "bool", False)], [("out", "bool")])
def logic_not(a):
    """Отрицание."""
    return not flag(a)


@L("Исключающее ИЛИ", [("a", "bool", False), ("b", "bool", False)],
   [("out", "bool")])
def logic_xor(a, b):
    """Истинно ровно одно из условий."""
    return flag(a) != flag(b)


@L("Если — иначе", [("condition", "bool", False), ("then_value", "any", ""),
                    ("else_value", "any", "")], [("out", "any")])
def if_else(condition, then_value, else_value):
    """Выбирает одно из двух значений."""
    return then_value if flag(condition) else else_value


@L("Пустое?", [("value", "any", "")], [("out", "bool")])
def is_empty(value):
    """Проверяет, пусто ли значение."""
    if value is None:
        return True
    if isinstance(value, (list, dict, str)):
        return len(value) == 0
    return False


@L("Значение по умолчанию", [("value", "any", ""),
                              ("fallback", "any", "—")], [("out", "any")])
def default_value(value, fallback):
    """Если значение пустое — берёт замену."""
    if value in (None, "", [], {}):
        return fallback
    return value


@L("Выбор из трёх", [("index", "number", 0), ("a", "any", ""),
                     ("b", "any", ""), ("c", "any", "")], [("out", "any")])
def select3(index, a, b, c):
    """Выбирает значение по номеру 0/1/2."""
    return [a, b, c][max(0, min(2, int(num(index))))]


# ======================= 4. Списки =======================
@LS("Список из текста", [{"name": "value", "type": "text",
                            "default": "1, 2, 3", "multiline": True},
                          ("separator", "text", ",")], [("out", "list")])
def list_from_text(value, separator):
    """Разбивает текст в список."""
    sep = txt(separator) or ","
    return [part.strip() for part in txt(value).split(sep) if part.strip()]


@LS("Собрать список", [("a", "any"), ("b", "any"), ("c", "any"),
                         ("d", "any"), ("e", "any"), ("f", "any")],
    [("out", "list")])
def pack(a, b, c, d, e, f):
    """Собирает до шести значений в список."""
    return [item for item in (a, b, c, d, e, f)
            if item not in (None, "")]


@LS("Объединить списки", [("a", "list"), ("b", "list")],
    [("out", "list")])
def merge(a, b):
    """Склеивает два списка."""
    return lst(a) + lst(b)


@LS("Элемент по номеру", [("values", "list"), ("index", "number", 0)],
    [("out", "any")])
def item_at(values, index):
    """Берёт элемент списка (нумерация с 0)."""
    items = lst(values)
    if not items:
        return None
    position = int(num(index)) % len(items)
    return items[position]


@LS("Длина списка", [("values", "list")], [("out", "number")])
def size(values):
    """Количество элементов."""
    return float(len(lst(values)))


@LS("Сортировать", [("values", "list"), ("descending", "bool", False)],
    [("out", "list")])
def sort(values, descending):
    """Сортирует список (числа как числа)."""
    items = lst(values)
    try:
        items = sorted(items, key=lambda v: float(v), reverse=flag(descending))
    except (TypeError, ValueError):
        items = sorted((txt(v) for v in items), reverse=flag(descending))
    return items


@LS("Перевернуть список", [("values", "list")], [("out", "list")])
def reverse_list(values):
    """Обратный порядок."""
    return list(reversed(lst(values)))


@LS("Только уникальные", [("values", "list")], [("out", "list")])
def unique(values):
    """Убирает повторы, сохраняя порядок."""
    seen = []
    for item in lst(values):
        if item not in seen:
            seen.append(item)
    return seen


@LS("Фильтр по тексту", [("values", "list"), ("part", "text", "")],
    [("out", "list")])
def filter_text(values, part):
    """Оставляет элементы, содержащие подстроку."""
    needle = txt(part).lower()
    return [item for item in lst(values) if needle in txt(item).lower()]


@LS("Фильтр по диапазону", [("values", "list"), ("minimum", "number", 0),
                            ("maximum", "number", 100)], [("out", "list")])
def filter_range(values, minimum, maximum):
    """Оставляет числа в диапазоне."""
    low, high = num(minimum), num(maximum)
    return [item for item in nums(values) if low <= item <= high]


@LS("Умножить все", [("values", "list"), ("factor", "number", 2)],
    [("out", "list")])
def map_scale(values, factor):
    """Умножает каждое число списка."""
    scale = num(factor, 1)
    return [item * scale for item in nums(values)]


@LS("Шаблон для каждого", [("values", "list"),
                             ("template", "text", "• {x}")],
    [("out", "list")])
def map_template(values, template):
    """Применяет шаблон с {x} к каждому элементу."""
    pattern = txt(template) or "{x}"
    return [pattern.replace("{x}", txt(item)) for item in lst(values)]


@LS("Часть списка", [("values", "list"), ("start", "number", 0),
                       ("count", "number", 3)], [("out", "list")])
def slice_list(values, start, count):
    """Берёт часть списка."""
    begin = int(num(start))
    size_value = int(num(count))
    return lst(values)[begin:begin + size_value]


@LS("Диапазон чисел", [("start", "number", 1), ("stop", "number", 10),
                         ("step", "number", 1)], [("out", "list")])
def number_range(start, stop, step):
    """Список чисел от start до stop."""
    begin, end = num(start), num(stop)
    increment = num(step, 1) or 1.0
    items = []
    current = begin
    guard = 0
    while (increment > 0 and current <= end) or (increment < 0 and current >= end):
        items.append(current)
        current += increment
        guard += 1
        if guard > 100000:
            break
    return items


@LS("Перемешать", [("values", "list")], [("out", "list")])
def shuffle(values):
    """Случайный порядок элементов."""
    items = lst(values)
    random.shuffle(items)
    return items


@LS("Есть в списке", [("values", "list"), ("item", "any", "")],
    [("out", "bool")])
def list_contains(values, item):
    """Есть ли такой элемент."""
    return txt(item) in [txt(v) for v in lst(values)]


@LS("Первый и последний", [("values", "list")],
    [("first", "any"), ("last", "any")])
def first_last(values):
    """Первый и последний элементы."""
    items = lst(values)
    if not items:
        return {"first": None, "last": None}
    return {"first": items[0], "last": items[-1]}


@LS("Посчитать повторы", [("values", "list")], [("out", "dict")])
def group_count(values):
    """Сколько раз встречается каждый элемент."""
    result = {}
    for item in lst(values):
        key = txt(item)
        result[key] = result.get(key, 0) + 1
    return result


# ======================= 5. Данные =======================
@D("Словарь из текста", [{"name": "value", "type": "text",
                            "default": "имя = Анна\nвозраст = 30",
                            "multiline": True}], [("out", "dict")])
def dict_from_text(value):
    """Строки вида 'ключ = значение' → словарь."""
    result = {}
    for line in txt(value).splitlines():
        if "=" in line:
            key, _, item = line.partition("=")
            result[key.strip()] = item.strip()
    return result


@D("Значение из словаря", [("data", "dict"), ("key", "text", "")],
   [("out", "any")])
def dict_get(data, key):
    """Берёт значение по ключу."""
    if isinstance(data, dict):
        return data.get(txt(key))
    return None


@D("Записать в словарь", [("data", "dict"), ("key", "text", ""),
                          ("value", "any", "")], [("out", "dict")])
def dict_set(data, key, value):
    """Добавляет или обновляет пару ключ-значение."""
    result = dict(data) if isinstance(data, dict) else {}
    result[txt(key)] = value
    return result


@D("Пары словаря", [("data", "dict")], [("out", "list")])
def dict_items(data):
    """Список строк 'ключ: значение'."""
    if not isinstance(data, dict):
        return []
    return [f"{key}: {txt(value)}" for key, value in data.items()]


@D("Разобрать JSON", [{"name": "value", "type": "text", "default": "{}",
                         "multiline": True}], [("out", "any")])
def json_parse(value):
    """Разбирает JSON-текст."""
    return json.loads(txt(value) or "null")


@D("Собрать JSON", [("value", "any")], [("out", "text")])
def json_dump(value):
    """Превращает значение в JSON-текст."""
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


@D("Разобрать CSV", [{"name": "value", "type": "text",
                        "default": "a;b\n1;2", "multiline": True},
                      ("delimiter", "text", ";")], [("out", "list")])
def csv_parse(value, delimiter):
    """CSV-текст → список строк."""
    reader = csv.reader(io.StringIO(txt(value)),
                        delimiter=(txt(delimiter) or ";")[0])
    return [row for row in reader]


@D("Собрать CSV", [("rows", "list"), ("delimiter", "text", ";")],
   [("out", "text")])
def csv_dump(rows, delimiter):
    """Список строк → CSV-текст."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=(txt(delimiter) or ";")[0],
                        lineterminator="\n")
    for row in lst(rows):
        writer.writerow(row if isinstance(row, (list, tuple)) else [row])
    return buffer.getvalue()


@D("В число", [("value", "any", "")], [("out", "number")])
def to_number(value):
    """Преобразует значение в число."""
    return num(value)


@D("В текст", [("value", "any", "")], [("out", "text")])
def to_text(value):
    """Преобразует значение в текст."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return txt(value)


@D("В логическое", [("value", "any", "")], [("out", "bool")])
def to_bool(value):
    """Преобразует значение в да/нет."""
    return flag(value)


@D("Данные для диаграммы",
   [("labels", "list"), ("values", "list"),
    {"name": "kind", "type": "text", "default": "bar",
     "choices": ["bar", "line", "pie"]}, ("title", "text", "Диаграмма")],
   [("out", "chart")])
def chart_data(labels, values, kind, title):
    """Готовые данные для виджета диаграммы."""
    return {"kind": txt(kind) or "bar", "title": txt(title),
            "labels": [txt(item) for item in lst(labels)],
            "values": nums(values)}


@D("Текстовая таблица", [("rows", "list")], [("out", "text")])
def table_text(rows):
    """Рисует простую таблицу текстом."""
    table = []
    for row in lst(rows):
        cells = row if isinstance(row, (list, tuple)) else [row]
        table.append([txt(cell) for cell in cells])
    if not table:
        return ""
    widths = [max(len(row[i]) if i < len(row) else 0 for row in table)
              for i in range(max(len(row) for row in table))]
    lines = []
    for row in table:
        cells = [(row[i] if i < len(row) else "").ljust(widths[i])
                 for i in range(len(widths))]
        lines.append(" | ".join(cells))
    return "\n".join(lines)


# ======================= 6. Дата и время =======================
@DT("Сейчас", [], [("date", "text"), ("time", "text"), ("iso", "text")])
def now():
    """Текущая дата и время."""
    moment = _dt.datetime.now()
    return {"date": moment.strftime("%d.%m.%Y"),
            "time": moment.strftime("%H:%M:%S"),
            "iso": moment.isoformat(timespec="seconds")}


@DT("Сдвиг дней", [("days", "number", 1),
                   ("start", "text", "")], [("out", "text")])
def shift_days(days, start):
    """Прибавляет дни к дате (формат ДД.ММ.ГГГГ)."""
    base = _dt.datetime.now()
    source = txt(start).strip()
    if source:
        for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                base = _dt.datetime.strptime(source, pattern)
                break
            except ValueError:
                continue
    return (base + _dt.timedelta(days=num(days))).strftime("%d.%m.%Y")


@DT("Формат даты", [("iso", "text", ""),
                     ("pattern", "text", "%d.%m.%Y %H:%M")],
    [("out", "text")])
def format_date(iso, pattern):
    """Форматирует дату в ISO-виде."""
    source = txt(iso).strip()
    moment = _dt.datetime.now()
    if source:
        try:
            moment = _dt.datetime.fromisoformat(source)
        except ValueError:
            pass
    return moment.strftime(txt(pattern) or "%d.%m.%Y")


@DT("Разница дат", [("a", "text", ""), ("b", "text", "")],
    [("days", "number")])
def date_diff(a, b):
    """Сколько дней между датами (ДД.ММ.ГГГГ)."""
    def parse(value):
        for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return _dt.datetime.strptime(txt(value).strip(), pattern)
            except ValueError:
                continue
        return _dt.datetime.now()
    return float((parse(b) - parse(a)).days)


@DT("День недели", [("date", "text", "")], [("out", "text")])
def weekday(date):
    """Название дня недели."""
    names = ["понедельник", "вторник", "среда", "четверг", "пятница",
             "суббота", "воскресенье"]
    source = txt(date).strip()
    moment = _dt.datetime.now()
    if source:
        for pattern in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                moment = _dt.datetime.strptime(source, pattern)
                break
            except ValueError:
                continue
    return names[moment.weekday()]


@DT("Секунды в время", [("seconds", "number", 3600)], [("out", "text")])
def seconds_to_time(seconds):
    """Секунды → чч:мм:сс."""
    total_seconds = int(max(0, num(seconds)))
    hours, rest = divmod(total_seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ======================= 7. Файлы =======================
@F("Прочитать текст", [("path", "file", "")], [("out", "text")])
def read_text(path):
    """Читает текстовый файл (UTF-8)."""
    name = txt(path).strip()
    if not name:
        return ""
    with open(name, "r", encoding="utf-8") as handle:
        return handle.read()


@F("Записать текст", [("path", "file", ""),
                      {"name": "content", "type": "text", "default": "",
                       "multiline": True}, ("append", "bool", False)],
   [("out", "file")])
def write_text(path, content, append):
    """Записывает текст в файл."""
    name = txt(path).strip()
    if not name:
        raise ValueError("Не задан путь к файлу")
    folder = os.path.dirname(os.path.abspath(name))
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(name, "a" if flag(append) else "w", encoding="utf-8") as handle:
        handle.write(txt(content))
    return name


@F("Строки файла", [("path", "file", "")], [("out", "list")])
def read_lines(path):
    """Читает файл как список строк."""
    name = txt(path).strip()
    if not name:
        return []
    with open(name, "r", encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle]


@F("Записать строки", [("path", "file", ""), ("lines", "list")],
   [("out", "file")])
def write_lines(path, lines):
    """Записывает список строк в файл."""
    name = txt(path).strip()
    if not name:
        raise ValueError("Не задан путь к файлу")
    folder = os.path.dirname(os.path.abspath(name))
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(name, "w", encoding="utf-8") as handle:
        handle.write("\n".join(txt(item) for item in lst(lines)))
    return name


@F("Файл существует", [("path", "file", "")],
   [("exists", "bool"), ("size", "number")])
def file_info(path):
    """Есть ли файл и его размер в байтах."""
    name = txt(path).strip()
    if name and os.path.exists(name):
        return {"exists": True, "size": float(os.path.getsize(name))}
    return {"exists": False, "size": 0.0}


@F("Собрать путь", [("folder", "text", ""), ("name", "text", "file.txt")],
   [("out", "file")])
def join_path(folder, name):
    """Склеивает папку и имя файла."""
    return os.path.join(txt(folder), txt(name))


@F("Список файлов", [("folder", "text", "."), ("mask", "text", "")],
   [("out", "list")])
def list_files(folder, mask):
    """Файлы в папке (можно фильтр по расширению)."""
    name = txt(folder).strip() or "."
    if not os.path.isdir(name):
        return []
    pattern = txt(mask).strip().lower()
    items = sorted(os.listdir(name))
    if pattern:
        items = [item for item in items if item.lower().endswith(pattern)]
    return items


# ======================= 8. Случайное и система =======================
@S("Случайное число", [("minimum", "number", 0), ("maximum", "number", 100),
                       ("whole", "bool", True)], [("out", "number")])
def random_number(minimum, maximum, whole):
    """Случайное число из диапазона."""
    low, high = num(minimum), num(maximum, 1)
    if low > high:
        low, high = high, low
    value = random.uniform(low, high)
    return float(round(value)) if flag(whole) else value


@S("Случайный элемент", [("values", "list")], [("out", "any")])
def random_choice(values):
    """Выбирает случайный элемент списка."""
    items = lst(values)
    return random.choice(items) if items else None


@S("Уникальный код", [("short", "bool", True)], [("out", "text")])
def unique_id(short):
    """Генерирует уникальный идентификатор."""
    value = uuid.uuid4().hex
    return value[:8] if flag(short) else value


@S("Сведения о системе", [], [("out", "text")])
def system_info():
    """Короткая информация об ОС и Python."""
    return (f"{platform.system()} {platform.release()}; "
            f"Python {platform.python_version()}")


@S("Переменная среды", [("name", "text", "PATH")], [("out", "text")])
def env_var(name):
    """Значение переменной окружения."""
    return os.environ.get(txt(name), "")


@S("Цвет (HEX)", [("value", "color", "#3d7eff")], [("out", "color")])
def color_hex(value):
    """Цвет в виде #RRGGBB."""
    text_value = txt(value).strip() or "#3d7eff"
    if not text_value.startswith("#"):
        text_value = "#" + text_value
    return text_value


@S("Цвет из RGB", [("r", "number", 61), ("g", "number", 126),
                    ("b", "number", 255)], [("out", "color")])
def color_rgb(r, g, b):
    """Собирает цвет из компонент."""
    def channel(value):
        return max(0, min(255, int(num(value))))
    return "#{:02x}{:02x}{:02x}".format(channel(r), channel(g), channel(b))


@S("Шрифт", [("family", "text", "Arial"), ("size", "number", 11),
            ("bold", "bool", False), ("italic", "bool", False)],
   [("out", "font")])
def font(family, size, bold, italic):
    """Описание шрифта для виджетов."""
    return {"family": txt(family) or "Arial", "size": int(num(size, 11)),
            "bold": flag(bold), "italic": flag(italic)}


# ======================= 9. Вывод =======================
@O("Результат", [("value", "any", ""), ("label", "text", "Результат")],
   [("out", "text")])
def output(value, label):
    """Показывает значение как итог схемы."""
    if isinstance(value, (dict, list)):
        shown = json.dumps(value, ensure_ascii=False, default=str)
    else:
        shown = txt(value)
    prefix = txt(label)
    return f"{prefix}: {shown}" if prefix else shown


@O("Комментарий", [{"name": "note", "type": "text", "default": "Заметка",
                     "multiline": True}], [("out", "text")])
def comment(note):
    """Заметка на полотне, ничего не вычисляет."""
    return txt(note)


@O("Инспектор значения", [("value", "any", "")],
   [("type", "text"), ("preview", "text")])
def inspect_value(value):
    """Показывает тип и содержимое значения."""
    preview = txt(value)
    if isinstance(value, (dict, list)):
        preview = json.dumps(value, ensure_ascii=False, default=str)[:400]
    return {"type": type(value).__name__, "preview": preview}