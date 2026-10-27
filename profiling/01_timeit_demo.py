"""timeit: точечный замер скорости функций polygon_tool."""
import timeit

from common import make_polygon
from polygon_tool.geometry import analyze, area, perimeter

POINTS = make_polygon(60)
NUMBER = 500   # сколько раз выполнять за один замер
REPEAT = 5     # сколько замеров делать

for name, func in [("perimeter", perimeter), ("area", area), ("analyze", analyze)]:
    times = timeit.repeat(lambda f=func: f(POINTS), number=NUMBER, repeat=REPEAT)
    best = min(times) / NUMBER  # берём лучший замер: он наименее зашумлён ОС
    print(f"{name:<10} {best * 1e6:10.2f} мкс на вызов")
