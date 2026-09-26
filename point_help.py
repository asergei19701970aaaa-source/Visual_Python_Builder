"""Practical explanations for every connection point.

The canvas and property panel call :func:`point_help`. This adapter keeps
that stable interface while providing the same detailed, action-oriented
explanation everywhere in the editor.
"""
from __future__ import annotations

from practical_help import port_help, render_help


# Kept as a public compatibility name for older extensions that import it.
# New explanations are generated from the component passport and therefore
# also cover newly added points.
POINT_HELP: dict[str, dict[str, str]] = {}


def point_help(
    component_type: str,
    port_name: str,
    caption: str = "",
    kind: str = "",
    description: str = "",
) -> str:
    """Return a concrete guide for a point, never a generic direction label.

    ``description`` is preserved when a component supplies a specialised
    explanation. The generated guide adds how to connect the point, what
    changes after the connection, a usable example and a common mistake.
    """
    try:
        entry = port_help(component_type, port_name)
    except (KeyError, StopIteration):
        name = caption or port_name or "эта точка"
        detail = description.strip() or f"Помогает использовать «{name}» в работе элемента."
        return (
            f"Что делает: {detail}\n"
            "Как использовать: соедините точку с подходящим действием или значением.\n"
            "Следующий шаг: наведите курсор на линию, чтобы увидеть совместимые продолжения.\n"
            "Частая ошибка: не соединяйте действие с числом или текстом."
        )
    text = render_help(entry)
    if description.strip() and description.strip() not in text:
        text = "Что делает: " + description.strip() + "\n" + text
    return text
