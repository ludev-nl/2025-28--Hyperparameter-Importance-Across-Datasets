import unittest
import pandas as pd
import numpy as np

from ConfigSpace import ConfigurationSpace

import fanovaservice as fnvs


tasks = [3, 6, 11, 12, 14]
min_runs = 300


class FanovaTests(unittest.TestCase):

    def setUp(self):
        self.data = {t: pd.read_csv(f'tests/data/t{t}').convert_dtypes()
                     for t in tasks}
        # TODO: maybe correct cfg space

    def test_cfg_space(self):
        cfg_space = fnvs.auto_configspace(self.data)
        self.assertIsInstance(cfg_space, ConfigurationSpace)

        # Concatenate all data for ease
        data_list = list(self.data.values())
        all_data = pd.concat(data_list).dropna(axis=1, how='all')

        # Check that all parameters with actual values are in the space
        valid_params = all_data.drop(columns=['value']).columns
        self.assertSetEqual(set(valid_params), set(cfg_space.keys()))

        # Check that all instances fit in the configspace
        # NaN values are always accepted
        for param in list(cfg_space.values()):
            values = np.array(all_data[param.name].dropna())
            valid = param.legal_value(values).all()
            self.assertTrue(valid, f'Invalid values for f{param.name} found!')

    def test_filter(self):
        # TODO: filtering not implemented, so this test can not be made yet
        # test on smaller subset of which you know which instances should
        # remain
        pass

    def test_impute(self):
        # TODO: what cfg space to use? hardcoded?
        # Test all instances fit in new cfg space, which should not be bigger
        # than necessary. Test no nan values left.
        pass

    def test_prepare(self):
        # TODO: what imputed data to use? Or just dropna here?
        # Test further rounding does not do anything, and that all data is
        # numerical
        pass

    def test_run(self):
        # TODO: what prepared data to use?
        # Test only tasks with enough data appear in result
        # Test that no Constant parameter appears in result
        pass


if __name__ == '__main__':
    unittest.main()
