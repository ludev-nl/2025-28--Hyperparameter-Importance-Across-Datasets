import unittest
import pandas as pd
import numpy as np

from ConfigSpace import ConfigurationSpace, CategoricalHyperparameter, Constant, OrdinalHyperparameter
from ConfigSpace.hyperparameters import NumericalHyperparameter
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES

import fanovaservice as fnvs

# The configspace used to generate data
cfg_space = ConfigurationSpace({'int': (0, 5),
                                'full_int': (0, 5),
                                'float': (0.0, 5.0),
                                'cat': ['a', 'b', 'c', 'IMPUTE_HPIAD'],
                                'full_cat': ['a', 'b', 'c', 'IMPUTE_HPIAD'],
                                'const': 'IMPUTE_HPIAD',
                                'full_const': -1})
# The configspace as it should be after imputation
imp_space = ConfigurationSpace({'int': (-1, 5),
                                'full_int': (0, 5),
                                'float': (-1.0, 5.0),
                                'cat': ['a', 'b', 'c',
                                        'IMPUTE_HPIAD', '_IMPUTE_HPIAD'],
                                'full_cat': ['a', 'b', 'c', 'IMPUTE_HPIAD'],
                                'const': ['IMPUTE_HPIAD', '_IMPUTE_HPIAD']})
# The configspace as it should be for fanova
run_space = ConfigurationSpace({'int': (-1, 5),
                                'full_int': (0, 5),
                                'float': (-1.0, 5.0),
                                'cat': ['a', 'b', 'c',
                                        'IMPUTE_HPIAD', '_IMPUTE_HPIAD'],
                                'full_cat': ['a', 'b', 'c', 'IMPUTE_HPIAD']})


class FanovaTests(unittest.TestCase):

    def setUp(self):
        self.data = {}
        sample_size = 500

        for id in range(10):
            df = pd.DataFrame(cfg_space.sample_configuration(sample_size))
            df.index += id * sample_size
            df['value'] = np.random.rand(sample_size)
            df['ignore'] = pd.NA

            for p in cfg_space.keys():
                if 'full' not in p:
                    df[p] = df[p].map(lambda x: pd.NA if np.random.rand() < 0.1 else x)

            self.data[id] = df.convert_dtypes()

    def stub_impute(self):
        default = dict(cfg_space.get_default_configuration())
        imputed = {id: data.fillna(default).dropna(axis=1, how='any')
                   for id, data in self.data.items()}
        imputed = {id: data.drop(columns=data.columns[data.nunique() <= 1])
                   for id, data in imputed.items()}
        return imputed

    def cfg_space_check(self,
                        created: ConfigurationSpace,
                        correct: ConfigurationSpace) -> bool:
        # Check that all hyperparams are as they should be
        for param_name, correct_param in correct.items():
            auto_param = created[param_name]
            self.assertEqual(type(auto_param), type(correct_param))

            # We do not care about the order of categoricals
            if isinstance(auto_param, CategoricalHyperparameter):
                self.assertSetEqual(set(auto_param.choices),
                                    set(correct_param.choices))
            # Constants just have the same value
            elif isinstance(auto_param, Constant):
                self.assertEqual(auto_param.value, correct_param.value)
            # Numericals might not display the full range in the random data
            elif isinstance(auto_param, NumericalHyperparameter):
                self.assertGreaterEqual(auto_param.lower, correct_param.lower)
                self.assertLessEqual(auto_param.upper, correct_param.upper)
                self.assertGreaterEqual(auto_param.upper, auto_param.lower)

    def test_cfg_space(self):
        auto_cfg_space = fnvs.auto_configspace(self.data)
        self.assertIsInstance(auto_cfg_space, ConfigurationSpace)
        self.assertSetEqual(set(auto_cfg_space.keys()), set(cfg_space.keys()))

        self.cfg_space_check(auto_cfg_space, cfg_space)

    def test_filter(self):
        filter_space = ConfigurationSpace({'int': (0, 4),
                                           'full_int': (0, 5),
                                           'float': (1.0, 5.0),
                                           'cat': ['a', 'c', 'IMPUTE_HPIAD'],
                                           'full_cat': ['a', 'b', 'c',
                                                        'IMPUTE_HPIAD'],
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

        # Assert that all constant hyperparameters are gone
        for p in new_space.values():
            self.assertNotIsInstance(p, Constant)

        # Assert that the new configspace is correct
        self.cfg_space_check(new_space, imp_space)

    def test_bins(self):
        imputed = self.stub_impute()

        binned, new_cfg = fnvs.bin_numeric(imputed, cfg_space)
        all_binned = pd.concat(binned)

        # Test that all hyperparams still exist
        self.assertSetEqual(set(new_cfg.keys()), set(cfg_space.keys()))

        # Test that all numerical hyperparams became ordinal
        for p_name, param in new_cfg.items():
            if isinstance(cfg_space[p_name], NumericalHyperparameter):
                self.assertIsInstance(param, OrdinalHyperparameter)
                self.assertLessEqual(set(all_binned[p_name].unique()), set(param.sequence))
                self.assertLessEqual(set(param.sequence), set(range(32)))
            else:
                self.assertIsInstance(param, type(cfg_space[p_name]))


    def test_prepare(self):
        imputed = self.stub_impute()
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
        def stub_prepare(val):
            if val == -1:
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
        imputed = self.stub_impute()
        prepared = imputed[0].map(lambda x: stub_prepare(x))

        # Run fANOVA
        result = fnvs.run_fanova(prepared, run_space, n_pairs=3)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(set(result.keys()), set(run_space.keys()))
        self.assertEqual(len(result) - len(run_space), 3)


if __name__ == '__main__':
    unittest.main()
