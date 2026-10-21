"""Тесты модуля geometry. Идентификаторы TC-xx соответствуют docs/test-cases.md."""

import math
import unittest

from polygon_tool.geometry import PolygonError, analyze, area, perimeter, signed_area

SQUARE = [(0, 0), (4, 0), (4, 4), (0, 4)]
L_SHAPE = [(0, 0), (4, 0), (4, 2), (2, 2), (2, 4), (0, 4)]


class GeometryTests(unittest.TestCase):
    def test_tc01_square(self):
        r = analyze(SQUARE)
        self.assertAlmostEqual(r["perimeter"], 16)
        self.assertAlmostEqual(r["area"], 16)
        self.assertEqual(r["vertices"], 4)

    def test_tc02_triangle_3_4_5(self):
        r = analyze([(0, 0), (3, 0), (0, 4)])
        self.assertAlmostEqual(r["perimeter"], 12)
        self.assertAlmostEqual(r["area"], 6)

    def test_tc03_non_convex_l_shape(self):
        r = analyze(L_SHAPE)
        self.assertAlmostEqual(r["perimeter"], 16)
        self.assertAlmostEqual(r["area"], 12)

    def test_tc04_orientation_does_not_matter(self):
        self.assertAlmostEqual(area(SQUARE), area(SQUARE[::-1]))
        self.assertGreater(signed_area(SQUARE), 0)
        self.assertLess(signed_area(SQUARE[::-1]), 0)
        self.assertAlmostEqual(perimeter(SQUARE), perimeter(SQUARE[::-1]))

    def test_tc05_fewer_than_three_points(self):
        for pts in ([], [(0, 0)], [(0, 0), (1, 1)]):
            with self.subTest(n=len(pts)), self.assertRaises(PolygonError):
                analyze(pts)

    def test_tc06_collinear_points(self):
        with self.assertRaises(PolygonError) as ctx:
            analyze([(0, 0), (1, 1), (2, 2)])
        self.assertIn("одной прямой", str(ctx.exception))

    def test_tc07_self_intersecting_bowtie(self):
        with self.assertRaises(PolygonError) as ctx:
            analyze([(0, 0), (4, 4), (4, 0), (0, 4)])
        self.assertIn("самопересека", str(ctx.exception))

    def test_tc08_duplicate_adjacent_vertices(self):
        with self.assertRaises(PolygonError):
            analyze([(0, 0), (4, 0), (4, 0), (4, 4), (0, 4)])
        with self.assertRaises(PolygonError):  # первая точка повторена в конце
            analyze(SQUARE + [(0, 0)])

    def test_tc09_non_finite_coordinates(self):
        for bad in (math.nan, math.inf):
            with self.subTest(bad=bad), self.assertRaises(PolygonError):
                analyze([(0, 0), (1, 0), (0, bad)])

    def test_tc10_fractional_coordinates(self):
        r = analyze([(0, 0), (2.5, 0), (2.5, 1.5), (0, 1.5)])
        self.assertAlmostEqual(r["perimeter"], 8)
        self.assertAlmostEqual(r["area"], 3.75)

    def test_tc28_large_offset_precision(self):
        base = 1e9
        r = analyze([(base, base), (base + 1, base), (base + 1, base + 1), (base, base + 1)])
        self.assertEqual(r["area"], 1.0)
        self.assertAlmostEqual(r["perimeter"], 4.0)

    def test_tc29_touching_sides_rejected(self):
        # вершина 5 лежит на стороне 1: контур касается сам себя
        with self.assertRaises(PolygonError):
            analyze([(0, 0), (4, 0), (4, 4), (2, 0), (0, 4)])

    def test_tc30_folded_back_sides_rejected(self):
        with self.assertRaises(PolygonError):
            analyze([(0, 0), (4, 0), (2, 0), (2, 3)])


if __name__ == "__main__":
    unittest.main()
