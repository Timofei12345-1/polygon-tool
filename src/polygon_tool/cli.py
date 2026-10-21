"""Консольный интерфейс (ТЗ: ФТ-1 … ФТ-14).

Коды возврата: 0 — успех; 1 — ошибка данных или многоугольника;
2 — неверные аргументы (argparse); 3 — ошибка резервного копирования.
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .backup import BackupError, BackupManager
from .geometry import PolygonError, analyze
from .io_handlers import (
    DataError,
    format_result_text,
    read_points_console,
    read_points_file,
    write_result_file,
)

EXIT_OK = 0
EXIT_DATA_ERROR = 1
EXIT_BACKUP_ERROR = 3


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-file", default="data/points.json", help="файл хранилища точек (по умолчанию data/points.json)")
    common.add_argument("--backup-dir", default="backups", help="каталог резервных копий (по умолчанию backups)")
    common.add_argument("--keep", type=int, default=10, help="сколько копий хранить (по умолчанию 10)")

    parser = argparse.ArgumentParser(
        prog="polygon-tool",
        description="Периметр и площадь многоугольника по координатам вершин; резервное копирование точек.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="команда")

    calc = sub.add_parser("calc", parents=[common], help="вычислить периметр и площадь")
    calc.add_argument("-i", "--input", help="входной файл (.txt, .csv, .json); без него — ввод из консоли")
    calc.add_argument("-o", "--output", help="выходной файл (.txt или .json); без него — только консоль")
    calc.add_argument("--save", action="store_true", help="сохранить введённые точки в хранилище")

    sub.add_parser("backup", parents=[common], help="создать резервную копию хранилища")

    restore = sub.add_parser("restore", parents=[common], help="восстановить хранилище из копии")
    group = restore.add_mutually_exclusive_group()
    group.add_argument("--latest", action="store_true", help="взять самую свежую копию (по умолчанию)")
    group.add_argument("--file", help="путь к конкретной копии")

    sub.add_parser("list-backups", parents=[common], help="показать список копий")

    verify = sub.add_parser("verify", parents=[common], help="проверить целостность копий")
    verify.add_argument("--file", help="проверить только эту копию (иначе — все)")
    return parser


def _cmd_calc(args: argparse.Namespace, manager: BackupManager) -> int:
    points = read_points_file(args.input) if args.input else read_points_console()
    result = analyze(points)
    print(format_result_text(result))
    if args.output:
        write_result_file(args.output, result)
        print(f"Результат записан в {args.output}")
    if args.save:
        try:
            manager.save_points(points)
        except OSError as exc:
            raise BackupError(f"Не удалось сохранить точки: {exc.strerror or exc}") from None
        print(f"Точки сохранены в {manager.data_file}")
    return EXIT_OK


def _cmd_backup(args: argparse.Namespace, manager: BackupManager) -> int:
    path = manager.create_backup()
    print(f"Копия создана: {path}")
    return EXIT_OK


def _cmd_restore(args: argparse.Namespace, manager: BackupManager) -> int:
    path = manager.restore(args.file)
    print(f"Данные восстановлены из {path}")
    return EXIT_OK


def _cmd_list(args: argparse.Namespace, manager: BackupManager) -> int:
    backups = manager.list_backups()
    if not backups:
        print("Резервных копий нет.")
        return EXIT_OK
    for path in backups:
        try:
            info = manager.verify_backup(path)
            print(f"{path.name}  точек: {info['points_count']}  создана: {info['created']}")
        except BackupError as exc:
            print(f"{path.name}  ПОВРЕЖДЕНА: {exc}")
    return EXIT_OK


def _cmd_verify(args: argparse.Namespace, manager: BackupManager) -> int:
    targets = [args.file] if args.file else manager.list_backups()
    if not targets:
        print("Резервных копий нет.")
        return EXIT_OK
    bad = 0
    for target in targets:
        try:
            manager.verify_backup(target)
            print(f"OK       {target}")
        except BackupError as exc:
            bad += 1
            print(f"ОШИБКА   {exc}")
    return EXIT_BACKUP_ERROR if bad else EXIT_OK


COMMANDS = {
    "calc": _cmd_calc,
    "backup": _cmd_backup,
    "restore": _cmd_restore,
    "list-backups": _cmd_list,
    "verify": _cmd_verify,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manager = BackupManager(args.data_file, args.backup_dir, args.keep)
    except ValueError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_DATA_ERROR
    try:
        return COMMANDS[args.command](args, manager)
    except (PolygonError, DataError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_DATA_ERROR
    except BackupError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_BACKUP_ERROR
    except KeyboardInterrupt:
        print("\nПрервано пользователем.", file=sys.stderr)
        return EXIT_DATA_ERROR


if __name__ == "__main__":
    sys.exit(main())
