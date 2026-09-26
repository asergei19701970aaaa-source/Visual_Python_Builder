"""GUI: окно приложения, меню и статус-строка."""
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, lst, num, txt

nd = library("Window", "15. GUI: Окно", color="#7a3f5f")


@nd("Окно приложения",
    inputs=[("title", "text", "Моё приложение"), ("content", "layout", None),
            ("bindings", "events", None), ("menus", "list", None),
            ("width", "number", 900), ("height", "number", 600),
            ("style", "style", ""), ("statusbar", "text", "Готово"),
            ("app_name", "text", "MyApp"), ("icon", "text", "")],
    outputs=[("window", "window")], tags=["window", "окно", "main"])
def app_window(title, content, bindings, menus, width, height, style,
               statusbar, app_name, icon):
    """Главное окно. Подключите сюда компоновку и связи сигналов."""
    return u.window(
        title=txt(title), content=content,
        bindings=[b for b in lst(bindings) if isinstance(b, dict)],
        menus=[m for m in lst(menus) if isinstance(m, dict)],
        width=int(num(width, 900)), height=int(num(height, 600)),
        stylesheet=txt(style), statusbar=txt(statusbar),
        app_name=txt(app_name) or "MyApp", icon=txt(icon))


@nd("Диалоговое окно",
    inputs=[("title", "text", "Диалог"), ("content", "layout", None),
            ("bindings", "events", None), ("width", "number", 480),
            ("height", "number", 320), ("style", "style", ""),
            ("app_name", "text", "MyDialog")],
    outputs=[("window", "window")], tags=["dialog"])
def dialog_window(title, content, bindings, width, height, style, app_name):
    """Окно на базе QDialog (без меню и статус-строки)."""
    return u.window(title=txt(title), content=content,
                    bindings=[b for b in lst(bindings) if isinstance(b, dict)],
                    width=int(num(width, 480)), height=int(num(height, 320)),
                    cls="QDialog", stylesheet=txt(style),
                    app_name=txt(app_name) or "MyDialog")


@nd("Пункт меню", inputs=[("text", "text", "Открыть…"),
                        ("actions", "list", None, "data"),
                        ("shortcut", "text", ""), ("separator", "bool", False)],
    outputs=[("item", "action")], tags=["menu"])
def menu_item(text, actions, shortcut, separator):
    """Один пункт меню с действиями."""
    return u.menu_item(txt(text), [a for a in lst(actions) if isinstance(a, dict)],
                       txt(shortcut), flag(separator))


@nd("Меню", inputs=[("title", "text", "Файл"),
                    ("items", "list", None, "data")],
    outputs=[("menu", "menu")], tags=["menu"])
def menu(title, items):
    """Меню верхней панели окна."""
    return u.menu(txt(title), [i for i in lst(items) if isinstance(i, dict)])


@nd("Собрать меню/связи в список",
    inputs=[("a", "any", None), ("b", "any", None), ("c", "any", None),
            ("d", "any", None), ("e", "any", None), ("f", "any", None)],
    outputs=[("items", "list")], tags=["pack"])
def collect(a, b, c, d, e, f):
    """Собирает меню, связи или действия в один список."""
    out = []
    for v in (a, b, c, d, e, f):
        if isinstance(v, dict):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            out.extend(x for x in v if isinstance(x, dict))
    return out
