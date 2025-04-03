import numpy as np
import pandas as pd

from fanova import fANOVA
from ConfigSpace import ConfigurationSpace
from ConfigSpace import Constant
from ConfigSpace import CategoricalHyperparameter
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES


def auto_configspace(data: dict[int, pd.DataFrame]) -> ConfigurationSpace:
    """Create a configuration space to fit all hyperparameter setups in
    data, which should still contain the irrelevant 'value' column. The
    resulting configuration space will be as small as possible, will not
    contain NA values, and parameters that are NA in all data will not
    appear in the configuration space at all.
    """
    param_dict = {}

    for _, full_data in data.items():
        params_data = full_data.drop(columns=['value'])
        params_data = params_data.dropna(axis=1, how='all')
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
    """Filters data according to the configuration space cfg_space, and
    returns the data that fits. Columns in data not present as parameter
    in cfg_space are ignored, and NA values are always accepted.
    """
    result = {}

    for task, task_data in data.items():
        copy = task_data.copy(deep=True)
        valid = pd.Series([True for _ in range(len(copy))], index=copy.index)

        for param_name, param in cfg_space.items():
            valid_p = copy[param_name].map(lambda x:
                                           True if pd.isna(x)
                                           else param.legal_value(x))
            valid = (valid) & (valid_p)

        result[task] = copy[valid]

    return result


def impute_data(data: dict[int, pd.DataFrame],
                cfg_space: ConfigurationSpace) \
        -> tuple[dict[int, pd.DataFrame], ConfigurationSpace]:
    """Imputes the data with a value out of range. The range is specified
    by cfg_space, and we return the imputed data, as well as an extended
    configuration space that includes the imputed values. Columns containing
    only missing values are removed.
    """
    # The values to impute with
    impute_vals = {}
    # New configspace including imputed values
    cfg_dict = {}

    for param_name, param in cfg_space.items():
        # If a parameter has no missing values, skip it
        missing = False
        for task_data in data.values():
            missing |= task_data[param_name].isna().any()

        # Constant params become categorical by adding an impute value
        if isinstance(param, Constant):
            if missing:
                impute_vals[param_name] = 'IMPUTE_HPIAD'
                # Ensure impute value was not yet present
                while impute_vals[param_name] == param.value:
                    impute_vals[param_name] = '_' + impute_vals[param_name]
                cfg_dict[param_name] = [param.value, impute_vals[param_name]]
            else:
                cfg_dict[param_name] = param.value

        # Categorical params get an extra impute value
        elif isinstance(param, CategoricalHyperparameter):
            if missing:
                impute_vals[param_name] = 'IMPUTE_HPIAD'
                # Ensure impute value was not yet present
                while impute_vals[param_name] in param.choices:
                    impute_vals[param_name] = '_' + impute_vals[param_name]
                cfg_dict[param_name] = \
                    list(param.choices) + [impute_vals[param_name]]
            else:
                cfg_dict[param_name] = list(param.choices)

        # Numerical params are imputed with one below their lower bound
        else:
            if missing:
                impute_vals[param_name] = param.lower - 1
                cfg_dict[param_name] = (param.lower - 1, param.upper)
            else:
                cfg_dict[param_name] = (param.lower, param.upper)

    # The resulting data
    imputed_data = {}

    for task, task_data in data.items():
        imputed_data[task] = \
            task_data[['value'] + list(cfg_space.keys())].fillna(impute_vals)

    return imputed_data, ConfigurationSpace(cfg_dict)


def prepare_data(data: dict[int, pd.DataFrame],
                 cfg_space: ConfigurationSpace) -> dict[int, pd.DataFrame]:
    """Prepares the data for fANOVA. This includes rounding numeric data
    to a certain amount of decimal digits, and converting categorical and
    constant hyperparameters to numeric values. The data should already
    have been imputed.
    """
    res = {}

    for task, task_data in data.items():
        prep = task_data.apply(np.round, decimals=ROUND_PLACES)

        for param_name, param in cfg_space.items():
            if isinstance(param, CategoricalHyperparameter):
                prep[param_name] = \
                    prep[param_name].map((lambda option:
                                          param.choices.index(option)))
            elif isinstance(param, Constant):
                prep[param_name] = 0

        res[task] = prep.astype(np.float64)

    return res


def run_fanova(task_data: pd.DataFrame,
               cfg_space: ConfigurationSpace,
               min_runs: int = 0) -> dict[str, float]:
    """Run fANOVA on data for one task, which contains imputed and prepared
    setups and evals that fit in the configuration space cfg_space. If the
    task does not have at least min_runs runs, return None. Returns a dict
    with relative importance indexed by parameter name.
    """
    if len(task_data) < min_runs:
        return None

    X = task_data.drop(columns=['value'])
    Y = task_data.value.to_numpy()

    fnv = fANOVA(X, Y, config_space=cfg_space)

    result = {}
    index = -1

    for param_name, param in cfg_space.items():
        index += 1
        if isinstance(param, Constant):
            continue

        score = fnv.quantify_importance((index,))[(index,)]
        result[param_name] = score['individual importance']

    # TODO: pairwise marginals

    return result


def export_csv(flow_id: int,
               suite_id: int,
               results: pd.DataFrame) -> None: # pragma: no cover
    # TODO: this is just for current testing. Eventually this
    # will be sent to Dash components without creating a file.
    # The first column is index, so dont plot that!
    results.to_csv(f'fanova_f{flow_id}_s{suite_id}.csv')
