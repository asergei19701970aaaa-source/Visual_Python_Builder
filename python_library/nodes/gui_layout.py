"""GUI: компоновки (расположение виджетов)."""
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, lst, num, txt

nd = library("Layout", "12. GUI: Компоновка", color="#3a6f8f")


def _items(*values):
    out = []
    for v in values:
        if isinstance(v, dict):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            out.extend(x for x in v if isinstance(x, dict))
    return out


def _margins(layout, margin, spacing):
    m, s = int(num(margin)), int(num(spacing))
    if m >= 0:
        layout["calls"].append(f"setContentsMargins({m}, {m}, {m}, {m})")
    if s >= 0:
        layout["calls"].append(f"setSpacing({s})")
    return layout


@nd("Вертикально (VBox)",
    inputs=[("a", "widget", None), ("b", "widget", None), ("c", "widget", None),
            ("d", "widget", None), ("extra", "list", None),
            ("margin", "number", 12), ("spacing", "number", 8),
            ("name", "text", "vertical_layout")],
    outputs=[("layout", "layout")], tags=["vbox", "колонка"])
def vbox(a, b, c, d, extra, margin, spacing, name):
    """QVBoxLayout — элементы друг под другом."""
    return _margins(u.layout(
        "QVBoxLayout", children=_items(a, b, c, d, lst(extra)), name=name),
                    margin, spacing)


@nd("Горизонтально (HBox)",
    inputs=[("a", "widget", None), ("b", "widget", None), ("c", "widget", None),
            ("d", "widget", None), ("extra", "list", None),
            ("margin", "number", 12), ("spacing", "number", 8),
            ("name", "text", "horizontal_layout")],
    outputs=[("layout", "layout")], tags=["hbox", "строка"])
def hbox(a, b, c, d, extra, margin, spacing, name):
    """QHBoxLayout — элементы в ряд."""
    return _margins(u.layout(
        "QHBoxLayout", children=_items(a, b, c, d, lst(extra)), name=name),
                    margin, spacing)


@nd("Сетка (Grid)",
    inputs=[("items", "list", None), ("columns", "number", 2),
            ("margin", "number", 12), ("spacing", "number", 8),
            ("name", "text", "grid_layout")],
    outputs=[("layout", "layout")], tags=["grid", "таблица"])
def grid(items, columns, margin, spacing, name):
    """QGridLayout — элементы по ячейкам сетки."""
    cols = max(1, int(num(columns, 2)))
    cells = []
    for i, item in enumerate(x for x in lst(items) if isinstance(x, dict)):
        cells.append({"item": item, "row": i // cols, "col": i % cols})
    return _margins(
        u.layout("QGridLayout", grid=cells, name=name), margin, spacing)


@nd("Форма (подпись + поле)",
    inputs=[("labels", "list", None), ("fields", "list", None),
            ("margin", "number", 12), ("spacing", "number", 8),
            ("name", "text", "form_layout")],
    outputs=[("layout", "layout")], tags=["form"])
def form(labels, fields, margin, spacing, name):
    """QFormLayout — пары 'подпись — поле'."""
    names = [txt(v) for v in lst(labels)]
    widgets = [w for w in lst(fields) if isinstance(w, dict)]
    rows = []
    for i, w in enumerate(widgets):
        rows.append({"label": names[i] if i < len(names) else f"Поле {i + 1}",
                     "item": w})
    return _margins(
        u.layout("QFormLayout", form=rows, name=name), margin, spacing)


@nd("Растяжка", inputs=[], outputs=[("item", "widget")], tags=["stretch"])
def stretch():
    """Пустое растягивающееся пространство."""
    return u.spacer("stretch")


@nd("Отступ", inputs=[("size", "number", 12)],
    outputs=[("item", "widget")], tags=["spacing"])
def spacing(size):
    """Фиксированный отступ в пикселях."""
    return u.spacer("spacing", int(num(size, 12)))


@nd("Контейнер (виджет из компоновки)",
    inputs=[("content", "layout", None), ("name", "text", ""),
            ("style", "style", "")],
    outputs=[("widget", "widget")], tags=["container"])
def container(content, name, style):
    """Оборачивает компоновку в QWidget."""
    return u.widget("QWidget", name=name or "panel", content=content,
                    stylesheet=txt(style))


@nd("Разделитель областей (Splitter)",
    inputs=[("a", "widget", None), ("b", "widget", None),
            ("vertical", "bool", False), ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["splitter"])
def splitter(a, b, vertical, name):
    """QSplitter — две области с подвижной границей."""
    orient = "Vertical" if flag(vertical) else "Horizontal"
    return u.widget("QSplitter", name=name or "splitter",
                    calls=[f"setOrientation(QtCore.Qt.Orientation.{orient})"],
                    children=_items(a, b))


@nd("Собрать виджеты в список", inputs=[("w1", "widget", None), ("w2", "widget", None), ("w3", "widget", None), ("w4", "widget", None), ("w5", "widget", None), ("w6", "widget", None), ("w7", "widget", None), ("w8", "widget", None), ("w9", "widget", None), ("w10", "widget", None), ("w11", "widget", None), ("w12", "widget", None), ("w13", "widget", None), ("w14", "widget", None), ("w15", "widget", None), ("w16", "widget", None), ("w17", "widget", None), ("w18", "widget", None), ("w19", "widget", None), ("w20", "widget", None), ("w21", "widget", None), ("w22", "widget", None), ("w23", "widget", None), ("w24", "widget", None), ("w25", "widget", None), ("w26", "widget", None), ("w27", "widget", None), ("w28", "widget", None), ("w29", "widget", None), ("w30", "widget", None), ("w31", "widget", None), ("w32", "widget", None), ("w33", "widget", None), ("w34", "widget", None), ("w35", "widget", None), ("w36", "widget", None), ("w37", "widget", None), ("w38", "widget", None), ("w39", "widget", None), ("w40", "widget", None), ("w41", "widget", None), ("w42", "widget", None), ("w43", "widget", None), ("w44", "widget", None), ("w45", "widget", None), ("w46", "widget", None), ("w47", "widget", None), ("w48", "widget", None), ("w49", "widget", None), ("w50", "widget", None), ("w51", "widget", None), ("w52", "widget", None), ("w53", "widget", None), ("w54", "widget", None), ("w55", "widget", None), ("w56", "widget", None), ("w57", "widget", None), ("w58", "widget", None), ("w59", "widget", None), ("w60", "widget", None)], outputs=[("items", "list")], tags=["collect", "designer"])
def collect(w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16, w17, w18, w19, w20, w21, w22, w23, w24, w25, w26, w27, w28, w29, w30, w31, w32, w33, w34, w35, w36, w37, w38, w39, w40, w41, w42, w43, w44, w45, w46, w47, w48, w49, w50, w51, w52, w53, w54, w55, w56, w57, w58, w59, w60):
    """Собирает до 60 виджетов в один список — нужно для больших .ui из Qt Designer."""
    out=[]
    for v in (w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16, w17, w18, w19, w20, w21, w22, w23, w24, w25, w26, w27, w28, w29, w30, w31, w32, w33, w34, w35, w36, w37, w38, w39, w40, w41, w42, w43, w44, w45, w46, w47, w48, w49, w50, w51, w52, w53, w54, w55, w56, w57, w58, w59, w60):
        if isinstance(v, dict): out.append(v)
        elif isinstance(v, (list, tuple)): out.extend(x for x in v if isinstance(x, dict))
    return out
