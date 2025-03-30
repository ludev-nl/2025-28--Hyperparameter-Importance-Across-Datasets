import numpy as np
import pandas as pd

from fanova import fANOVA
from ConfigSpace import ConfigurationSpace
from ConfigSpace import CategoricalHyperparameter
from ConfigSpace import Constant
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES


def auto_configspace(data: dict[int, pd.DataFrame]) -> ConfigurationSpace:
    param_dict = {}

    for _, full_data in data.items():
        params_data = full_data.drop(columns=['value'])
        params_data = params_data.loc[:, params_data.notna().any()]
        num_cols = params_data.select_dtypes(include=['number']).columns
        cat_cols = params_data.select_dtypes(exclude=['number']).columns

        # Min and max of numerical hyperparams
        for col in num_cols:
            min_val = params_data[col].min()
            max_val = params_data[col].max()
            if col not in param_dict.keys():
                param_dict[col] = (min_val, max_val)
            else:
                prev_min, prev_max = param_dict[col]
                param_dict[col] = (min(prev_min, min_val),
                                   max(prev_max, max_val))

        # Unique values of categorical hyperparams
        for col in cat_cols:
            unique_values = set(params_data[col].dropna().unique())
            if col not in param_dict.keys():
                param_dict[col] = unique_values
            else:
                param_dict[col] = set.union(param_dict[col], unique_values)

    # Find constant parameters, and convert sets to lists
    for param, range in param_dict.items():
        if isinstance(range, tuple) and range[0] == range[1]:
            param_dict[param] = range[0]
        elif isinstance(range, set):
            if len(range) == 1:
                param_dict[param] = range.pop()
            else:
                param_dict[param] = list(range)

    return ConfigurationSpace(space=param_dict)


def filter_data(data: dict[int, pd.DataFrame],
                cfg_space: ConfigurationSpace) -> dict[int, pd.DataFrame]:
    # TODO: unimplemented
    return data


def impute_data(data: dict[int, pd.DataFrame],
                cfg_space: ConfigurationSpace) \
        -> tuple[dict[int, pd.DataFrame], ConfigurationSpace]:
    # TODO: impute using some value out of range, instead of default
    # This should return a new configspace, that also includes the
    # imputed values.
    imputed_data = {}
    default = dict(cfg_space.get_default_configuration())

    for task, task_data in data.items():
        imputed_data[task] = \
            task_data.dropna(axis=1, how='all').fillna(default)

    return imputed_data, cfg_space


def prepare_data(data: dict[int, pd.DataFrame],
                 cfg_space: ConfigurationSpace) -> dict[int, pd.DataFrame]:
    res = {}

    for task, task_data in data.items():
        prep = task_data.apply(np.round, decimals=ROUND_PLACES)

        for param_name in cfg_space:
            param = cfg_space[param_name]
            if isinstance(param, CategoricalHyperparameter):
                prep[param_name] = \
                    prep[param_name].map((lambda option:
                                          param.choices.index(option)))
            elif isinstance(param, Constant):
                prep[param_name] = 0

        res[task] = prep

    return res


def run_fanova(data: dict[int, pd.DataFrame],
               cfg_space: ConfigurationSpace,
               min_runs: int) -> pd.DataFrame:
    results = {}

    for task, task_data in data.items():
        X = task_data.drop(columns=['value'])
        Y = task_data.value.to_numpy()

        if len(X) < min_runs:
            continue

        fnv = fANOVA(X, Y, config_space=cfg_space)

        result = {}
        index = -1

        for param in cfg_space:
            index += 1
            if isinstance(cfg_space[param], Constant):
                continue

            score = fnv.quantify_importance((index,))[(index,)]
            result[param] = score['individual importance']

        # TODO: pairwise marginals

        results[task] = result

    return pd.DataFrame.from_dict(results, orient='index')


def export_csv(flow_id: int,
               suite_id: int,
               results: pd.DataFrame) -> None:
    # TODO: this is just for current testing. Eventually this
    # will be sent to Dash components without creating a file.
    # The first column is index, so dont plot that!
    results.to_csv(f'fanova_f{flow_id}_s{suite_id}.csv')
