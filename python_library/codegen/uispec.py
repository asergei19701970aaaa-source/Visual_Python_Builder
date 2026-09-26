"""Описание интерфейса в виде обычных словарей.

Этот модуль НЕ импортирует PyQt6: ноды строят декларативное
описание окна, а генератор кода превращает его в готовые .py файлы.

Структуры:
  widget  -> {'kind': 'widget', 'cls': 'QPushButton', 'name': ..., 'calls': [...],
              'children': [...], 'tooltip': ..., 'stylesheet': ...}
  layout  -> {'kind': 'layout', 'cls': 'QVBoxLayout', 'children': [...]}
  window  -> {'kind': 'window', 'title': ..., 'content': widget|layout,
              'bindings': [...], 'menus': [...]}
"""
import itertools
import re

_COUNTER = itertools.count(1)


def ident(value, fallback="widget"):
    """Превращает произвольную строку в корректное имя Python."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    text = ""
    for ch in str(value or ""):
        low = ch.lower()
        if low in table:
            piece = table[low]
            text += piece.upper() if ch.isupper() and piece else piece
        else:
            text += ch
    text = re.sub(r"[^0-9a-zA-Z_]+", "_", text).strip("_").lower()
    if not text or text[0].isdigit():
        text = f"{fallback}_{text}" if text else fallback
    return text


def widget_name(prefix="widget"):
    """Генерирует уникальное имя виджета."""
    return f"{ident(prefix)}_{next(_COUNTER)}"


def as_list(value):
    """Нормализует вход в список элементов."""
    if value is None or value == "":
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            if item is None or item == "":
                continue
            out.append(item)
        return out
    return [value]


def widget(cls, name=None, calls=None, content=None, children=None, tabs=None,
           tooltip="", stylesheet="", module="QtWidgets", helper=None,
           extra=None):
    """Создаёт описание виджета.

    cls        — имя класса Qt (QPushButton и т.п.)
    calls      — список строк вида 'setText(\"OK\")'
    content    — вложенная компоновка (для контейнеров)
    children   — вложенные виджеты (для QSplitter и др.)
    tabs       — список {'title': ..., 'content': ...} для QTabWidget
    helper     — имя вспомогательного класса ('PaintCanvas', 'ChartView')
    """
    return {
        "kind": "widget",
        "cls": str(cls),
        "module": module,
        "name": ident(name, "widget") if name else widget_name(ident(cls)),
        "calls": [str(c) for c in as_list(calls)],
        "content": content,
        "children": as_list(children),
        "tabs": as_list(tabs),
        "tooltip": str(tooltip or ""),
        "stylesheet": str(stylesheet or ""),
        "helper": helper,
        "extra": dict(extra or {}),
    }


def layout(cls="QVBoxLayout", children=None, calls=None, grid=None, form=None,
           name=None):
    """Создаёт описание компоновки.

    grid — список {'item': ..., 'row': 0, 'col': 0, 'rowspan': 1, 'colspan': 1}
    form — список {'label': 'Имя', 'item': ...}
    """
    return {
        "kind": "layout",
        "cls": str(cls),
        "name": ident(name, "layout") if name else widget_name(ident(cls)),
        "children": as_list(children),
        "calls": [str(c) for c in as_list(calls)],
        "grid": as_list(grid),
        "form": as_list(form),
    }


def spacer(mode="stretch", size=1):
    """Растяжка ('stretch') или фиксированный отступ ('spacing')."""
    return {"kind": "spacer", "mode": str(mode), "size": int(size or 0)}


def action(code, imports=None, label=""):
    """Действие — кусок Python-кода для тела слота."""
    return {
        "kind": "action",
        "code": str(code or "pass"),
        "imports": [str(i) for i in as_list(imports)],
        "label": str(label or ""),
    }


def expression(code, imports=None, label=""):
    """Выражение, которое вычислится во время работы готового приложения."""
    return {
        "kind": "expression",
        "code": str(code or "None"),
        "imports": [str(i) for i in as_list(imports)],
        "label": str(label or ""),
    }


def code_of(value, default="None"):
    """Код runtime-выражения или безопасный литерал обычного значения."""
    if isinstance(value, dict) and value.get("kind") == "expression":
        return str(value.get("code") or default)
    return repr(value)


def runtime(kind, actions=None, **params):
    """Описание состояния или события для генератора приложения."""
    data = {"kind": "runtime_" + str(kind)}
    data.update(params)
    if actions is not None:
        data["actions"] = as_list(actions)
    return data


def binding(target, signal="clicked", actions=None):
    """Связь 'сигнал виджета — действия'."""
    name = target.get("name") if isinstance(target, dict) else ident(target)
    sig = ident(signal or "clicked", "signal")
    return {
        "kind": "binding",
        "widget": name,
        "signal": str(signal or "clicked"),
        "slot": f"on_{name}_{sig}",
        "actions": as_list(actions),
        "target": target if isinstance(target, dict) else None,
    }


def menu_item(text, actions=None, shortcut="", separator=False):
    """Пункт меню."""
    return {
        "kind": "menu_item",
        "text": str(text or "Пункт"),
        "actions": as_list(actions),
        "shortcut": str(shortcut or ""),
        "separator": bool(separator),
    }


def menu(title, items=None):
    """Меню верхней панели."""
    return {"kind": "menu", "title": str(title or "Меню"),
            "items": as_list(items)}


def shape(kind="rect", **params):
    """Графическая фигура для холста рисования."""
    data = {"kind": "shape", "shape": str(kind)}
    data.update(params)
    return data


def window(title="Моё приложение", content=None, bindings=None, width=800,
           height=600, cls="QMainWindow", stylesheet="", icon="",
           statusbar="", menus=None, app_name="MyApp", resizable=True,
           center=True, extra=None):
    """Корневое описание окна приложения."""
    return {
        "kind": "window",
        "cls": str(cls or "QMainWindow"),
        "title": str(title or "Моё приложение"),
        "content": content,
        "bindings": as_list(bindings),
        "menus": as_list(menus),
        "width": int(width or 800),
        "height": int(height or 600),
        "stylesheet": str(stylesheet or ""),
        "icon": str(icon or ""),
        "statusbar": str(statusbar or ""),
        "app_name": ident(app_name or "MyApp", "app"),
        "resizable": bool(resizable),
        "center": bool(center),
        "extra": dict(extra or {}),
    }


def describe(spec, level=0):
    """Краткое текстовое описание дерева интерфейса."""
    if not isinstance(spec, dict):
        return ""
    pad = "  " * level
    kind = spec.get("kind")
    lines = []
    if kind == "window":
        lines.append(f"{pad}Окно: {spec.get('title')} "
                     f"({spec.get('width')}x{spec.get('height')})")
        lines.append(describe(spec.get("content"), level + 1))
        for b in spec.get("bindings", []):
            lines.append(f"{pad}  Сигнал: {b.get('widget')}.{b.get('signal')} "
                         f"→ {b.get('slot')}")
    elif kind == "widget":
        lines.append(f"{pad}{spec.get('cls')} ({spec.get('name')})")
        lines.append(describe(spec.get("content"), level + 1))
        for child in spec.get("children", []):
            lines.append(describe(child, level + 1))
        for tab in spec.get("tabs", []):
            lines.append(f"{pad}  Вкладка: {tab.get('title')}")
            lines.append(describe(tab.get("content"), level + 2))
    elif kind == "layout":
        lines.append(f"{pad}{spec.get('cls')}")
        for child in spec.get("children", []):
            lines.append(describe(child, level + 1))
        for cell in spec.get("grid", []):
            lines.append(describe(cell.get("item"), level + 1))
        for row in spec.get("form", []):
            lines.append(f"{pad}  {row.get('label')}:")
            lines.append(describe(row.get("item"), level + 2))
    elif kind == "spacer":
        lines.append(f"{pad}Отступ ({spec.get('mode')})")
    return "\n".join(l for l in lines if l)