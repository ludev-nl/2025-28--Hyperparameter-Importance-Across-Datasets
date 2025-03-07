import unittest
import pandas as pd

from openmlfetcher import OpenMLFetcher


class OpenMLTests(unittest.TestCase):

    def setUp(self):
        self.omlf = OpenMLFetcher(6969, 99)

    def test_tasks_pos(self):
        openml100 = [3, 6, 11, 12, 14, 15, 16, 18, 22, 23, 28, 29, 31, 32, 37,
                     43, 45, 49, 53, 219, 2074, 2079, 3021, 3022, 3481, 3549,
                     3560, 3573, 3902, 3903, 3904, 3913, 3917, 3918, 7592,
                     9910, 9946, 9952, 9957, 9960, 9964, 9971, 9976, 9977,
                     9978, 9981, 9985, 10093, 10101, 14952, 14954, 14965,
                     14969, 14970, 125920, 125922, 146195, 146800, 146817,
                     146819, 146820, 146821, 146822, 146824, 146825, 167119,
                     167120, 167121, 167124, 167125, 167140, 167141]
        tasks = self.omlf.fetch_tasks()
        self.assertListEqual(tasks, openml100)

    def test_tasks_neg(self):
        self.omlf.suite_id = 1000000
        self.assertIsNone(self.omlf.fetch_tasks())

    def test_runs_pos(self):
        max_runs = 50
        data = self.omlf.fetch_runs(3, max_runs)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), max_runs)
        self.assertEqual(len(data.columns), 29)
        self.assertNotIn(object, set(data.dtypes))

    def test_runs_neg(self):
        data = self.omlf.fetch_runs(1000000)
        self.assertIsNone(data)


if __name__ == '__main__':
    unittest.main()
