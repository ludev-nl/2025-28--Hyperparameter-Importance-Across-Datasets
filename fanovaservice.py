import numpy as np
import pandas as pd

from fanova import fANOVA
from ConfigSpace import ConfigurationSpace
from ConfigSpace import Constant
from ConfigSpace import CategoricalHyperparameter
from ConfigSpace.hyperparameters import NumericalHyperparameter
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES


def auto_configspace(data: dict[int, pd.DataFrame]) -> ConfigurationSpace:
    """Create a configuration space to fit all hyperparameter setups in
    data, which should still contain the irrelevant 'value' column. The
    resulting configuration space will be as small as possible, will not
    contain NA values, and parameters that are NA in all data will not
    appear in the configuration space at all.
    """
    if len(data) == 0:
        return ConfigurationSpace()

    full_data = pd.concat(data)

    param_dict: dict[str,
                     tuple[int, int]
                     | tuple[float, float]
                     | list[int | float | str]
                     | int
                     | float
                     | str] = {}

    params_data = full_data.drop(columns=['value'])
    params_data = params_data.dropna(axis=1, how='all')
    num_cols = params_data.select_dtypes(include=['number']).columns
    cat_cols = params_data.select_dtypes(exclude=['number']).columns

    # Min and max of numerical hyperparams
    for col in num_cols:
        min_val = params_data[col].min()
        max_val = params_data[col].max()
        if min_val == max_val:
            param_dict[col] = min_val
        else:
            param_dict[col] = (min_val, max_val)

    # Unique values of categorical hyperparams
    for col in cat_cols:
        unique_values = list(params_data[col].dropna().unique())
        if len(unique_values) == 1:
            param_dict[col] = unique_values[0]
        else:
            param_dict[col] = unique_values

    return ConfigurationSpace(space=param_dict)


def filter_data(data: dict[int, pd.DataFrame],
                cfg_space: ConfigurationSpace) -> dict[int, pd.DataFrame]:
    """Filters data according to the configuration space cfg_space, and
    returns the data that fits. Columns in data not present as parameter
    in cfg_space are ignored, and NA values are always accepted. If a parameter
    is omitted from the cfg_space, all values are accepted for that parameter.
    """
    result = {}

    for task, task_data in data.items():
        valid = pd.Series([True for _ in range(len(task_data))],
                          index=task_data.index)

        for param_name, param in cfg_space.items():
            valid_p = task_data[param_name].map(lambda x:
                                                True if pd.isna(x)
                                                else param.legal_value(x))
            valid &= valid_p

        result[task] = task_data[valid]

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
    impute_vals: dict[str, int | float | str] = {}
    # New configspace including imputed values
    cfg_dict: dict[str,
                   tuple[int, int]
                   | tuple[float, float]
                   | list[object]
                   | set[object]
                   | int
                   | float
                   | str] = {}

    for param_name, param in cfg_space.items():
        # If a parameter has no missing values, skip it
        missing = False
        for task_data in data.values():
            missing |= task_data[param_name].isna().any()

        # Constant params become categorical by adding an impute value
        # TODO: maybe they should remain constant?
        if isinstance(param, Constant):
            if missing:
                impute_val = 'IMPUTE_HPIAD'
                # Ensure impute value was not yet present
                while impute_val == param.value:
                    impute_val = '_' + impute_val
                impute_vals[param_name] = impute_val
                cfg_dict[param_name] = [param.value, impute_val]
            else:
                cfg_dict[param_name] = param.value

        # Categorical params get an extra impute value
        elif isinstance(param, CategoricalHyperparameter):
            if missing:
                impute_val = 'IMPUTE_HPIAD'
                # Ensure impute value was not yet present
                while impute_val in param.choices:
                    impute_val = '_' + impute_val
                impute_vals[param_name] = impute_val
                cfg_dict[param_name] = \
                    list(param.choices) + [impute_val]
            else:
                cfg_dict[param_name] = list(param.choices)

        # Numerical params are imputed with one below their lower bound
        elif isinstance(param, NumericalHyperparameter):
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
               min_runs: int = 0) -> dict[str, float] | None:
    """Run fANOVA on data for one task, which contains imputed and prepared
    setups and evals that fit in the configuration space cfg_space. If the
    task does not have at least min_runs runs, return None. Returns a dict
    with relative importance indexed by parameter name.
    """
    if len(task_data) <= 0 or len(task_data) < min_runs:
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
               results: pd.DataFrame) -> None:  # pragma: no cover
    # TODO: this is just for current testing. Eventually this
    # will be sent to Dash components without creating a file.
    # The first column is index, so dont plot that!
    results.to_csv(f'fanova_f{flow_id}_s{suite_id}.csv')
