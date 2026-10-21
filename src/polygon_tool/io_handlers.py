"""Ввод и вывод данных: консоль и файлы TXT/CSV/JSON (ТЗ: ФТ-1, ФТ-2, ФТ-6, ФТ-7)."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Callable

from .geometry import Point


class DataError(ValueError):
    """Ошибка чтения или записи пользовательских данных."""


_SEPARATORS = re.compile(r"[,;\s]+")

CONSOLE_HELP = (
    "Введите вершины по порядку обхода, по одной на строку, в формате «x y» "
    "(разделитель: пробел, запятая или «;»).\n"
    "Пустая строка завершает ввод."
)


def _to_float(value: object, where: str) -> float:
    if isinstance(value, bool):
        raise DataError(f"{where}: логическое значение не является числом.")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise DataError(f"{where}: «{value}» не является числом.") from None
    if not math.isfinite(number):
        raise DataError(f"{where}: значение должно быть конечным числом.")
    return number


def parse_points_text(text: str, source: str = "ввод") -> list[Point]:
    """Разбирает текст: строка = одна вершина. Допускаются пустые строки,
    комментарии после «#» и заголовок «x,y» первой строкой (CSV)."""
    points: list[Point] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p for p in _SEPARATORS.split(line) if p]
        if not points and [p.lower() for p in parts] == ["x", "y"]:
            continue
        where = f"{source}, строка {lineno}"
        if len(parts) != 2:
            raise DataError(f"{where}: ожидалось два числа «x y», получено: «{raw.strip()}».")
        points.append((_to_float(parts[0], where), _to_float(parts[1], where)))
    if not points:
        raise DataError(f"{source}: не найдено ни одной точки.")
    return points


def _points_from_json(obj: object, source: str) -> list[Point]:
    if isinstance(obj, dict):
        obj = obj.get("points")
    if not isinstance(obj, list):
        raise DataError(f"{source}: ожидался список точек или объект с ключом «points».")
    points: list[Point] = []
    for i, item in enumerate(obj, start=1):
        where = f"{source}, точка {i}"
        if isinstance(item, dict) and "x" in item and "y" in item:
            x, y = item["x"], item["y"]
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            x, y = item
        else:
            raise DataError(f"{where}: ожидалась пара [x, y] или объект {{\"x\":..., \"y\":...}}.")
        points.append((_to_float(x, where), _to_float(y, where)))
    if not points:
        raise DataError(f"{source}: не найдено ни одной точки.")
    return points


def read_points_file(path: str | Path) -> list[Point]:
    """Читает вершины из файла. Формат определяется по расширению:
    .json — JSON, остальные (.txt, .csv, ...) — текст."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise DataError(f"Файл не найден: {path}") from None
    except UnicodeDecodeError:
        raise DataError(f"Файл {path} не является текстом в кодировке UTF-8.") from None
    except OSError as exc:
        raise DataError(f"Не удалось прочитать файл {path}: {exc.strerror or exc}") from None

    if path.suffix.lower() == ".json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            raise DataError(f"{path}: некорректный JSON ({exc.msg}, строка {exc.lineno}).") from None
        return _points_from_json(obj, str(path))
    return parse_points_text(text, source=str(path))


def read_points_console(
    input_fn: Callable[[str], str] | None = None,
    print_fn: Callable[[str], None] | None = None,
) -> list[Point]:
    """Интерактивный ввод вершин из консоли до пустой строки или конца ввода."""
    input_fn = input_fn or input
    print_fn = print_fn or print
    print_fn(CONSOLE_HELP)
    lines: list[str] = []
    while True:
        try:
            line = input_fn(f"Вершина {len(lines) + 1}: ")
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return parse_points_text("\n".join(lines), source="консоль")


def format_number(value: float, digits: int = 6) -> str:
    """Число с округлением до digits знаков, без лишних нулей."""
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def format_result_text(result: dict) -> str:
    return (
        f"Количество вершин: {result['vertices']}\n"
        f"Периметр: {format_number(result['perimeter'])}\n"
        f"Площадь: {format_number(result['area'])}"
    )


def write_result_file(path: str | Path, result: dict) -> None:
    """Записывает результат: .json — JSON, иначе — текст (ФТ-7)."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        payload = json.dumps(
            {
                "vertices": result["vertices"],
                "perimeter": round(result["perimeter"], 6),
                "area": round(result["area"], 6),
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        payload = format_result_text(result)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    except OSError as exc:
        raise DataError(f"Не удалось записать файл {path}: {exc.strerror or exc}") from None
