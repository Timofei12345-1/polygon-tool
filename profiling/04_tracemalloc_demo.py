"""tracemalloc: снимки памяти до и после, сравнение (поиск утечек)."""
import tracemalloc

from common import make_polygon
from polygon_tool.geometry import analyze

tracemalloc.start()
before = tracemalloc.take_snapshot()

# имитация «утечки»: результаты копятся в списке и не освобождаются
leak = []
for n in range(10, 400):
    leak.append((make_polygon(n), analyze(make_polygon(n))))

after = tracemalloc.take_snapshot()

print("Топ-5 строк, где память выросла сильнее всего:")
for stat in after.compare_to(before, "lineno")[:5]:
    print(stat)

current, peak = tracemalloc.get_traced_memory()
print(f"\nТекущая: {current / 1024:.1f} КиБ, пик: {peak / 1024:.1f} КиБ")
