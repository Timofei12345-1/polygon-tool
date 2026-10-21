"""Резервное копирование и восстановление точек координат (ТЗ: ФТ-8 … ФТ-13).

Хранилище точек — JSON-файл {"points": [[x, y], ...]}.
Каждая копия — файл points_<дата>_<время>_<мкс>.json плюс манифест
points_<...>.manifest.json с SHA-256, числом точек и датой создания.
Все записи атомарные: данные пишутся во временный файл и подменяются os.replace.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import datetime
from pathlib import Path

from .geometry import Point

MANIFEST_SUFFIX = ".manifest.json"
FORMAT_VERSION = 1


class BackupError(Exception):
    """Ошибка хранилища, резервной копии или восстановления."""


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _parse_points(data: bytes, source: str) -> list[Point]:
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupError(f"{source}: некорректный JSON ({exc}).") from None
    raw = obj.get("points") if isinstance(obj, dict) else None
    if not isinstance(raw, list):
        raise BackupError(f"{source}: отсутствует список «points».")
    points: list[Point] = []
    for i, item in enumerate(raw, start=1):
        if not (isinstance(item, (list, tuple)) and len(item) == 2 and all(_is_number(v) for v in item)):
            raise BackupError(f"{source}: точка {i} не является парой чисел [x, y].")
        points.append((float(item[0]), float(item[1])))
    return points


def _serialize(points: list[Point]) -> bytes:
    return json.dumps({"points": [[x, y] for x, y in points]}, indent=2).encode("utf-8")


class BackupManager:
    """Хранилище точек и управление его резервными копиями."""

    def __init__(self, data_file: str | Path, backup_dir: str | Path, keep: int = 10) -> None:
        if keep < 1:
            raise ValueError("keep должен быть >= 1")
        self.data_file = Path(data_file)
        self.backup_dir = Path(backup_dir)
        self.keep = keep

    # --- хранилище -------------------------------------------------------

    def save_points(self, points: list[Point]) -> None:
        """Атомарно записывает точки в хранилище (ФТ-8)."""
        _atomic_write(self.data_file, _serialize(list(points)))

    def load_points(self) -> list[Point]:
        try:
            data = self.data_file.read_bytes()
        except FileNotFoundError:
            raise BackupError(f"Файл данных не найден: {self.data_file}") from None
        except OSError as exc:
            raise BackupError(f"Не удалось прочитать {self.data_file}: {exc.strerror or exc}") from None
        return _parse_points(data, str(self.data_file))

    # --- копии -----------------------------------------------------------

    def _new_backup_path(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        candidate = self.backup_dir / f"points_{stamp}.json"
        counter = 0
        while candidate.exists():
            counter += 1
            candidate = self.backup_dir / f"points_{stamp}_{counter:03d}.json"
        return candidate

    @staticmethod
    def _manifest_path(backup: Path) -> Path:
        return backup.with_name(backup.stem + MANIFEST_SUFFIX)

    def create_backup(self) -> Path:
        """Создаёт копию текущих данных с манифестом и выполняет ротацию (ФТ-9, ФТ-12)."""
        try:
            data = self.data_file.read_bytes()
        except FileNotFoundError:
            raise BackupError(f"Нечего копировать: файл данных не найден ({self.data_file}).") from None
        except OSError as exc:
            raise BackupError(f"Не удалось прочитать {self.data_file}: {exc.strerror or exc}") from None
        points = _parse_points(data, str(self.data_file))  # не копируем повреждённые данные

        backup = self._new_backup_path()
        manifest = {
            "format_version": FORMAT_VERSION,
            "file": backup.name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "points_count": len(points),
            "created": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        try:
            _atomic_write(backup, data)
            _atomic_write(self._manifest_path(backup), json.dumps(manifest, indent=2).encode("utf-8"))
        except OSError as exc:
            raise BackupError(f"Не удалось создать копию: {exc.strerror or exc}") from None
        self._rotate()
        return backup

    def list_backups(self) -> list[Path]:
        """Копии от старых к новым (ФТ-13)."""
        if not self.backup_dir.is_dir():
            return []
        return sorted(
            p for p in self.backup_dir.glob("points_*.json") if not p.name.endswith(MANIFEST_SUFFIX)
        )

    def _rotate(self) -> None:
        backups = self.list_backups()
        for old in backups[: max(0, len(backups) - self.keep)]:
            for path in (old, self._manifest_path(old)):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    def verify_backup(self, backup: str | Path) -> dict:
        """Проверяет целостность копии (SHA-256, число точек); возвращает манифест (ФТ-10)."""
        backup = Path(backup)
        try:
            data = backup.read_bytes()
        except FileNotFoundError:
            raise BackupError(f"Копия не найдена: {backup}") from None
        except OSError as exc:
            raise BackupError(f"Не удалось прочитать копию {backup}: {exc.strerror or exc}") from None

        manifest_path = self._manifest_path(backup)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise BackupError(f"Нет манифеста для копии {backup.name}: целостность не подтверждена.") from None
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            raise BackupError(f"Манифест копии {backup.name} повреждён.") from None
        if not isinstance(manifest, dict):
            raise BackupError(f"Манифест копии {backup.name} повреждён.")

        if hashlib.sha256(data).hexdigest() != manifest.get("sha256"):
            raise BackupError(f"Контрольная сумма копии {backup.name} не совпадает: файл изменён или повреждён.")
        points = _parse_points(data, backup.name)
        if len(points) != manifest.get("points_count"):
            raise BackupError(f"Число точек в копии {backup.name} не совпадает с манифестом.")
        return manifest

    def restore(self, backup: str | Path | None = None) -> Path:
        """Восстанавливает данные из копии (по умолчанию — самой свежей) (ФТ-11).

        Перед заменой копия проверяется, а текущее состояние сохраняется
        в отдельную копию, чтобы восстановление можно было откатить.
        """
        if backup is None:
            backups = self.list_backups()
            if not backups:
                raise BackupError(f"Резервных копий нет (каталог: {self.backup_dir}).")
            backup = backups[-1]
        backup = Path(backup)

        self.verify_backup(backup)
        data = backup.read_bytes()  # читаем до ротации: копия не пропадёт, даже если keep мал

        if self.data_file.exists():
            try:
                self.create_backup()
            except BackupError:
                pass  # текущие данные повреждены — их всё равно заменяем проверенной копией
        try:
            _atomic_write(self.data_file, data)
        except OSError as exc:
            raise BackupError(f"Не удалось записать {self.data_file}: {exc.strerror or exc}") from None
        return backup
