import unittest
import pandas as pd
import numpy as np

from ConfigSpace import ConfigurationSpace, CategoricalHyperparameter, Constant
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES

import fanovaservice as fnvs


cfg_space = ConfigurationSpace({'int': (0, 5),
                                'full_int': (0, 5),
                                'float': (0.0, 5.0),
                                'cat': ['a', 'b', 'c', 'IMPUTE_HPIAD'],
                                'full_cat': ['a', 'b', 'c', 'IMPUTE_HPIAD'],
                                'const': 'IMPUTE_HPIAD',
                                'full_const': -1})

imp_space = ConfigurationSpace({'int': (-1, 5),
                                'full_int': (0, 5),
                                'float': (-1.0, 5.0),
                                'cat': ['a', 'b', 'c',
                                        'IMPUTE_HPIAD', '_IMPUTE_HPIAD'],
                                'full_cat': ['a', 'b', 'c', 'IMPUTE_HPIAD'],
                                'const': ['IMPUTE_HPIAD', '_IMPUTE_HPIAD'],
                                'full_const': -1})


class FanovaTests(unittest.TestCase):

    def setUp(self):
        self.data = \
            {1: pd.read_csv('tests/sample1.csv', index_col=0).convert_dtypes(),
             2: pd.read_csv('tests/sample2.csv', index_col=0).convert_dtypes()}

    def cfg_space_equal(self,
                        created: ConfigurationSpace,
                        correct: ConfigurationSpace) -> bool:
        # Check that all hyperparams are as they should be
        for param_name, correct_param in correct.items():
            auto_param = created[param_name]
            # For categorical hyperparams, list equality of choices is checked
            # by default, but order is irrelevant so we check them as sets
            if (isinstance(correct_param, CategoricalHyperparameter)
                    and isinstance(auto_param, CategoricalHyperparameter)):
                self.assertSetEqual(set(auto_param.choices),
                                    set(correct_param.choices))
            else:
                self.assertEqual(auto_param, correct_param)

    def test_cfg_space(self):
        auto_cfg_space = fnvs.auto_configspace(self.data)
        self.assertIsInstance(auto_cfg_space, ConfigurationSpace)
        self.assertSetEqual(set(auto_cfg_space.keys()), set(cfg_space.keys()))

        self.cfg_space_equal(auto_cfg_space, cfg_space)

    def test_filter(self):
        filter_space = ConfigurationSpace({'int': (0, 4),
                                           'full_int': (0, 5),
                                           'float': (1.0, 5.0),
                                           'cat': ['a', 'c', 'IMPUTE_HPIAD'],
                                           'full_cat': ['a', 'b', 'c', 'IMPUTE_HPIAD'],
                                           'const': 'IMPUTE_HPIAD',
                                           'full_const': -1})

        # Filter the data, and determine what it should be
        filtered = fnvs.filter_data(self.data, filter_space)
        correct = {id: data[((data.cat != 'b') | data.cat.isna())
                            & ((data.int != 5) | data.int.isna())
                            & ((data.float >= 1.0) | data.float.isna())]
                   for id, data in self.data.items()}

        # Check we filtered correctly
        for id, data in filtered.items():
            self.assertIsInstance(data, pd.DataFrame)
            self.assertTrue(data.equals(correct[id]))

    def test_impute(self):
        imputed_data, new_space = fnvs.impute_data(self.data, cfg_space)

        # Assert that there are no missing values anymore
        for data in imputed_data.values():
            self.assertIsInstance(data, pd.DataFrame)
            self.assertFalse(data.isna().any().any())
            # Assert that the new data fits in the correct config space
            for param_name, param in imp_space.items():
                values = np.array(data[param_name])
                self.assertTrue(param.legal_value(values).all())

        # Assert that the new configspace is correct
        self.cfg_space_equal(new_space, imp_space)

    def test_prepare(self):
        default = dict(cfg_space.get_default_configuration())
        imputed = {id: data.fillna(default).dropna(axis=1, how='any')
                   for id, data in self.data.items()}
        prepared = fnvs.prepare_data(imputed, cfg_space)

        for prep in prepared.values():
            self.assertIsInstance(prep, pd.DataFrame)

            # Test that all numerical data has already been rounded
            rounded = prep.apply(np.round, decimals=ROUND_PLACES)
            self.assertTrue(prep.equals(rounded))

            # Test that all data is now numerical
            non_numeric = prep.select_dtypes(exclude=['number']).columns
            self.assertEqual(len(non_numeric), 0)

    def test_run(self):
        # Replaces data by relevant numeric data for fanova
        def prep(val):
            if isinstance(val, int) and val < 0:
                return 0

            elif isinstance(val, str):
                if val == 'a':
                    return 1
                elif val == 'b':
                    return 2
                elif val == 'c':
                    return 3
                return 0

            return val

        # Prepare the data using stub implementations
        default = dict(cfg_space.get_default_configuration())
        imputed = self.data[1].fillna(default).dropna(axis=1, how='any')
        prepared = imputed.map(lambda x: prep(x))

        # Run fANOVA once succesfully
        result = fnvs.run_fanova(prepared, cfg_space, min_runs=0)
        # And check that all non-constant hyperparams appear
        for param_name, param in cfg_space.items():
            if isinstance(param, Constant):
                self.assertNotIn(param_name, result.keys())
            else:
                self.assertIn(param_name, result.keys())

        # Run fANOVA once unsuccesfully
        result = fnvs.run_fanova(prepared, cfg_space, min_runs=len(prepared)+1)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
