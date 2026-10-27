# Профилирование и измерение производительности

Все демо-скрипты лежат в `profiling/` и запускаются **из корня проекта**.
Установка инструментов: `pip install -r requirements-profiling.txt`

## 1. Скорость и время выполнения

### timeit
Встроенный модуль для точечного замера: запускает код много раз и снижает влияние погрешностей ОС. Подходит для сравнения небольших функций.
```bash
python profiling/01_timeit_demo.py
python -m timeit -s "from polygon_tool.geometry import area; p=[(0,0),(4,0),(4,4),(0,4)]" "area(p)"
```

### cProfile
Встроенный профилировщик: какие функции вызывались, сколько раз (`ncalls`), чистое время (`tottime`) и суммарное (`cumtime`).
```bash
python profiling/02_cprofile_demo.py
python -m cProfile -s cumtime -m polygon_tool calc -i examples/square.txt
snakeviz profiling/cprofile.prof      # визуализация в браузере
```

### line_profiler
Показывает время каждой строки функции. cProfile говорит, *какая функция* медленная, line_profiler — *какая строка*.
```bash
python profiling/03_line_profiler_demo.py
```
Столбцы: `Hits` (сколько раз выполнена), `Time`, `Per Hit`, `% Time`.

## 2. Использование памяти

### tracemalloc
Встроенный модуль: снимки памяти в разные моменты и их сравнение, чтобы находить утечки.
```bash
python profiling/04_tracemalloc_demo.py
```

### memory_profiler
Построчный анализ памяти: декоратор `@profile`, в таблице видно `Mem usage` и `Increment` по каждой строке (в МиБ).
```bash
python -m memory_profiler profiling/05_memory_profiler_demo.py
```

## 3. Комплексный мониторинг (APM)

### yappi
Профилировщик для многопоточных и asyncio-приложений (cProfile с потоками работает плохо). Умеет `cpu`- и `wall`-часы, статистику по потокам.
```bash
python profiling/06_yappi_demo.py
```

### py-spy
Внешний профилировщик на Rust: не требует менять код и может подключаться к уже запущенному процессу.
```bash
py-spy record -o profiling/flame.svg -- python profiling/07_workload.py   # Flame Graph
py-spy top --pid <PID>                                                    # живой top
py-spy dump --pid <PID>                                                   # где процесс «завис» сейчас
```
На Linux/macOS для подключения к чужому процессу может понадобиться `sudo`.

### Scalene
Всё в одном: CPU (Python vs нативный код), память и GPU, отчёт в виде веб-страницы.
```bash
scalene profiling/07_workload.py
scalene --html --outfile profiling/scalene.html profiling/07_workload.py
```
(у новых версий синтаксис запуска мог измениться — проверь `scalene --help`)

## Сводная таблица
| Инструмент | Что измеряет | Меняет код | Когда использовать |
|---|---|---|---|
| timeit | время небольшого фрагмента | нет | сравнить два варианта функции |
| cProfile | время по функциям | нет | найти медленную функцию |
| line_profiler | время по строкам | нет (через API) / `@profile` | найти медленную строку |
| tracemalloc | выделения памяти, снимки | нет | искать утечки |
| memory_profiler | память по строкам | `@profile` | найти прожорливую строку |
| yappi | время, потоки, asyncio | нет | многопоточные приложения |
| py-spy | где «висит» процесс | нет | работающий процесс, Flame Graph |
| Scalene | CPU + память + GPU | нет | общая картина в одном отчёте |

## Результаты для polygon-tool
Вставь сюда реальные выводы своих запусков и короткий вывод (какая функция/строка самая тяжёлая; по ожиданию — проверка самопересечений в `validate_polygon`, у неё сложность O(n²)).
