"""GUI: стили (QSS) для виджетов и окон."""
from python_library.nodes._base import flag, library, num, txt

nd = library("Style", "14. GUI: Стиль", color="#5f7a3f")

DARK = """
QWidget { background: #1f232b; color: #e6e9ef; font-size: 14px; }
QPushButton { background: #2f6f55; border: none; border-radius: 6px;
              padding: 8px 14px; color: #ffffff; }
QPushButton:hover { background: #388566; }
QPushButton:disabled { background: #3a4150; color: #98a2b3; }
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #262b34; border: 1px solid #3a4150; border-radius: 6px;
    padding: 6px; color: #e6e9ef; }
QTableWidget, QListWidget, QTreeWidget { background: #262b34;
    border: 1px solid #3a4150; }
""".strip()

LIGHT = """
QWidget { background: #f5f6f8; color: #1f232b; font-size: 14px; }
QPushButton { background: #3d7eff; border: none; border-radius: 6px;
              padding: 8px 14px; color: #ffffff; }
QPushButton:hover { background: #2f6ae0; }
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #ffffff; border: 1px solid #c7ccd6; border-radius: 6px;
    padding: 6px; }
""".strip()


@nd("Готовая тема",
    inputs=[{"name": "theme", "type": "text", "default": "dark",
             "choices": ["dark", "light"]}],
    outputs=[("style", "style")], tags=["theme", "qss"])
def theme(theme):
    """Тёмная или светлая тема оформления."""
    return DARK if txt(theme) != "light" else LIGHT


@nd("Стиль виджета",
    inputs=[("background", "color", ""), ("color", "color", ""),
            ("radius", "number", 6), ("padding", "number", 6),
            ("font_size", "number", 0), ("bold", "bool", False),
            ("border", "text", "")],
    outputs=[("style", "style")], tags=["qss", "цвет"])
def widget_style(background, color, radius, padding, font_size, bold, border):
    """Собирает QSS-строку для одного виджета."""
    parts = []
    if txt(background):
        parts.append(f"background: {txt(background)};")
    if txt(color):
        parts.append(f"color: {txt(color)};")
    if num(radius) > 0:
        parts.append(f"border-radius: {int(num(radius))}px;")
    if num(padding) > 0:
        parts.append(f"padding: {int(num(padding))}px;")
    if num(font_size) > 0:
        parts.append(f"font-size: {int(num(font_size))}px;")
    if flag(bold):
        parts.append("font-weight: bold;")
    if txt(border):
        parts.append(f"border: {txt(border)};")
    return " ".join(parts)


@nd("Произвольный QSS",
    inputs=[{"name": "value", "type": "text", "default": "QWidget { }",
             "multiline": True}],
    outputs=[("style", "style")], tags=["qss"])
def custom_style(value):
    """Произвольный текст таблицы стилей."""
    return txt(value)


@nd("Объединить стили", inputs=[("a", "style", ""), ("b", "style", ""),
                              ("c", "style", "")],
    outputs=[("style", "style")], tags=["qss"])
def merge_style(a, b, c):
    """Склеивает несколько стилей."""
    return "\n".join(p for p in (txt(a), txt(b), txt(c)) if p)