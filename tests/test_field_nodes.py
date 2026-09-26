import unittest

from python_library.nodes import field_nodes as f


CLASSIC = (
    "I/1: 0,1; 1,1; 2,1; 3,1 | O/2: 0,0; 1,0; 0,1; 1,1 | "
    "T/3: 1,0; 0,1; 1,1; 2,1"
)


class FieldNodesTest(unittest.TestCase):
    def test_ensure_field_creates_and_keeps(self):
        grid, created = f.ensure_field(None, 10, 20, 0, 2, 8, 5)
        self.assertTrue(created)
        self.assertEqual(len(grid), 20)
        self.assertEqual(len(grid[0]), 10)
        self.assertIn(0, grid[-1])
        again, _ = f.ensure_field(None, 10, 20, 0, 2, 8, 5)
        self.assertEqual(grid, again)
        same, created = f.ensure_field(grid, 5, 5, 0, 0, 8, 1)
        self.assertIs(same, grid)
        self.assertFalse(created)

    def test_shapes_and_rotation(self):
        points, value, count, name = f.shape_from_set(CLASSIC, 4)
        self.assertEqual(count, 3)
        self.assertEqual(value, 2)
        self.assertEqual(name, "O")
        line, _, _, _ = f.shape_from_set(CLASSIC, 0)
        self.assertEqual(sorted(f.rotate_shape(line, 4)), sorted(line))
        vertical = f.rotate_shape(line, 1)
        self.assertEqual(len({p[0] for p in vertical}), 1)

    def test_fits_stamp_and_rows(self):
        grid, _ = f.ensure_field(None, 4, 3, 0, 0, 8, 1)
        line = [[0, 0], [1, 0], [2, 0], [3, 0]]
        self.assertEqual(f.fits(grid, line, 0, 2, 0)[0], "да")
        self.assertEqual(f.fits(grid, line, 1, 2, 0)[0], "нет")
        self.assertEqual(f.drop_distance(grid, line, 0, 0, 0), 2)
        full = f.stamp(grid, line, 0, 2, 1)
        self.assertEqual(grid[2], [0, 0, 0, 0])
        cleared, removed = f.remove_full_rows(full, 0)
        self.assertEqual(removed, 1)
        self.assertEqual(cleared[2], [0, 0, 0, 0])

    def test_scoring_speed_and_keys(self):
        self.assertEqual(f.score_gain(2, 3, "0,100,300,500,800", 5, 2), 910)
        self.assertEqual(f.level_from_lines(25, 1, 10), 3)
        self.assertEqual(f.step_interval(3, 1, 800, 60, 80), 680)
        self.assertEqual(f.step_interval(50, 1, 800, 60, 80), 80)
        self.assertEqual(
            f.key_command("A", "Left,A", "Right,D", "Up,W", "Down,S", "Space", "P", "R"),
            "влево",
        )
        self.assertEqual(f.fill_template("{0}/{1}", None, 3.0, ""), "0/3")


if __name__ == "__main__":
    unittest.main()
