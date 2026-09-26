"""Реестр нод: декоратор @node и поиск по библиотеке."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from python_library.core import NodeSpec, Port

# Ключ → NodeSpec
REGISTRY: Dict[str, NodeSpec] = {}

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _slug(value: str) -> str:
    """Латинский идентификатор из произвольной строки."""
    out: List[str] = []
    for ch in str(value).strip().lower():
        if ch in _TRANSLIT:
            out.append(_TRANSLIT[ch])
        elif ch.isalnum():
            out.append(ch)
        elif ch in " _-/":
            out.append("_")
    slug = "".join(out)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "node"


def _as_ports(items: Optional[Sequence[Any]]) -> List[Port]:
    """Превращает краткие описания портов в объекты Port.

    Поддерживается:
      "name"                          — тип any
      ("name", "number")              — тип без значения по умолчанию
      ("name", "number", 0)           — тип и значение
      ("name", "number", 0, "data")   — явная роль точки
      {"name": ..., "type": ..., ...}  — полное описание
      Port(...)                       — готовый порт
    """
    ports: List[Port] = []
    for item in items or []:
        if isinstance(item, Port):
            ports.append(item)
        elif isinstance(item, dict):
            ports.append(Port(**item))
        elif isinstance(item, str):
            ports.append(Port(name=item))
        elif isinstance(item, (tuple, list)):
            name = item[0]
            ptype = item[1] if len(item) > 1 else "any"
            default = item[2] if len(item) > 2 else None
            kind = item[3] if len(item) > 3 else ""
            ports.append(Port(
                name=name, type=ptype, default=default, kind=kind))
        else:
            raise TypeError(f"Неверное описание порта: {item!r}")
    return ports


def register(spec: NodeSpec) -> NodeSpec:
    """Добавляет NodeSpec в реестр."""
    REGISTRY[spec.key] = spec
    return spec


def node(title: str,
         inputs: Optional[Sequence[Any]] = None,
         outputs: Optional[Sequence[Any]] = None,
         category: str = "Общее",
         key: Optional[str] = None,
         tags: Optional[Iterable[str]] = None,
         color: str = "",
         doc: str = "",
         purpose: str = "",
         howto: str = "",
         inputs_doc: Optional[Dict[str, str]] = None,
         outputs_doc: Optional[Dict[str, str]] = None,
         connect_from: str = "",
         connect_to: str = "",
         example: str = "",
         mistakes: str = "",
         see_also: str = "",
         method_handlers: Optional[Dict[str, Callable[..., Any]]] = None,
         property_handlers: Optional[Dict[str, Callable[..., Any]]] = None,
         ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Декоратор регистрации ноды."""

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        node_key = key or f"{_slug(category)}.{fn.__name__}"
        spec = NodeSpec(
            key=node_key,
            title=title,
            category=category,
            inputs=_as_ports(inputs),
            outputs=_as_ports(outputs),
            fn=fn,
            description=(fn.__doc__ or "").strip(),
            tags=list(tags or []),
            color=color,
            doc=doc,
            purpose=purpose,
            howto=howto,
            inputs_doc=dict(inputs_doc or {}),
            outputs_doc=dict(outputs_doc or {}),
            connect_from=connect_from,
            connect_to=connect_to,
            example=example,
            mistakes=mistakes,
            see_also=see_also,
            method_handlers=dict(method_handlers or {}),
            property_handlers=dict(property_handlers or {}),
        )
        register(spec)
        return fn

    return wrapper


def specs_by_category(specs: Optional[Dict[str, NodeSpec]] = None
                      ) -> Dict[str, List[NodeSpec]]:
    """Группирует ноды по категориям (для дерева библиотеки)."""
    source = specs if specs is not None else REGISTRY
    grouped: Dict[str, List[NodeSpec]] = {}
    for spec in source.values():
        grouped.setdefault(spec.category, []).append(spec)
    for items in grouped.values():
        items.sort(key=lambda s: s.title.lower())
    return dict(sorted(grouped.items(), key=lambda kv: kv[0].lower()))


def search_specs(query: str,
                 specs: Optional[Dict[str, NodeSpec]] = None) -> List[NodeSpec]:
    """Поиск нод по названию, категории, описанию и тегам."""
    source = specs if specs is not None else REGISTRY
    words = [w for w in str(query).lower().split() if w]
    if not words:
        return sorted(source.values(), key=lambda s: (s.category, s.title))
    found = [spec for spec in source.values()
             if all(word in spec.search_text for word in words)]
    return sorted(found, key=lambda s: (s.category, s.title))
