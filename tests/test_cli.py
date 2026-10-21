"""Интеграционные тесты консольного интерфейса (TC-24 … TC-27)."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from polygon_tool.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.store = ["--data-file", str(self.tmp / "data" / "points.json"), "--backup-dir", str(self.tmp / "bk")]

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(list(argv))
            except SystemExit as exc:  # argparse
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_tc24_file_to_file(self):
        out_file = self.tmp / "result.json"
        code, out, _ = self.run_cli("calc", "-i", str(EXAMPLES / "square.txt"), "-o", str(out_file))
        self.assertEqual(code, 0)
        self.assertIn("Периметр: 16", out)
        self.assertEqual(json.loads(out_file.read_text(encoding="utf-8"))["area"], 16)

    def test_tc24b_all_example_formats(self):
        expected = {"square.txt": "16", "l_shape.csv": "12", "triangle.json": "6"}
        for name, area in expected.items():
            with self.subTest(name=name):
                code, out, _ = self.run_cli("calc", "-i", str(EXAMPLES / name))
                self.assertEqual(code, 0)
                self.assertIn(f"Площадь: {area}", out)

    def test_tc25_invalid_polygon_exit_code(self):
        code, out, err = self.run_cli("calc", "-i", str(EXAMPLES / "bowtie_invalid.txt"))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Ошибка", err)

    def test_tc25b_missing_input_file(self):
        code, _, err = self.run_cli("calc", "-i", str(self.tmp / "none.txt"))
        self.assertEqual(code, 1)
        self.assertIn("не найден", err)

    def test_tc26_console_input(self):
        answers = iter(["0 0", "3 0", "0 4", ""])
        with mock.patch("builtins.input", lambda prompt="": next(answers)):
            code, out, _ = self.run_cli("calc")
        self.assertEqual(code, 0)
        self.assertIn("Периметр: 12", out)
        self.assertIn("Площадь: 6", out)

    def test_tc27_backup_restore_cycle(self):
        sq = str(EXAMPLES / "square.txt")
        self.assertEqual(self.run_cli("calc", "-i", sq, "--save", *self.store)[0], 0)
        code, out, _ = self.run_cli("backup", *self.store)
        self.assertEqual((code, "Копия создана" in out), (0, True))
        self.assertEqual(self.run_cli("calc", "-i", str(EXAMPLES / "triangle.json"), "--save", *self.store)[0], 0)
        code, out, _ = self.run_cli("restore", "--latest", *self.store)
        self.assertEqual(code, 0)
        code, out, _ = self.run_cli("calc", "-i", str(self.tmp / "data" / "points.json"))
        self.assertIn("Площадь: 16", out)

    def test_tc27b_list_and_verify(self):
        self.run_cli("calc", "-i", str(EXAMPLES / "square.txt"), "--save", *self.store)
        self.run_cli("backup", *self.store)
        code, out, _ = self.run_cli("list-backups", *self.store)
        self.assertEqual(code, 0)
        self.assertIn("точек: 4", out)
        code, out, _ = self.run_cli("verify", *self.store)
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_tc27c_verify_detects_corruption(self):
        self.run_cli("calc", "-i", str(EXAMPLES / "square.txt"), "--save", *self.store)
        self.run_cli("backup", *self.store)
        backup = next((self.tmp / "bk").glob("points_*[0-9].json"))
        backup.write_text("{}", encoding="utf-8")
        code, out, _ = self.run_cli("verify", *self.store)
        self.assertEqual(code, 3)
        self.assertIn("ОШИБКА", out)
        code, _, err = self.run_cli("restore", *self.store)
        self.assertEqual(code, 3)
        self.assertIn("Ошибка", err)

    def test_tc27d_restore_without_backups(self):
        code, _, err = self.run_cli("restore", *self.store)
        self.assertEqual(code, 3)
        self.assertIn("Резервных копий нет", err)

    def test_tc31_usage_errors(self):
        self.assertEqual(self.run_cli()[0], 2)
        self.assertEqual(self.run_cli("restore", "--latest", "--file", "x", *self.store)[0], 2)

    def test_tc32_invalid_keep(self):
        code, _, err = self.run_cli("backup", "--keep", "0", *self.store)
        self.assertEqual(code, 1)
        self.assertIn("Ошибка", err)


if __name__ == "__main__":
    unittest.main()
