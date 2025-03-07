import unittest
import pandas as pd

from fanovaservice import FanovaService


tasks = [3, 6, 11, 12, 14]


class FanovaTests(unittest.TestCase):

    def setUp(self):
        self.data = {t: pd.read_csv(f'tests/data/t{t}').convert_dtypes()
                     for t in tasks}

    def test_init(self):
        fnvs = FanovaService(self.data)
        # TODO: tests for auto config space
        # - check length
        # - check types
        # - check ranges
        # TODO: further tests for imputation
        # - check configspace updated
        for data in fnvs.raw_data.values():
            self.assertFalse(data.isna().any(axis=None))

    def test_filter(self):
        fnvs = FanovaService(self.data)
        X, Y = fnvs.filter_data(tasks[1])
        self.assertEqual(len(X), len(Y))
        # TODO: check that X was actually filtered

    def test_run(self):
        fnvs = FanovaService(self.data)
        min_runs = 300
        results = fnvs.run_fanova(min_runs)

        self.assertListEqual(list(results.index), tasks[:4])
        for param in results.columns:
            self.assertIn(param, set(fnvs.raw_data[tasks[0]].columns))


if __name__ == '__main__':
    unittest.main()
