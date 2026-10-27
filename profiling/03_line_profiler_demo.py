"""line_profiler: время выполнения каждой строки функции validate_polygon."""
from line_profiler import LineProfiler

from common import make_polygon
from polygon_tool.geometry import validate_polygon

POINTS = make_polygon(150)

lp = LineProfiler()
profiled = lp(validate_polygon)  # оборачиваем функцию, исходный код не трогаем
for _ in range(5):
    profiled(POINTS)
lp.print_stats()
