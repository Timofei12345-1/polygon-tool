"""Тесты модуля backup (TC-18 … TC-23)."""

import json
import tempfile
import unittest
from pathlib import Path

from polygon_tool.backup import BackupError, BackupManager

PTS = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]
OTHER = [(1.0, 1.0), (2.0, 1.0), (1.0, 5.0)]


class BackupTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.mgr = BackupManager(root / "data" / "points.json", root / "backups", keep=3)

    def test_save_and_load_roundtrip(self):
        self.mgr.save_points(PTS)
        self.assertEqual(self.mgr.load_points(), PTS)

    def test_tc18_backup_modify_restore(self):
        self.mgr.save_points(PTS)
        self.mgr.create_backup()
        self.mgr.save_points(OTHER)
        self.assertEqual(self.mgr.load_points(), OTHER)
        self.mgr.restore()
        self.assertEqual(self.mgr.load_points(), PTS)

    def test_tc18b_restore_specific_file(self):
        self.mgr.save_points(PTS)
        first = self.mgr.create_backup()
        self.mgr.save_points(OTHER)
        self.mgr.create_backup()
        self.mgr.restore(first)
        self.assertEqual(self.mgr.load_points(), PTS)

    def test_tc19_corrupted_backup_rejected(self):
        self.mgr.save_points(PTS)
        backup = self.mgr.create_backup()
        self.mgr.save_points(OTHER)
        backup.write_text(backup.read_text(encoding="utf-8").replace("4.0", "5.0", 1), encoding="utf-8")
        with self.assertRaises(BackupError) as ctx:
            self.mgr.verify_backup(backup)
        self.assertIn("Контрольная сумма", str(ctx.exception))
        with self.assertRaises(BackupError):
            self.mgr.restore(backup)
        self.assertEqual(self.mgr.load_points(), OTHER)  # данные не тронуты

    def test_tc20_rotation_keeps_latest_n(self):
        self.mgr.save_points(PTS)
        created = [self.mgr.create_backup() for _ in range(5)]
        remaining = self.mgr.list_backups()
        self.assertEqual(len(remaining), 3)
        self.assertEqual(remaining, sorted(created)[-3:])
        for old in created[:2]:
            self.assertFalse(old.exists())
            self.assertFalse(self.mgr._manifest_path(old).exists())

    def test_tc21_restore_snapshots_current_state(self):
        self.mgr.save_points(PTS)
        self.mgr.create_backup()
        self.mgr.save_points(OTHER)
        self.mgr.restore()
        backups = self.mgr.list_backups()
        self.assertEqual(len(backups), 2)  # исходная + снимок состояния перед восстановлением
        self.mgr.restore(backups[-1])      # откат восстановления
        self.assertEqual(self.mgr.load_points(), OTHER)

    def test_tc22_missing_or_broken_manifest(self):
        self.mgr.save_points(PTS)
        backup = self.mgr.create_backup()
        manifest = self.mgr._manifest_path(backup)
        manifest.write_text("{oops", encoding="utf-8")
        with self.assertRaises(BackupError):
            self.mgr.verify_backup(backup)
        manifest.unlink()
        with self.assertRaises(BackupError) as ctx:
            self.mgr.restore(backup)
        self.assertIn("манифест", str(ctx.exception).lower())

    def test_tc23_restore_without_backups(self):
        with self.assertRaises(BackupError):
            self.mgr.restore()

    def test_tc23b_backup_without_data_file(self):
        with self.assertRaises(BackupError):
            self.mgr.create_backup()

    def test_tc23c_corrupted_data_not_backed_up(self):
        self.mgr.data_file.parent.mkdir(parents=True)
        self.mgr.data_file.write_text("not json", encoding="utf-8")
        with self.assertRaises(BackupError):
            self.mgr.create_backup()
        self.assertEqual(self.mgr.list_backups(), [])

    def test_tc23d_restore_replaces_corrupted_data(self):
        self.mgr.save_points(PTS)
        self.mgr.create_backup()
        self.mgr.data_file.write_text("garbage", encoding="utf-8")
        self.mgr.restore()
        self.assertEqual(self.mgr.load_points(), PTS)

    def test_manifest_content(self):
        self.mgr.save_points(PTS)
        backup = self.mgr.create_backup()
        manifest = json.loads(self.mgr._manifest_path(backup).read_text(encoding="utf-8"))
        self.assertEqual(manifest["points_count"], 4)
        self.assertEqual(len(manifest["sha256"]), 64)
        self.assertEqual(manifest["file"], backup.name)

    def test_keep_one_restore_does_not_lose_data(self):
        mgr = BackupManager(self.mgr.data_file, self.mgr.backup_dir, keep=1)
        mgr.save_points(PTS)
        mgr.create_backup()
        mgr.save_points(OTHER)
        mgr.restore()
        self.assertEqual(mgr.load_points(), PTS)

    def test_invalid_keep(self):
        with self.assertRaises(ValueError):
            BackupManager("a.json", "b", keep=0)


if __name__ == "__main__":
    unittest.main()
