"""Долгая нагрузка для py-spy и Scalene (запускаются снаружи, код не меняется).

py-spy:  py-spy record -o profiling/flame.svg -- python profiling/07_workload.py
Scalene: scalene profiling/07_workload.py
"""
import time

from common import make_polygon
from polygon_tool.geometry import analyze

if __name__ == "__main__":
    start = time.time()
    while time.time() - start < 15:  # ~15 секунд нагрузки
        for n in (80, 120, 160):
            analyze(make_polygon(n))
