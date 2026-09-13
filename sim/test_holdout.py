import unittest

from evaluate_holdout import CASES


class HoldoutManifestTests(unittest.TestCase):
    def test_grid_is_unique_and_balanced(self):
        self.assertEqual(len(CASES), 12)
        self.assertEqual(len(set(CASES)), len(CASES))
        self.assertEqual({x for x, _ in CASES}, {.65, .8, .95})
        self.assertEqual({y for _, y in CASES}, {-.35, -.12, .12, .35})


if __name__ == '__main__':
    unittest.main()
