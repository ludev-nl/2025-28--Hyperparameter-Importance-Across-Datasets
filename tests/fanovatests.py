import unittest
import pandas as pd
import numpy as np

from ConfigSpace import ConfigurationSpace, CategoricalHyperparameter
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES

import fanovaservice as fnvs


cfg_space = ConfigurationSpace({'int': (0,5),
                                'float': (0.0, 5.0),
                                'cat': ['a', 'b', 'c'],
                                'const': 'value'})
min_runs = 300


class FanovaTests(unittest.TestCase):

    def setUp(self):
        self.data = {0: pd.read_csv('tests/sample.csv', index_col=0).convert_dtypes()}

    def test_cfg_space(self):
        auto_cfg_space = fnvs.auto_configspace(self.data)
        self.assertIsInstance(auto_cfg_space, ConfigurationSpace)
        self.assertSetEqual(set(auto_cfg_space.keys()), set(cfg_space.keys()))

        # Check that all hyperparams are as they should be
        for param_name, correct_param in cfg_space.items():
            auto_param = auto_cfg_space[param_name]
            # For categorical hyperparams, list equality of choices is checked
            # by default, but their order is irrelevant so we check them as sets
            if (isinstance(correct_param, CategoricalHyperparameter)
                    and isinstance(auto_param, CategoricalHyperparameter)):
                self.assertSetEqual(set(auto_param.choices), set(correct_param.choices))
            else:
                self.assertEqual(auto_param, correct_param)

    def test_filter(self):
        filter_space = ConfigurationSpace({'int': (0,4),
                                           'float': (1.0, 5.0),
                                           'cat': ['a', 'c'],
                                           'const': 'value'})

        # Filter the data, and determine what it should be
        filtered = fnvs.filter_data(self.data, filter_space)[0]
        data = self.data[0]
        correct = data[((data.cat != 'b') | data.cat.isna())
                       & ((data.int != 5) | data.int.isna())
                       & ((data.float >= 1.0) | data.float.isna())]

        # Check we filtered correctly
        self.assertIsInstance(filtered, pd.DataFrame)
        self.assertTrue(filtered.equals(correct))

    def test_impute(self):
        imputed_data, new_space = fnvs.impute_data(self.data, cfg_space)
        data = imputed_data[0]

        # Assert that there are no missing values anymore
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.isna().any().any())

        # Assert that the new data fits in the new config space
        for param_name in new_space:
            param = new_space[param_name]
            values = np.array(data[param_name])
            self.assertTrue(param.legal_value(values).all())

    def test_prepare(self):
        default = dict(cfg_space.get_default_configuration())
        imputed = self.data[0].fillna(default)
        prepared = fnvs.prepare_data({0: imputed}, cfg_space)[0]
        self.assertIsInstance(prepared, pd.DataFrame)

        # Test that all numerical data has already been rounded
        rounded = prepared.apply(np.round, decimals=ROUND_PLACES)
        self.assertTrue(prepared.equals(rounded))

        # Test that all data is now numerical
        non_numeric = prepared.select_dtypes(exclude=['number']).columns
        self.assertEqual(len(non_numeric), 0)

    def test_run(self):
        # TODO: what prepared data to use?
        # Test only tasks with enough data appear in result
        # Test that no Constant parameter appears in result
        pass


if __name__ == '__main__':
    unittest.main()
