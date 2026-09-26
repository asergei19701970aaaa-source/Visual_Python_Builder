"""Графика: фигуры и холст рисования для собираемого приложения."""
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, lst, num, txt

nd = library("Shape", "16. Графика", color="#8f3f5f")


def _style(fill, stroke, width, opacity=1.0):
    return {"fill": txt(fill) or "", "stroke": txt(stroke) or "",
            "width": max(0, int(num(width, 1))),
            "opacity": max(0.0, min(1.0, float(num(opacity, 1.0))))}


@nd("Прямоугольник",
    inputs=[("x", "number", 20), ("y", "number", 20), ("width", "number", 120),
            ("height", "number", 80), ("fill", "color", "#3d7eff"),
            ("stroke", "color", "#1f232b"), ("line_width", "number", 2),
            ("radius", "number", 0), ("opacity", "number", 1.0)],
    outputs=[("shape", "shape")], tags=["rect", "прямоугольник"])
def rect(x, y, width, height, fill, stroke, line_width, radius, opacity):
    """Прямоугольник (можно со скруглёнными углами)."""
    return u.shape("rect", x=num(x), y=num(y), w=num(width, 120),
                   h=num(height, 80), radius=num(radius),
                   style=_style(fill, stroke, line_width, opacity))


@nd("Эллипс / круг",
    inputs=[("x", "number", 40), ("y", "number", 40), ("width", "number", 100),
            ("height", "number", 100), ("fill", "color", "#ffc14d"),
            ("stroke", "color", "#1f232b"), ("line_width", "number", 2),
            ("opacity", "number", 1.0)],
    outputs=[("shape", "shape")], tags=["ellipse", "круг"])
def ellipse(x, y, width, height, fill, stroke, line_width, opacity):
    """Эллипс или круг."""
    return u.shape("ellipse", x=num(x), y=num(y), w=num(width, 100),
                   h=num(height, 100), style=_style(fill, stroke, line_width, opacity))


@nd("Линия",
    inputs=[("x1", "number", 10), ("y1", "number", 10), ("x2", "number", 200),
            ("y2", "number", 120), ("stroke", "color", "#e6e9ef"),
            ("line_width", "number", 2)],
    outputs=[("shape", "shape")], tags=["line"])
def line(x1, y1, x2, y2, stroke, line_width):
    """Отрезок прямой."""
    return u.shape("line", x1=num(x1), y1=num(y1), x2=num(x2, 200),
                   y2=num(y2, 120), style=_style("", stroke, line_width))


@nd("Текст на холсте",
    inputs=[("text", "text", "Привет"), ("x", "number", 20),
            ("y", "number", 40), ("size", "number", 16),
            ("fill", "color", "#e6e9ef"), ("bold", "bool", False)],
    outputs=[("shape", "shape")], tags=["text"])
def text_shape(text, x, y, size, fill, bold):
    """Надпись, нарисованная на холсте."""
    return u.shape("text", text=txt(text), x=num(x), y=num(y, 40),
                   size=int(num(size, 16)), bold=flag(bold),
                   style=_style(fill, "", 0))


DEFAULT_POLYGON = "10,10 120,40 60,140"


def parse_points(raw, ox=0.0, oy=0.0):
    """Точки многоугольника из любого разумного вида записи.

    Понимает: '10,10 120,40', '10 10 120 40', '10, 10, 120, 40',
    '10;10 120;40', [[x, y], ...], [x, y, x, y, ...].
    Непарный остаток отбрасывается, ошибки не выбрасываются.
    """
    flat = []
    if isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                flat += [item[0], item[1]]
            else:
                flat.append(item)
    else:
        text = txt(raw).replace(";", " ").replace(",", " ")
        flat = text.split()
    numbers = []
    for value in flat:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            continue
    pts = [[numbers[i] + ox, numbers[i + 1] + oy]
           for i in range(0, len(numbers) - 1, 2)]
    return pts


@nd("Многоугольник",
    inputs=[{"name": "points", "type": "text", "default": DEFAULT_POLYGON,
             "hint": "Пары x,y через пробел"},
            ("fill", "color", "#c792ea"), ("stroke", "color", "#1f232b"),
            ("line_width", "number", 2), ("opacity", "number", 1.0),
            ("offset_x", "number", 0), ("offset_y", "number", 0),
            ("scale", "number", 1.0)],
    outputs=[("shape", "shape")], tags=["polygon"])
def polygon(points, fill, stroke, line_width, opacity, offset_x, offset_y,
            scale=1.0):
    """Замкнутая фигура по точкам.

    offset_x/offset_y сдвигают фигуру, scale меняет размер от центра.
    Если точек меньше трёх, подставляется треугольник по умолчанию,
    чтобы фигура не исчезала с экрана при редактировании.
    """
    pts = parse_points(points)
    if len(pts) < 3:
        pts = parse_points(DEFAULT_POLYGON)
    factor = float(num(scale, 1.0) or 1.0)
    if factor <= 0:
        factor = 1.0
    if factor != 1.0:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        pts = [[cx + (p[0] - cx) * factor, cy + (p[1] - cy) * factor]
               for p in pts]
    ox, oy = num(offset_x, 0), num(offset_y, 0)
    pts = [[p[0] + ox, p[1] + oy] for p in pts]
    return u.shape("polygon", points=pts,
                   style=_style(fill, stroke, line_width, opacity))


@nd("Сетка на фоне",
    inputs=[("step", "number", 25), ("stroke", "color", "#2b303a")],
    outputs=[("shape", "shape")], tags=["grid"])
def grid(step, stroke):
    """Фоновая сетка холста."""
    return u.shape("grid", step=max(2, int(num(step, 25))),
                   style=_style("", stroke, 1))


@nd("Собрать фигуры",
    inputs=[("a", "shape", None), ("b", "shape", None), ("c", "shape", None),
            ("d", "shape", None), ("e", "shape", None), ("f", "shape", None),
            ("extra", "list", None)],
    outputs=[("shapes", "list")], tags=["pack"])
def collect_shapes(a, b, c, d, e, f, extra):
    """Собирает фигуры в список для холста."""
    out = []
    for v in (a, b, c, d, e, f, *lst(extra)):
        if isinstance(v, dict):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            out.extend(x for x in v if isinstance(x, dict))
    return out


@nd("Холст рисования (виджет)",
    inputs=[("shapes", "list", None), ("width", "number", 400),
            ("height", "number", 300), ("background", "color", "#1c1f26"),
            ("name", "text", "")],
    outputs=[("widget", "widget")], tags=["canvas", "paint"])
def canvas(shapes, width, height, background, name):
    """Виджет PaintCanvas: рисует переданные фигуры через QPainter."""
    items = [s for s in lst(shapes) if isinstance(s, dict)]
    w = u.widget("PaintCanvas", name=name or "canvas", helper="PaintCanvas",
                 module="")
    w["extra"]["shapes"] = items
    w["extra"]["canvas"] = {"background": txt(background) or "#1c1f26"}
    w["calls"].append(f"setMinimumSize({int(num(width, 400))}, "
                      f"{int(num(height, 300))})")
    return w