# 📐 polygon-tool

🇷🇺 Русский · [🇬🇧 English](README.en.md)

## 📋 Описание проекта

Консольная программа на Python для расчёта **периметра и площади сложного многоугольника** по заданным пользователем декартовым координатам вершин, с вводом и выводом данных через консоль или файл. В состав проекта входят подсистема **резервного копирования и восстановления** картографических точек, пользовательская документация и тест-кейсы.

## 🎯 Задание

1. Создать консольную программу на Python для нахождения периметра и площади сложного многоугольника по декартовым координатам его вершин (ввод/вывод через файл и через консоль).
2. Разработать алгоритм резервного копирования и восстановления картографических точек координат.
3. Разработать пользовательскую документацию (ТЗ, README на русском и английском языках, регламент технического обслуживания) и зафиксировать её вместе с проектом в GitHub.
4. Составить тест-кейсы и проверить работоспособность ключевых модулей на соответствие ТЗ.
5. Настроить автоформатирование кода (black) и провести профилирование производительности и памяти.

## 🛠️ Технологии

- **Python 3.10+** — основной язык программирования
- **Стандартная библиотека** — `argparse`, `json`, `hashlib`, `pathlib`, `math`, `tempfile` (внешние зависимости не нужны)
- **unittest / pytest** — автоматические тесты
- **black** — автоматическое форматирование кода
- **timeit, cProfile, line_profiler, tracemalloc, memory_profiler, yappi, py-spy, Scalene** — профилирование
- **Git и GitHub Actions** — контроль версий и автоматический прогон тестов

## 📦 Установка и запуск

### 1. Клонирование репозитория

```
git clone https://github.com/Timofei12345-1/polygon-tool.git
cd polygon-tool
```

### 2. Установка зависимостей

Для работы программы зависимости не требуются. Для разработки (необязательно):

```
pip install -r requirements.txt
```

### 3. Запуск основной программы

```
python -m polygon_tool calc -i examples/square.txt
```

Вывод:

```
Количество вершин: 4
Периметр: 16
Площадь: 16
```

> Если Python не находит модуль, выполните запуск из корня проекта с `PYTHONPATH=src` (Windows PowerShell: `$env:PYTHONPATH="src"`) или установите проект командой `pip install -e .` — тогда доступна короткая команда `polygon-tool`.

### 4. Запуск тестов

```
python -m unittest discover -s tests -v
# или
python -m pytest -v
```

## 📁 Структура проекта

```
polygon-tool/
├── src/polygon_tool/
│   ├── geometry.py        # Периметр, площадь, проверка многоугольника
│   ├── io_handlers.py     # Ввод/вывод: консоль, TXT, CSV, JSON
│   ├── backup.py          # Резервное копирование и восстановление точек
│   └── cli.py             # Командная строка
├── tests/                 # Автотесты (test_geometry, test_io, test_backup, test_cli)
├── profiling/             # Скрипты профилирования (timeit, cProfile, yappi и др.)
├── docs/
│   ├── TZ.md              # Техническое задание
│   ├── maintenance.md     # Регламент технического обслуживания
│   ├── test-cases.md      # Тест-кейсы и результаты проверки
│   ├── GIT.md             # Правила ведения репозитория
│   ├── code-style.md      # Форматирование кода (black)
│   └── profiling.md       # Описание инструментов профилирования и результаты
├── examples/              # Примеры входных файлов
├── README.md              # Документация (русский)
├── README.en.md           # Документация (английский)
├── requirements.txt           # Зависимости для разработки
├── requirements-profiling.txt # Зависимости для профилирования и black
└── .gitignore             # Git ignore файл
```

## 🎮 Использование программы

### Расчёт периметра и площади

```
# Ввод из консоли: «x y» по строке, пустая строка завершает ввод
python -m polygon_tool calc

# Ввод из файла (TXT, CSV или JSON определяются по расширению)
python -m polygon_tool calc -i examples/l_shape.csv

# Результат в файл (.json — JSON, иначе — текст)
python -m polygon_tool calc -i examples/square.txt -o result.json

# Сохранить точки в хранилище data/points.json
python -m polygon_tool calc -i examples/square.txt --save
```

Вершины перечисляются по порядку обхода (по или против часовой стрелки); первую точку в конце повторять не нужно.

### Форматы входного файла

```
# TXT / CSV — одна вершина в строке (разделитель: пробел, запятая, «;» или табуляция)
x,y
0,0
4,0
4,4
0,4
```

```
{"points": [[0, 0], [3, 0], [0, 4]]}
```

JSON также может быть списком пар `[[0,0],[3,0],[0,4]]` или списком объектов `[{"x":0,"y":0}, ...]`. Десятичный разделитель — точка.

### Резервное копирование

```
python -m polygon_tool backup          # создать копию хранилища в backups/
python -m polygon_tool list-backups    # список копий с проверкой целостности
python -m polygon_tool verify          # проверить все копии
python -m polygon_tool restore         # восстановить из самой свежей копии
python -m polygon_tool restore --file backups/points_20261021_020000_123456.json
```

Общие параметры: `--data-file` (по умолчанию `data/points.json`), `--backup-dir` (`backups`), `--keep` (число хранимых копий, по умолчанию 10).

### Использование как Python-модуля

```python
from polygon_tool.geometry import analyze, PolygonError
from polygon_tool.io_handlers import read_points_file
from polygon_tool.backup import BackupManager

# Расчёт
print(analyze([(0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4)]))
# {'vertices': 6, 'perimeter': 16.0, 'area': 12.0}

# Чтение из файла
points = read_points_file("examples/triangle.json")

# Проверка некорректного многоугольника
try:
    analyze([(0, 0), (4, 4), (4, 0), (0, 4)])
except PolygonError as err:
    print(err)  # Многоугольник самопересекается: стороны 1 и 3 ...

# Резервное копирование
manager = BackupManager("data/points.json", "backups", keep=5)
manager.save_points(points)
backup = manager.create_backup()
manager.restore(backup)
```

## 📊 Основные функции

### Модуль `geometry`

- `analyze(points)` — проверка и расчёт: число вершин, периметр, площадь
- `perimeter(points)` — периметр (с замыкающей стороной)
- `area(points)` / `signed_area(points)` — площадь по формуле Гаусса (шнуровки)
- `validate_polygon(points)` — проверка: ≥ 3 вершин, конечные числа, нет совпадающих соседних вершин, нет вырождения и самопересечений

### Модуль `io_handlers`

- `read_points_file(path)` — чтение вершин из TXT / CSV / JSON
- `read_points_console()` — интерактивный ввод из консоли
- `parse_points_text(text)` — разбор текста с вершинами
- `write_result_file(path, result)` — запись результата в TXT / JSON

### Класс `BackupManager`

- `save_points(points)` / `load_points()` — работа с хранилищем точек
- `create_backup()` — создание копии с манифестом (SHA-256) и ротацией
- `list_backups()` — список копий
- `verify_backup(path)` — проверка целостности копии
- `restore(path=None)` — восстановление (по умолчанию из самой свежей копии)

## 🔄 Алгоритм резервного копирования

1. Хранилище проверяется и копируется в `backups/points_<дата>_<время>.json`; повреждённые данные не копируются.
2. Рядом записывается манифест: SHA-256, число точек, дата создания.
3. Записи атомарные (временный файл → замена), сбой не оставляет наполовину записанных файлов.
4. Ротация: хранятся только последние N копий.
5. Восстановление: проверка копии → сохранение текущего состояния отдельной копией → атомарная замена. Повреждённая копия отклоняется, хранилище остаётся нетронутым.

## 🧪 Тестирование

Проект включает **51 автоматический тест**:

**Unit-тесты:**

- Периметр и площадь: квадрат, треугольник, невыпуклые фигуры, направление обхода
- Некорректные многоугольники: меньше 3 вершин, одна прямая, самопересечения, дубликаты
- Разбор TXT / CSV / JSON, ошибки ввода с номером строки
- Резервное копирование: восстановление, повреждённая копия, ротация, манифест

**Интеграционные тесты:**

- Полные сценарии командной строки, коды возврата
- Цикл «сохранить → копия → изменить → восстановить»

Таблица тест-кейсов и результаты проверки — в [docs/test-cases.md](docs/test-cases.md).

## 🎨 Стиль кода и профилирование

Все команды выполняются **из корня проекта**. Сначала установите инструменты:

```
pip install -r requirements-profiling.txt
```

### Форматирование кода (black)

```
black .                  # отформатировать весь проект
black --check --diff .   # только проверить, ничего не менять (как в CI)
```

Подробнее — в [docs/code-style.md](docs/code-style.md).

### Профилирование

| Что измеряем | Инструмент | Команда |
|---|---|---|
| Скорость фрагмента | timeit | `python profiling/01_timeit_demo.py` |
| Время по функциям | cProfile | `python profiling/02_cprofile_demo.py` |
| Время по строкам | line_profiler | `python profiling/03_line_profiler_demo.py` |
| Снимки памяти | tracemalloc | `python profiling/04_tracemalloc_demo.py` |
| Память по строкам | memory_profiler | `python -m memory_profiler profiling/05_memory_profiler_demo.py` |
| Многопоточность | yappi | `python profiling/06_yappi_demo.py` |
| Flame Graph | py-spy | `py-spy record -o profiling/flame.svg -- python profiling/07_workload.py` |
| CPU + память + GPU | Scalene | `scalene profiling/07_workload.py` |

> Скрипты сами находят модуль `polygon_tool` в `src/`, поэтому `pip install -e .` и `PYTHONPATH` не нужны. Описание инструментов и результаты замеров — в [docs/profiling.md](docs/profiling.md).

## 💡 Примеры использования

### Пример 1: Квадрат из файла

```
python -m polygon_tool calc -i examples/square.txt
# Периметр: 16, Площадь: 16
```

### Пример 2: Невыпуклый (Г-образный) многоугольник

```
python -m polygon_tool calc -i examples/l_shape.csv
# Периметр: 16, Площадь: 12
```

### Пример 3: Некорректный контур

```
python -m polygon_tool calc -i examples/bowtie_invalid.txt
# Ошибка: Многоугольник самопересекается: стороны 1 и 3 пересекаются или касаются.
# Код возврата: 1
```

### Пример 4: Резервная копия и восстановление

```
python -m polygon_tool calc -i examples/square.txt --save
python -m polygon_tool backup
python -m polygon_tool calc -i examples/triangle.json --save   # данные изменились
python -m polygon_tool restore                                 # вернули квадрат
```

## ⚠️ Коды возврата

| Код | Значение                                                                      |
|-----|-------------------------------------------------------------------------------|
| 0   | Успешно                                                                       |
| 1   | Ошибка данных (некорректный ввод, файл не найден, недопустимый многоугольник) |
| 2   | Неверные аргументы командной строки                                           |
| 3   | Ошибка хранилища или резервной копии                                          |

## 📚 Документация

- [Техническое задание](docs/TZ.md)
- [Регламент технического обслуживания](docs/maintenance.md)
- [Тест-кейсы и результаты](docs/test-cases.md)
- [Работа с Git](docs/GIT.md)
- [Стиль кода (black)](docs/code-style.md)
- [Профилирование](docs/profiling.md)
