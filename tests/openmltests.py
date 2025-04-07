import unittest
import pandas as pd

import openmlfetcher as omlf


suite_id = 99
flow_id = 6969
openml100 = [3, 6, 11, 12, 14, 15, 16, 18, 22, 23, 28, 29, 31, 32, 37,
             43, 45, 49, 53, 219, 2074, 2079, 3021, 3022, 3481, 3549,
             3560, 3573, 3902, 3903, 3904, 3913, 3917, 3918, 7592,
             9910, 9946, 9952, 9957, 9960, 9964, 9971, 9976, 9977,
             9978, 9981, 9985, 10093, 10101, 14952, 14954, 14965,
             14969, 14970, 125920, 125922, 146195, 146800, 146817,
             146819, 146820, 146821, 146822, 146824, 146825, 167119,
             167120, 167121, 167124, 167125, 167140, 167141]
max_runs = 50


class OpenMLTests(unittest.TestCase):

    def test_flows(self):
        flows = omlf.fetch_flows()
        self.assertIsInstance(flows, pd.DataFrame)
        # Check the columns are correct, and that there are at least as
        # many as at the time of development
        self.assertListEqual(list(flows.columns), ['name', 'version'])
        self.assertGreaterEqual(len(flows), 46546)

    def test_suites(self):
        suites = omlf.fetch_suites()
        self.assertIsInstance(suites, pd.DataFrame)
        # Check the columns are correct, and that there are at least as
        # many as at the time of development
        self.assertListEqual(list(suites.columns), ['alias'])
        self.assertGreaterEqual(len(suites), 3)

    def test_tasks_pos(self):
        tasks = omlf.fetch_tasks(suite_id)
        self.assertListEqual(tasks, openml100)

    def test_tasks_neg(self):
        # TODO: this behaviour might change as we implement error handling
        self.assertIsNone(omlf.fetch_tasks(1000000))

    def test_runs_pos(self):
        data = omlf.fetch_runs(flow_id, openml100[0], max_runs)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), max_runs)
        self.assertEqual(len(data.columns), 29)

        # This needs to be in one test, as a seperate unit test
        # would require reading data from a file, and Pandas
        # would interfere by reinterpreting types
        data = omlf.coerce_types(data)
        self.assertIsInstance(data, pd.DataFrame)
        self.assertNotIn(object, set(data.dtypes))

    def test_runs_neg(self):
        data = omlf.fetch_runs(flow_id, 1000000, max_runs)
        self.assertIsNone(data)


if __name__ == '__main__':
    unittest.main()
