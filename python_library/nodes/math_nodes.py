"""Математика: константы, арифметика, тригонометрия, статистика."""
import math
import statistics

from python_library.nodes._base import library, num, nums

nd = library("Math", "1. Математика", color="#3f5f8f")


@nd("Число", inputs=[("value", "number", 0)], outputs=[("out", "number")],
    tags=["const", "константа"])
def number(value):
    """Константа-число."""
    return num(value)


@nd("Сложение", inputs=[("a", "number", 0), ("b", "number", 0)],
    outputs=[("sum", "number")], tags=["+"])
def add(a, b):
    """a + b"""
    return num(a) + num(b)


@nd("Вычитание", inputs=[("a", "number", 0), ("b", "number", 0)],
    outputs=[("diff", "number")], tags=["-"])
def sub(a, b):
    """a - b"""
    return num(a) - num(b)


@nd("Умножение", inputs=[("a", "number", 1), ("b", "number", 1)],
    outputs=[("product", "number")], tags=["*"])
def mul(a, b):
    """a * b"""
    return num(a) * num(b)


@nd("Деление", inputs=[("a", "number", 0), ("b", "number", 1)],
    outputs=[("quotient", "number")], tags=["/"])
def div(a, b):
    """a / b"""
    return num(a) / num(b, 1)


@nd("Целое деление", inputs=[("a", "number", 0), ("b", "number", 1)],
    outputs=[("out", "number")], tags=["//"])
def floordiv(a, b):
    """a // b"""
    return float(num(a) // num(b, 1))


@nd("Остаток", inputs=[("a", "number", 0), ("b", "number", 1)],
    outputs=[("mod", "number")], tags=["%"])
def modulo(a, b):
    """Остаток от деления."""
    return math.fmod(num(a), num(b, 1))


@nd("Степень", inputs=[("a", "number", 2), ("b", "number", 2)],
    outputs=[("out", "number")], tags=["pow"])
def power(a, b):
    """a в степени b."""
    return num(a) ** num(b)


@nd("Корень", inputs=[("value", "number", 4)], outputs=[("out", "number")],
    tags=["sqrt"])
def sqrt(value):
    """Квадратный корень."""
    return math.sqrt(num(value))


@nd("Модуль", inputs=[("value", "number", 0)], outputs=[("out", "number")],
    tags=["abs"])
def absolute(value):
    """Абсолютное значение."""
    return abs(num(value))


@nd("Округление", inputs=[("value", "number", 0), ("digits", "number", 0)],
    outputs=[("out", "number")], tags=["round"])
def round_number(value, digits):
    """Округлить до N знаков."""
    return round(num(value), int(num(digits)))


@nd("Вниз / вверх", inputs=[("value", "number", 0)],
    outputs=[("floor", "number"), ("ceil", "number")], tags=["floor", "ceil"])
def floor_ceil(value):
    """Округление вниз и вверх."""
    v = num(value)
    return float(math.floor(v)), float(math.ceil(v))


@nd("Минимум из двух", inputs=[("a", "number", 0), ("b", "number", 0)],
    outputs=[("out", "number")], tags=["min"])
def min2(a, b):
    """Меньшее из двух чисел."""
    return min(num(a), num(b))


@nd("Максимум из двух", inputs=[("a", "number", 0), ("b", "number", 0)],
    outputs=[("out", "number")], tags=["max"])
def max2(a, b):
    """Большее из двух чисел."""
    return max(num(a), num(b))


@nd("Мин/Макс списка", inputs=[("items", "list", None)],
    outputs=[("min", "number"), ("max", "number")], tags=["min", "max"])
def min_max(items):
    """Минимум и максимум списка чисел."""
    data = nums(items)
    if not data:
        raise ValueError("Пустой список")
    return min(data), max(data)


@nd("Сумма списка", inputs=[("items", "list", None)],
    outputs=[("sum", "number")], tags=["sum"])
def total(items):
    """Сумма всех чисел списка."""
    return float(sum(nums(items)))


@nd("Среднее", inputs=[("items", "list", None)],
    outputs=[("avg", "number")], tags=["mean"])
def average(items):
    """Среднее арифметическое."""
    data = nums(items)
    if not data:
        raise ValueError("Пустой список")
    return sum(data) / len(data)


@nd("Медиана и разброс", inputs=[("items", "list", None)],
    outputs=[("median", "number"), ("stdev", "number")], tags=["median"])
def median_stdev(items):
    """Медиана и стандартное отклонение."""
    data = nums(items)
    if not data:
        raise ValueError("Пустой список")
    dev = statistics.pstdev(data) if len(data) > 1 else 0.0
    return statistics.median(data), dev


@nd("Процент", inputs=[("value", "number", 0), ("percent", "number", 10)],
    outputs=[("out", "number")], tags=["%"])
def percent(value, percent):
    """Сколько составляет N% от числа."""
    return num(value) * num(percent) / 100.0


@nd("Интерполяция", inputs=[("a", "number", 0), ("b", "number", 1),
                        ("t", "number", 0.5)],
    outputs=[("out", "number")], tags=["lerp"])
def lerp(a, b, t):
    """Линейная интерполяция между a и b."""
    return num(a) + (num(b) - num(a)) * num(t, 0.5)


@nd("Ограничить", inputs=[("value", "number", 0), ("low", "number", 0),
                      ("high", "number", 100)],
    outputs=[("out", "number")], tags=["clamp"])
def clamp(value, low, high):
    """Зажать число в диапазоне."""
    lo, hi = sorted((num(low), num(high, 100)))
    return max(lo, min(hi, num(value)))


@nd("Перевести диапазон",
    inputs=[("value", "number", 0), ("in_min", "number", 0),
            ("in_max", "number", 1), ("out_min", "number", 0),
            ("out_max", "number", 100)],
    outputs=[("out", "number")], tags=["map", "remap"])
def remap(value, in_min, in_max, out_min, out_max):
    """Пересчёт значения из одного диапазона в другой."""
    i0, i1 = num(in_min), num(in_max, 1)
    if i1 == i0:
        raise ValueError("Пустой входной диапазон")
    k = (num(value) - i0) / (i1 - i0)
    return num(out_min) + k * (num(out_max, 100) - num(out_min))


@nd("Синус/Косинус", inputs=[("angle", "number", 0), ("degrees", "bool", True)],
    outputs=[("sin", "number"), ("cos", "number")], tags=["sin", "cos"])
def sin_cos(angle, degrees):
    """Синус и косинус угла."""
    a = num(angle)
    if degrees:
        a = math.radians(a)
    return math.sin(a), math.cos(a)


@nd("Тангенс", inputs=[("angle", "number", 0), ("degrees", "bool", True)],
    outputs=[("out", "number")], tags=["tan"])
def tangent(angle, degrees):
    """Тангенс угла."""
    a = num(angle)
    return math.tan(math.radians(a) if degrees else a)


@nd("Логарифм", inputs=[("value", "number", 1), ("base", "number", 10)],
    outputs=[("out", "number")], tags=["log"])
def logarithm(value, base):
    """Логарифм по основанию."""
    return math.log(num(value, 1), num(base, 10))


@nd("Экспонента", inputs=[("value", "number", 1)],
    outputs=[("out", "number")], tags=["exp"])
def exponent(value):
    """e в степени value."""
    return math.exp(num(value))


@nd("Константы π и e", inputs=[],
    outputs=[("pi", "number"), ("e", "number")], tags=["pi"])
def constants():
    """Математические константы."""
    return math.pi, math.e


@nd("Факториал", inputs=[("value", "number", 5)],
    outputs=[("out", "number")], tags=["factorial"])
def factorial(value):
    """Факториал целого числа."""
    return float(math.factorial(int(num(value))))


@nd("Гипотенуза", inputs=[("a", "number", 3), ("b", "number", 4)],
    outputs=[("out", "number")], tags=["hypot"])
def hypot(a, b):
    """Длина вектора (a, b)."""
    return math.hypot(num(a), num(b))


@nd("Формула (выражение)",
    inputs=[{"name": "expr", "type": "text", "default": "a * b + 1",
             "hint": "Доступны a, b, c и функции math"},
            ("a", "number", 2), ("b", "number", 3), ("c", "number", 0)],
    outputs=[("out", "number")], tags=["eval", "formula"])
def formula(expr, a, b, c):
    """Вычисляет арифметическое выражение."""
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"a": num(a), "b": num(b), "c": num(c),
                    "abs": abs, "round": round, "min": min, "max": max})
    return float(eval(str(expr or "0"), {"__builtins__": {}}, allowed))