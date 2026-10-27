"""cProfile: какие функции вызываются, сколько раз и сколько времени занимают."""
import cProfile
import pstats

from common import make_polygon
from polygon_tool.geometry import analyze

POINTS = make_polygon(150)


def workload():
    for _ in range(20):
        analyze(POINTS)


profiler = cProfile.Profile()
profiler.runcall(workload)

stats = pstats.Stats(profiler)
stats.sort_stats("cumulative").print_stats(10)  # сортировка по суммарному времени
stats.sort_stats("tottime").print_stats(10)     # сортировка по чистому времени
stats.dump_stats("profiling/cprofile.prof")     # можно открыть в snakeviz
