"""Случайные числа, системная информация, цвета и шрифты."""
import os
import platform
import random
import sys
import uuid

from python_library.nodes._base import library, lst, num, txt

nd = library("Sys", "8. Случайное и система", color="#4a4a55")


@nd("Случайное число", inputs=[("low", "number", 0), ("high", "number", 100),
                              ("whole", "bool", True), ("seed", "number", 0)],
    outputs=[("out", "number")], tags=["random"])
def random_number(low, high, whole, seed):
    """Случайное число в диапазоне."""
    rnd = random.Random(int(num(seed)) or None)
    lo, hi = sorted((num(low), num(high, 100)))
    value = rnd.uniform(lo, hi)
    return float(round(value)) if whole else value


@nd("Случайный элемент", inputs=[("items", "list", None), ("seed", "number", 0)],
    outputs=[("item", "any")], tags=["random", "choice"])
def random_choice(items, seed):
    """Выбирает случайный элемент списка."""
    data = lst(items)
    if not data:
        raise ValueError("Пустой список")
    return random.Random(int(num(seed)) or None).choice(data)


@nd("Уникальный идентификатор", inputs=[("short", "bool", True)],
    outputs=[("out", "text")], tags=["uuid", "id"])
def unique_id(short):
    """Генерирует уникальный идентификатор."""
    value = uuid.uuid4().hex
    return value[:8] if short else value


@nd("Информация о системе", inputs=[],
    outputs=[("os", "text"), ("python", "text"), ("cwd", "text")],
    tags=["system"])
def system_info():
    """ОК, версия Python и текущая папка."""
    return (f"{platform.system()} {platform.release()}",
            sys.version.split()[0], os.getcwd())


@nd("Переменная окружения", inputs=[("name", "text", "HOME"),
                                ("fallback", "text", "")],
    outputs=[("value", "text")], tags=["env"])
def env_var(name, fallback):
    """Читает переменную окружения."""
    return os.environ.get(txt(name), txt(fallback))


@nd("Цвет (HEX)",
    inputs=[{"name": "value", "type": "text", "default": "#3d7eff",
             "hint": "Например #ff8800"}],
    outputs=[("color", "color")], tags=["color", "цвет"])
def color_hex(value):
    """Цвет в формате HEX."""
    v = txt(value).strip() or "#000000"
    return v if v.startswith("#") else f"#{v}"


@nd("Цвет (RGB)", inputs=[("r", "number", 61), ("g", "number", 126),
                        ("b", "number", 255)],
    outputs=[("color", "color")], tags=["color"])
def color_rgb(r, g, b):
    """Собирает цвет из компонент 0–255."""
    def part(v):
        return max(0, min(255, int(num(v))))
    return "#%02x%02x%02x" % (part(r), part(g), part(b))


@nd("Шрифт", inputs=[("family", "text", "Segoe UI"), ("size", "number", 12),
                    ("bold", "bool", False), ("italic", "bool", False)],
    outputs=[("font", "font")], tags=["font", "шрифт"])
def font(family, size, bold, italic):
    """Описание шрифта для виджетов."""
    return {"family": txt(family) or "Segoe UI", "size": int(num(size, 12)),
            "bold": bool(bold), "italic": bool(italic)}