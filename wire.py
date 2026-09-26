"""Проверенная геометрия нитей, перенесённая из NodeFlow 18.0."""

from __future__ import annotations

from PySide6.QtCore import QLineF, QPointF
from PySide6.QtGui import QPainterPath


def build_curve_path(start: QPointF, end: QPointF, vertical=False):
    path = QPainterPath(start)
    if vertical:
        distance = max(40.0, abs(end.y() - start.y()) * 0.5)
        path.cubicTo(
            QPointF(start.x(), start.y() + distance),
            QPointF(end.x(), end.y() - distance),
            end,
        )
    else:
        distance = max(40.0, abs(end.x() - start.x()) * 0.5)
        path.cubicTo(
            QPointF(start.x() + distance, start.y()),
            QPointF(end.x() - distance, end.y()),
            end,
        )
    return path


def _same(first, second):
    return (
        abs(first.x() - second.x()) < 0.01
        and abs(first.y() - second.y()) < 0.01
    )


def _intersection(a, b, c, d):
    ab_vertical = abs(a.x() - b.x()) < 0.01
    cd_vertical = abs(c.x() - d.x()) < 0.01
    if ab_vertical == cd_vertical:
        return None
    if not ab_vertical:
        a, b, c, d = c, d, a, b
    low_y, high_y = sorted((a.y(), b.y()))
    low_x, high_x = sorted((c.x(), d.x()))
    if (
        low_y - 0.01 <= c.y() <= high_y + 0.01
        and low_x - 0.01 <= a.x() <= high_x + 0.01
    ):
        return QPointF(a.x(), c.y())
    return None


def normalize_orthogonal_points(
    points, vertical=False, simplify=True
):
    """Убирает диагонали, повторы, лишние углы и самопетли."""
    source = [QPointF(point) for point in points]
    if len(source) < 2:
        return source
    result = [source[0]]
    previous_vertical = None
    for point in source[1:]:
        first = result[-1]
        diagonal = (
            abs(first.x() - point.x()) > 0.01
            and abs(first.y() - point.y()) > 0.01
        )
        if diagonal:
            wanted_vertical = (
                vertical
                if previous_vertical is None
                else not previous_vertical
            )
            corner = (
                QPointF(first.x(), point.y())
                if wanted_vertical
                else QPointF(point.x(), first.y())
            )
            if not _same(first, corner):
                result.append(corner)
                previous_vertical = wanted_vertical
                first = corner
        if not _same(first, point):
            result.append(point)
            previous_vertical = abs(first.x() - point.x()) < 0.01

    protected = set()
    if len(result) >= 4:
        protected = {id(result[1]), id(result[-2])}
    if not simplify:
        return result

    changed = True
    while changed and len(result) > 2:
        changed = False
        compact = [result[0]]
        for point in result[1:]:
            if not _same(compact[-1], point):
                compact.append(point)
            elif id(point) in protected:
                if id(compact[-1]) not in protected:
                    compact[-1] = point
            else:
                changed = True
        result = compact
        index = 1
        while index < len(result) - 1:
            a, b, c = result[index - 1:index + 2]
            collinear = (
                abs(a.x() - b.x()) < 0.01
                and abs(b.x() - c.x()) < 0.01
            ) or (
                abs(a.y() - b.y()) < 0.01
                and abs(b.y() - c.y()) < 0.01
            )
            if collinear and id(b) not in protected:
                del result[index]
                changed = True
            else:
                index += 1
        loop_removed = False
        for first_index in range(len(result) - 3):
            for second_index in range(
                first_index + 2, len(result) - 1
            ):
                cross = _intersection(
                    result[first_index],
                    result[first_index + 1],
                    result[second_index],
                    result[second_index + 1],
                )
                if cross is None:
                    continue
                removed = result[
                    first_index + 1:second_index + 1
                ]
                if any(id(point) in protected for point in removed):
                    continue
                result = (
                    result[:first_index + 1]
                    + [cross]
                    + result[second_index + 1:]
                )
                changed = True
                loop_removed = True
                break
            if loop_removed:
                break
    return result


def build_orthogonal_points(
    start: QPointF, end: QPointF, vertical=False, bends=None
):
    """Строит маршрут с защищёнными участками возле портов."""
    stub = 16.0
    if bends:
        route = [QPointF(float(p[0]), float(p[1])) for p in bends]
        if vertical:
            route[0] = QPointF(start.x(), start.y() + stub)
            route[-1] = QPointF(end.x(), end.y() - stub)
        else:
            route[0] = QPointF(start.x() + stub, start.y())
            route[-1] = QPointF(end.x() - stub, end.y())
        if len(route) >= 4:
            if vertical:
                if abs(route[1].x() - route[0].x()) > 0.01:
                    route[1].setY(route[0].y())
                if abs(route[-2].x() - route[-1].x()) > 0.01:
                    route[-2].setY(route[-1].y())
            else:
                if abs(route[1].y() - route[0].y()) > 0.01:
                    route[1].setX(route[0].x())
                if abs(route[-2].y() - route[-1].y()) > 0.01:
                    route[-2].setX(route[-1].x())
        elif len(route) == 3:
            first, middle, last = route
            route = (
                [
                    first,
                    QPointF(middle.x(), first.y()),
                    QPointF(middle.x(), last.y()),
                    last,
                ]
                if vertical
                else [
                    first,
                    QPointF(first.x(), middle.y()),
                    QPointF(last.x(), middle.y()),
                    last,
                ]
            )
        elif len(route) == 2:
            first, last = route
            if vertical:
                middle = (first.x() + last.x()) / 2
                route = [
                    first,
                    QPointF(middle, first.y()),
                    QPointF(middle, last.y()),
                    last,
                ]
            else:
                middle = (first.y() + last.y()) / 2
                route = [
                    first,
                    QPointF(first.x(), middle),
                    QPointF(last.x(), middle),
                    last,
                ]
        return normalize_orthogonal_points(
            [start] + route + [end], vertical=vertical
        )

    if vertical:
        source_out = QPointF(start.x(), start.y() + stub)
        target_out = QPointF(end.x(), end.y() - stub)
        if source_out.y() <= target_out.y():
            middle = (source_out.y() + target_out.y()) / 2
            points = [
                start,
                source_out,
                QPointF(source_out.x(), middle),
                QPointF(target_out.x(), middle),
                target_out,
                end,
            ]
        else:
            detour = max(start.x(), end.x()) + 40.0
            points = [
                start,
                source_out,
                QPointF(detour, source_out.y()),
                QPointF(detour, target_out.y()),
                target_out,
                end,
            ]
    else:
        source_out = QPointF(start.x() + stub, start.y())
        target_out = QPointF(end.x() - stub, end.y())
        if source_out.x() <= target_out.x():
            middle = (source_out.x() + target_out.x()) / 2
            points = [
                start,
                source_out,
                QPointF(middle, source_out.y()),
                QPointF(middle, target_out.y()),
                target_out,
                end,
            ]
        else:
            detour = max(start.y(), end.y()) + 40.0
            points = [
                start,
                source_out,
                QPointF(source_out.x(), detour),
                QPointF(target_out.x(), detour),
                target_out,
                end,
            ]
    return normalize_orthogonal_points(points, vertical=vertical)


def rounded_orthogonal_path(points):
    path = QPainterPath(points[0])
    radius = 5.5
    for index in range(1, len(points) - 1):
        previous, corner, following = (
            points[index - 1],
            points[index],
            points[index + 1],
        )
        incoming = QLineF(previous, corner)
        outgoing = QLineF(corner, following)
        before_distance = min(radius, incoming.length() / 2)
        after_distance = min(radius, outgoing.length() / 2)
        before = incoming.pointAt(
            1.0 - before_distance / max(0.001, incoming.length())
        )
        after = outgoing.pointAt(
            after_distance / max(0.001, outgoing.length())
        )
        path.lineTo(before)
        path.quadTo(corner, after)
    path.lineTo(points[-1])
    return path