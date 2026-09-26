"""Вспомогательные средства для библиотек нод.

Файл начинается с "_", поэтому loader его не сканирует как библиотеку.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional, Sequence

from python_library.registry import node


def library(prefix: str, category: str, color: str = ""):
    """Создаёт декоратор для группы нод с единым префиксом ключей.

    Пример:
        nd = library('Math', '1. Математика')

        @nd('Сложение', inputs=[('a', 'number', 0)], outputs=[('sum', 'number')])
        def add(a):
            ...

    Ключ ноды получится 'Math.add' и останется стабильным между версиями.
    """

    def nd(title: str,
           inputs: Optional[Sequence[Any]] = None,
           outputs: Optional[Sequence[Any]] = None,
           tags: Optional[Iterable[str]] = None,
           doc: str = "",
           key: Optional[str] = None,
           node_color: str = "",
           **help_fields) -> Callable:
        def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
            full_key = key or f"{prefix}.{fn.__name__}"
            node(title=title, inputs=inputs, outputs=outputs,
                 category=category, key=full_key, tags=tags,
                 color=node_color or color, doc=doc, **help_fields)(fn)
            return fn

        return wrapper

    return nd


def register_simple(nd, key: str, title: str, inputs, outputs, fn,
                    tags=None, doc: str = ""):
    """Регистрация ноды из таблицы (когда функция — lambda)."""
    fn.__name__ = key
    fn.__doc__ = doc or title
    return nd(title, inputs=inputs, outputs=outputs, tags=tags,
              key=None)(fn)


# --------------------------------------------------------- безопасные типы
def num(value: Any, fallback: float = 0.0) -> float:
    """Мягкое преобразование в число."""
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ".").strip())
        except ValueError:
            return float(fallback)
    if isinstance(value, (list, tuple)):
        return float(len(value))
    return float(fallback)


def txt(value: Any) -> str:
    """Мягкое преобразование в текст."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "да" if value else "нет"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def flag(*args, **kwargs) -> bool:
    """Мягкое преобразование в флаг. 
    Принимает любое количество аргументов, защищая от TypeError.
    """
    # 1. Если аргументов вообще нет, возвращаем False
    if not args:
        return False
        
    # 2. Первым аргументом всегда идет проверяемое значение (value)
    value = args[0]
    
    # 3. Вторым аргументом может идти fallback (значение по умолчанию)
    fallback = args[1] if len(args) > 1 else kwargs.get("fallback", False)
    
    # 4. Логика обработки значения
    if value is None:
        return bool(fallback)
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in ("", "none", "null"):
            return bool(fallback)
        return cleaned not in ("0", "нет", "false", "no", "off")
    return bool(value)




def lst(value: Any) -> List[Any]:
    """Мягкое преобразование в список."""
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, str):
        return [p.strip() for p in value.split(",")] if value else []
    return [value]


def nums(value: Any) -> List[float]:
    """Список чисел из любого значения."""
    return [num(v) for v in lst(value)]

def safe_divisor(value, name="делитель"):
    result=num(value,1)
    if result==0: raise ValueError(f"{name} не может быть равен 0")
    return result
def safe_eval_number(expression, variables=None):
    import math
    allowed={k:getattr(math,k) for k in dir(math) if not k.startswith('_')}
    allowed.update({"abs":abs,"round":round,"min":min,"max":max})
    if variables: allowed.update(variables)
    try: return float(eval(str(expression or "0"), {"__builtins__":{}}, allowed))
    except ZeroDivisionError as exc: raise ValueError("Деление на ноль в формуле") from exc
    except Exception as exc: raise ValueError(f"Ошибка в формуле: {exc}") from exc
def strict_key(value):
    return (type(value).__name__, value)
