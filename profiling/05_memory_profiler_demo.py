"""memory_profiler: потребление памяти построчно.

Запуск: python -m memory_profiler profiling/05_memory_profiler_demo.py
"""
from common import make_polygon
from memory_profiler import profile
from polygon_tool.geometry import analyze


@profile
def build_and_analyze():
    polygons = [make_polygon(n) for n in range(50, 300)]  # много точек в памяти
    results = [analyze(p) for p in polygons]
    del polygons  # видно, как память освобождается
    return results


if __name__ == "__main__":
    build_and_analyze()
