"""Геометрические вычисления для многоугольников (ТЗ: ФТ-3, ФТ-4, ФТ-5)."""

from __future__ import annotations

import math
from typing import Sequence

Point = tuple[float, float]


class PolygonError(ValueError):
    """Многоугольник некорректен (вырожден, самопересекается и т. п.)."""


def _translate(points: Sequence[Point]) -> list[Point]:
    """Сдвигает вершины так, чтобы первая оказалась в (0, 0).

    Это уменьшает потерю точности при больших абсолютных координатах.
    """
    x0, y0 = points[0]
    return [(x - x0, y - y0) for x, y in points]


def _cross(o: Point, a: Point, b: Point) -> float:
    """Векторное произведение (a - o) x (b - o)."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def signed_area(points: Sequence[Point]) -> float:
    """Площадь со знаком по формуле Гаусса (шнуровки).

    Положительна при обходе против часовой стрелки.
    """
    pts = _translate(points)
    n = len(pts)
    terms = []
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        terms.append(x1 * y2 - x2 * y1)
    return math.fsum(terms) / 2.0


def area(points: Sequence[Point]) -> float:
    """Площадь многоугольника (всегда >= 0)."""
    return abs(signed_area(points))


def perimeter(points: Sequence[Point]) -> float:
    """Периметр: сумма длин сторон, включая замыкающую."""
    n = len(points)
    return math.fsum(
        math.hypot(points[(i + 1) % n][0] - points[i][0], points[(i + 1) % n][1] - points[i][1])
        for i in range(n)
    )


def _on_segment(a: Point, b: Point, c: Point) -> bool:
    """Лежит ли c в габаритном прямоугольнике отрезка ab (при условии коллинеарности)."""
    return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


def _segments_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    """Пересекаются или касаются ли отрезки p1p2 и p3p4."""
    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    if d1 == 0 and _on_segment(p3, p4, p1):
        return True
    if d2 == 0 and _on_segment(p3, p4, p2):
        return True
    if d3 == 0 and _on_segment(p1, p2, p3):
        return True
    if d4 == 0 and _on_segment(p1, p2, p4):
        return True
    return False


def _all_collinear(pts: Sequence[Point]) -> bool:
    """Лежат ли все точки на одной прямой (pts[0] уже сдвинута в начало координат)."""
    origin = pts[0]
    direction = next(p for p in pts if p != origin)  # соседние не совпадают, значит найдётся
    extent = max(max(abs(x), abs(y)) for x, y in pts)
    tolerance = 1e-12 * max(1.0, extent * extent)
    return all(abs(_cross(origin, direction, p)) <= tolerance for p in pts)


def validate_polygon(points: Sequence[Point]) -> None:
    """Проверяет многоугольник, при нарушении бросает PolygonError (ФТ-5).

    Правила:
      1. не менее 3 вершин;
      2. координаты — конечные числа;
      3. соседние вершины (включая последнюю и первую) не совпадают;
      4. многоугольник не вырожден (не все вершины на одной прямой);
      5. стороны не пересекаются и не касаются (кроме соседних в общей вершине).
    """
    n = len(points)
    if n < 3:
        raise PolygonError(f"Нужно не менее 3 вершин, получено: {n}.")

    for i, (x, y) in enumerate(points, start=1):
        if not (math.isfinite(x) and math.isfinite(y)):
            raise PolygonError(f"Вершина {i}: координаты должны быть конечными числами.")

    for i in range(n):
        if points[i] == points[(i + 1) % n]:
            raise PolygonError(
                f"Совпадают соседние вершины {i + 1} и {(i + 1) % n + 1}. "
                "Не повторяйте первую точку в конце списка."
            )

    pts = _translate(points)
    if _all_collinear(pts):
        raise PolygonError("Многоугольник вырожден: все вершины лежат на одной прямой.")

    # Соседние стороны не должны «складываться» сами на себя.
    for i in range(n):
        a, b, c = pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        if _cross(b, a, c) == 0 and (a[0] - b[0]) * (c[0] - b[0]) + (a[1] - b[1]) * (c[1] - b[1]) > 0:
            raise PolygonError(f"Стороны при вершине {(i + 1) % n + 1} накладываются друг на друга.")

    # Несоседние стороны не должны пересекаться.
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # соседние стороны (замыкающая и первая)
            if _segments_intersect(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                raise PolygonError(
                    f"Многоугольник самопересекается: стороны {i + 1} и {j + 1} пересекаются или касаются."
                )


def analyze(points: Sequence[Point]) -> dict:
    """Валидирует многоугольник и возвращает число вершин, периметр и площадь."""
    validate_polygon(points)
    return {
        "vertices": len(points),
        "perimeter": perimeter(points),
        "area": area(points),
    }
