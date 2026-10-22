# 📐 polygon-tool

[🇷🇺 Русский](README.md) · 🇬🇧 English

## 📋 Project description

A Python command-line tool that computes the **perimeter and area of a complex polygon** from user-supplied
Cartesian vertex coordinates, with input and output via console or file. The project also includes a
**backup and restore** subsystem for map coordinate points, user documentation and test cases.

## ✍️ Authors

| Role | Name |
|---|---|
| Developer | Timofei Korolev |
| Reviewer | Viktoriya Dmitrievna Shashkova |


## 🛠️ Technologies

- **Python 3.10+** — main language
- **Standard library** — `argparse`, `json`, `hashlib`, `pathlib`, `math`, `tempfile` (no external dependencies)
- **unittest / pytest** — automated tests
- **Git and GitHub Actions** — version control and automatic test runs

## 📦 Installation and launch

### 1. Clone the repository

```bash
git clone https://github.com/Timofei12345-1/polygon-tool.git
cd polygon-tool
```

### 2. Install dependencies

The program itself needs none. For development (optional):

```bash
pip install -r requirements.txt
```

### 3. Run the program

```bash
python -m polygon_tool calc -i examples/square.txt
```

Output (console messages are in Russian):

```
Количество вершин: 4     (vertices)
Периметр: 16             (perimeter)
Площадь: 16              (area)
```

> If Python cannot find the module, run from the project root with `PYTHONPATH=src`
> (Windows PowerShell: `$env:PYTHONPATH="src"`) or install the project with `pip install -e .`,
> which provides the short `polygon-tool` command.

### 4. Run the tests

```bash
python -m unittest discover -s tests -v
# or
python -m pytest -v
```

## 📁 Project structure

```
polygon-tool/
├── src/polygon_tool/
│   ├── geometry.py        # Perimeter, area, polygon validation
│   ├── io_handlers.py     # Input/output: console, TXT, CSV, JSON
│   ├── backup.py          # Backup and restore of points
│   └── cli.py             # Command line interface
├── tests/                 # Automated tests (test_geometry, test_io, test_backup, test_cli)
├── docs/
│   ├── TZ.md              # Technical specification (Russian)
│   ├── maintenance.md     # Maintenance regulations (Russian)
│   ├── test-cases.md      # Test cases and results (Russian)
│   └── GIT.md             # Repository workflow (Russian)
├── examples/              # Sample input files
├── README.md              # Documentation (Russian)
├── README.en.md           # Documentation (English)
├── requirements.txt       # Development dependencies
└── .gitignore             # Git ignore file
```

## 🎮 Usage

### Perimeter and area

```bash
# Console input: one "x y" pair per line, an empty line ends input
python -m polygon_tool calc

# From a file (TXT, CSV or JSON, detected by extension)
python -m polygon_tool calc -i examples/l_shape.csv

# Write the result to a file (.json → JSON, otherwise text)
python -m polygon_tool calc -i examples/square.txt -o result.json

# Also save the points to the store data/points.json
python -m polygon_tool calc -i examples/square.txt --save
```

List vertices in traversal order (clockwise or counter-clockwise); do not repeat the first point at the end.

### Input file formats

```text
# TXT / CSV — one vertex per line (separator: space, comma, ";" or tab)
x,y
0,0
4,0
4,4
0,4
```

```json
{"points": [[0, 0], [3, 0], [0, 4]]}
```

JSON may also be a list of pairs `[[0,0],[3,0],[0,4]]` or a list of objects `[{"x":0,"y":0}, ...]`.
The decimal separator is a dot.

### Backup and restore

```bash
python -m polygon_tool backup          # create a backup of the store in backups/
python -m polygon_tool list-backups    # list backups with integrity check
python -m polygon_tool verify          # verify all backups
python -m polygon_tool restore         # restore from the latest backup
python -m polygon_tool restore --file backups/points_20261021_020000_123456.json
```

Common options: `--data-file` (default `data/points.json`), `--backup-dir` (`backups`),
`--keep` (number of backups to keep, default 10).

### Using it as a Python module

```python
from polygon_tool.geometry import analyze, PolygonError
from polygon_tool.io_handlers import read_points_file
from polygon_tool.backup import BackupManager

# Calculation
print(analyze([(0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4)]))
# {'vertices': 6, 'perimeter': 16.0, 'area': 12.0}

# Read from a file
points = read_points_file("examples/triangle.json")

# Invalid polygon
try:
    analyze([(0, 0), (4, 4), (4, 0), (0, 4)])
except PolygonError as err:
    print(err)  # the polygon is self-intersecting (message in Russian)

# Backup
manager = BackupManager("data/points.json", "backups", keep=5)
manager.save_points(points)
backup = manager.create_backup()
manager.restore(backup)
```

## 📊 Main functions

### Module `geometry`

- `analyze(points)` — validate and compute: vertex count, perimeter, area
- `perimeter(points)` — perimeter (including the closing side)
- `area(points)` / `signed_area(points)` — area by the shoelace formula
- `validate_polygon(points)` — checks: ≥ 3 vertices, finite numbers, no identical adjacent vertices, no degeneracy or self-intersection

### Module `io_handlers`

- `read_points_file(path)` — read vertices from TXT / CSV / JSON
- `read_points_console()` — interactive console input
- `parse_points_text(text)` — parse text with vertices
- `write_result_file(path, result)` — write the result as TXT / JSON

### Class `BackupManager`

- `save_points(points)` / `load_points()` — work with the point store
- `create_backup()` — create a backup with a manifest (SHA-256) and rotation
- `list_backups()` — list backups
- `verify_backup(path)` — verify backup integrity
- `restore(path=None)` — restore (from the latest backup by default)

## 🔄 Backup algorithm

1. The store is validated and copied to `backups/points_<date>_<time>.json`; corrupted data is never backed up.
2. A manifest is written next to it: SHA-256, point count, creation time.
3. All writes are atomic (temporary file → replace), so a failure never leaves a half-written file.
4. Rotation: only the latest N backups are kept.
5. Restore: verify the backup → save the current state as another backup → atomic replace.
   A corrupted backup is rejected and the store stays untouched.

## 🧪 Testing

The project includes **51 automated tests**:

**Unit tests:**
- Perimeter and area: square, triangle, non-convex shapes, traversal direction
- Invalid polygons: fewer than 3 vertices, collinear points, self-intersections, duplicates
- TXT / CSV / JSON parsing, input errors with line numbers
- Backup: restore, corrupted backup, rotation, manifest

**Integration tests:**
- Full command-line scenarios, exit codes
- "save → backup → modify → restore" cycle

The test-case table and results are in [docs/test-cases.md](docs/test-cases.md) (Russian).

## 💡 Examples

### Example 1: Square from a file

```bash
python -m polygon_tool calc -i examples/square.txt
# Perimeter: 16, Area: 16
```

### Example 2: Non-convex (L-shaped) polygon

```bash
python -m polygon_tool calc -i examples/l_shape.csv
# Perimeter: 16, Area: 12
```

### Example 3: Invalid outline

```bash
python -m polygon_tool calc -i examples/bowtie_invalid.txt
# Error: the polygon is self-intersecting (sides 1 and 3 cross or touch).
# Exit code: 1
```

### Example 4: Backup and restore

```bash
python -m polygon_tool calc -i examples/square.txt --save
python -m polygon_tool backup
python -m polygon_tool calc -i examples/triangle.json --save   # data changed
python -m polygon_tool restore                                 # the square is back
```

## ⚠️ Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Data error (invalid input, file not found, invalid polygon) |
| 2 | Invalid command-line arguments |
| 3 | Storage or backup error |
