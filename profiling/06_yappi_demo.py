"""yappi: профилирование многопоточной программы (cProfile с потоками плох)."""
import threading

import yappi

from common import make_polygon
from polygon_tool.geometry import analyze


def worker(n):
    pts = make_polygon(n)
    for _ in range(10):
        analyze(pts)


yappi.set_clock_type("cpu")  # "wall" — если важно и время ожидания
yappi.start()

threads = [threading.Thread(target=worker, args=(n,), name=f"worker-{n}")
           for n in (60, 100, 140, 180)]
for t in threads:
    t.start()
for t in threads:
    t.join()

yappi.stop()
print("=== Функции (топ-10 по общему времени) ===")
yappi.get_func_stats().sort("ttot", "desc").print_all(columns={
    0: ("name", 50), 1: ("ncall", 8), 2: ("tsub", 8), 3: ("ttot", 8)})
print("\n=== Потоки ===")
yappi.get_thread_stats().print_all()
