"""Тесты модуля io_handlers (TC-11 … TC-17)."""

import json
import tempfile
import unittest
from pathlib import Path

from polygon_tool.io_handlers import (
    DataError,
    format_number,
    parse_points_text,
    read_points_console,
    read_points_file,
    write_result_file,
)

RESULT = {"vertices": 4, "perimeter": 16.0, "area": 16.0}


class IoTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_tc11_text_separators_comments_header(self):
        text = "x,y\n# комментарий\n0 0\n4,0\n\n4;4  # хвост\n0\t4\n"
        self.assertEqual(parse_points_text(text), [(0, 0), (4, 0), (4, 4), (0, 4)])

    def test_tc12_non_numeric_input_reports_line(self):
        with self.assertRaises(DataError) as ctx:
            parse_points_text("0 0\nabc 1\n")
        self.assertIn("строка 2", str(ctx.exception))

    def test_tc12b_wrong_number_of_values_and_nan(self):
        for text in ("1 2 3\n", "5\n", "nan 1\n", "inf 2\n"):
            with self.subTest(text=text), self.assertRaises(DataError):
                parse_points_text(text)

    def test_tc13_missing_file(self):
        with self.assertRaises(DataError) as ctx:
            read_points_file(self.tmp / "nope.txt")
        self.assertIn("не найден", str(ctx.exception))

    def test_tc14_empty_file(self):
        for name, content in (("e.txt", ""), ("c.txt", "# только комментарий\n"), ("e.json", "[]")):
            path = self.tmp / name
            path.write_text(content, encoding="utf-8")
            with self.subTest(name=name), self.assertRaises(DataError):
                read_points_file(path)

    def test_tc15_json_formats(self):
        expected = [(0, 0), (3, 0), (0, 4)]
        variants = {
            "a.json": [[0, 0], [3, 0], [0, 4]],
            "b.json": {"points": [[0, 0], [3, 0], [0, 4]]},
            "c.json": [{"x": 0, "y": 0}, {"x": 3, "y": 0}, {"x": 0, "y": 4}],
        }
        for name, obj in variants.items():
            path = self.tmp / name
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.subTest(name=name):
                self.assertEqual(read_points_file(path), expected)

    def test_tc15b_broken_json(self):
        path = self.tmp / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(DataError):
            read_points_file(path)
        path.write_text('[[0, 0], [1]]', encoding="utf-8")
        with self.assertRaises(DataError):
            read_points_file(path)

    def test_tc15c_csv_and_bom(self):
        path = self.tmp / "p.csv"
        path.write_text("x,y\n0,0\n2,0\n0,2\n", encoding="utf-8-sig")
        self.assertEqual(read_points_file(path), [(0, 0), (2, 0), (0, 2)])

    def test_tc16_console_input(self):
        answers = iter(["0 0", "3 0", "0 4", ""])
        out = []
        points = read_points_console(input_fn=lambda prompt: next(answers), print_fn=out.append)
        self.assertEqual(points, [(0, 0), (3, 0), (0, 4)])
        self.assertTrue(out)  # подсказка показана

    def test_tc16b_console_eof_ends_input(self):
        answers = iter(["0 0", "1 0", "0 1"])

        def fake_input(prompt):
            try:
                return next(answers)
            except StopIteration:
                raise EOFError

        self.assertEqual(len(read_points_console(input_fn=fake_input, print_fn=lambda s: None)), 3)

    def test_tc17_write_result_txt_and_json(self):
        txt = self.tmp / "sub" / "r.txt"
        write_result_file(txt, RESULT)
        content = txt.read_text(encoding="utf-8")
        self.assertIn("Периметр: 16", content)
        self.assertIn("Площадь: 16", content)

        js = self.tmp / "r.json"
        write_result_file(js, RESULT)
        self.assertEqual(json.loads(js.read_text(encoding="utf-8")), RESULT)

    def test_tc17b_write_to_unwritable_path(self):
        blocker = self.tmp / "file"
        blocker.write_text("x", encoding="utf-8")
        with self.assertRaises(DataError):
            write_result_file(blocker / "r.txt", RESULT)  # «каталог» — на самом деле файл

    def test_format_number(self):
        self.assertEqual(format_number(16.0), "16")
        self.assertEqual(format_number(3.75), "3.75")
        self.assertEqual(format_number(1 / 3), "0.333333")
        self.assertEqual(format_number(-0.0000001), "0")


if __name__ == "__main__":
    unittest.main()
