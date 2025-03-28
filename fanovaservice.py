import numpy as np
import pandas as pd

from fanova import fANOVA
from ConfigSpace import ConfigurationSpace
from ConfigSpace import CategoricalHyperparameter
from ConfigSpace import Constant
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES


class FanovaService:
    raw_data: dict[int, pd.DataFrame] = {}
    auto_cfg_space: ConfigurationSpace = None
    user_cfg_space: ConfigurationSpace = None
    results: pd.DataFrame = None

    def __init__(self, raw_data: dict[int, pd.DataFrame]) -> None:
        self.raw_data = raw_data
        self.auto_configspace()
        self.impute_data()

    def auto_configspace(self) -> ConfigurationSpace:
        # TODO: create one configspace for all tasks
        # Use select_dtypes to split num (float, int) and cat (str)

        # TODO: no more one hot encoding once configspace is implemented

        param_dict = {}
        first = True

        for _, raw_data in self.raw_data.items():
            data = raw_data.drop(columns=['value'])
            num_cols = data.select_dtypes(include=['number']).columns
            cat_cols = data.select_dtypes(exclude=['number']).columns

            # Min and max of numerical hyperparams
            for col in num_cols:
                min_val = data[col].min()
                max_val = data[col].max()
                if first:
                    param_dict[col] = (min_val, max_val)
                else:
                    prev_min, prev_max = param_dict[col]
                    param_dict[col] = (min(prev_min, min_val),
                                       max(prev_max, max_val))

            # Unique values of categorical hyperparams
            for col in cat_cols:
                unique_values = set(data[col].dropna().unique())
                if first:
                    param_dict[col] = unique_values
                else:
                    param_dict[col] = set.union(param_dict[col], unique_values)

            first = False

        # Find constant parameters, and convert sets to lists
        for param, range in param_dict.items():
            if isinstance(range, tuple) and range[0] == range[1]:
                param_dict[param] = range[0]
            elif isinstance(range, set):
                if len(range) == 1:
                    param_dict[param] = range.pop()
                else:
                    param_dict[param] = list(range)

        cs = ConfigurationSpace(space=param_dict)

        self.auto_cfg_space = cs
        return cs

    def impute_data(self):
        # TODO: impute using some value out of range, instead of default
        # This should affect the configspace given to fanova, but not the
        # one for the user

        imputed_data = {}
        default = dict(self.auto_cfg_space.get_default_configuration())
        for (task, data) in self.raw_data.items():
            imputed_data[task] = data.fillna(default)

        self.raw_data = imputed_data

        pass

    def filter_data(self, task_id: int) -> tuple[pd.DataFrame, np.ndarray]:
        # Extract the relevant data
        data = self.raw_data[task_id]
        X = data.drop(labels="value", axis=1)
        Y = data.value.to_numpy()

        # TODO: filter X (and Y) using user configspace if applicable

        return X, Y

    def transform_for_fanova(self, data: pd.DataFrame) -> pd.DataFrame:
        res = data.apply(np.round, decimals=ROUND_PLACES)
        for param_name in self.auto_cfg_space:
            param = self.auto_cfg_space[param_name]
            if isinstance(param, CategoricalHyperparameter):
                res[param_name] = \
                    res[param_name].map((lambda option:
                                         param.choices.index(option)))
            elif isinstance(param, Constant):
                res[param_name] = 0
        return res

    def run_fanova(self, min_runs: int) -> pd.DataFrame:
        results = {}
        for task in self.raw_data.keys():
            X, Y = self.filter_data(task)

            if len(X) < min_runs:
                continue

            X = self.transform_for_fanova(X)
            # TODO: use correct configspace, including imputed vals
            fnv = fANOVA(X, Y, config_space=self.auto_cfg_space)

            result = {}
            index = -1
            for param in self.auto_cfg_space:
                index += 1
                if isinstance(self.auto_cfg_space[param], Constant):
                    continue
                score = fnv.quantify_importance((index,))[(index,)]
                result[param] = score['individual importance']

            # TODO: most important pairwise marginals

            results[task] = result

        self.results = pd.DataFrame.from_dict(results, orient='index')

        return self.results

    def export_csv(self, flow_id, suite_id):
        # TODO: this is just for current testing. Eventually this
        # will be sent to Dash components without creating a file.
        # The first column is index, so dont plot that!
        self.results.to_csv(f'fanova_f{flow_id}_s{suite_id}.csv')
