import numpy as np
import pandas as pd

from fanova import fANOVA
from ConfigSpace import ConfigurationSpace
from ConfigSpace import Constant
from ConfigSpace import CategoricalHyperparameter, OrdinalHyperparameter
from ConfigSpace.hyperparameters import NumericalHyperparameter
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES


def auto_configspace(data: dict[int, pd.DataFrame]) -> ConfigurationSpace:
    """Create a configuration space to fit all hyperparameter setups in
    data, which should still contain the irrelevant 'value' column. The
    resulting configuration space will be as small as possible, will not
    contain NA values, and parameters that are NA in all data will not
    appear in the configuration space at all.
    """
    full_data = pd.concat(data)

    param_dict: dict[str,
                     tuple[int, int]
                     | tuple[float, float]
                     | list[int | float | str]
                     | int
                     | float
                     | str] = {}

    params_data = full_data.drop(columns=['value'], errors='ignore')
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
    only missing values are removed. Constant columns with missing values
    become categorical, while those without missing values are discarded
    from the data.
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
        incomplete = False
        for task_data in data.values():
            incomplete |= task_data[param_name].isna().any()

        # Constant params become categorical by adding an impute value
        # Truly constant ones are no longer relevant
        if isinstance(param, Constant):
            if incomplete:
                impute_val = 'IMPUTE_HPIAD'
                # Ensure impute value was not yet present
                while impute_val == param.value:
                    impute_val = '_' + impute_val
                impute_vals[param_name] = impute_val
                cfg_dict[param_name] = [param.value, impute_val]

        # Categorical params get an extra impute value
        elif isinstance(param, CategoricalHyperparameter):
            if incomplete:
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
            if incomplete:
                impute_vals[param_name] = param.lower - 1
                cfg_dict[param_name] = (param.lower - 1, param.upper)
            else:
                cfg_dict[param_name] = (param.lower, param.upper)

    # The resulting data
    imputed_data = {}

    # The resulting ConfigSpace
    imputed_cfg = ConfigurationSpace(cfg_dict)

    for task, task_data in data.items():
        imputed_data[task] = \
            task_data[['value'] + list(imputed_cfg.keys())].fillna(impute_vals)

    return imputed_data, imputed_cfg


def bin_numeric(data: dict[int, pd.DataFrame],
                cfg_space: ConfigurationSpace,
                max_bins: int = 32) \
        -> tuple[dict[int, pd.DataFrame], ConfigurationSpace]:
    """Bins all numerical data in at most max_bins bins, up to 128 bins. If
    the amount of unique values is less than the amount of bins, we take the
    amount of unique values as bin count. The values are binned such that all
    bins contain roughly the same amount of values, automatically taking
    non-uniform distributions into account. In the returned configuration
    space all numerical hyperparameters are replaced by ordinal ones.
    """
    res = {}

    num = [p_name for p_name in cfg_space.keys()
           if isinstance(cfg_space[p_name], NumericalHyperparameter)]

    all_data = pd.concat([task_data[num] for task_data in data.values()])
    bounds = {}
    ordinal_params = []

    for p_name in num:
        n_bins = min(128, max_bins, all_data[p_name].nunique())
        sorted = np.sort(all_data[p_name])
        bounds_index = np.linspace(0, len(sorted)-1, n_bins)[1:].astype('int')
        bounds[p_name] = sorted[bounds_index]
        ordinal_params.append(OrdinalHyperparameter(p_name,
                                                    range(n_bins),
                                                    default_value=n_bins//2))

    non_num = [p for p in cfg_space.values()
               if not isinstance(p, NumericalHyperparameter)]
    cfg_space = ConfigurationSpace(space=non_num)
    cfg_space.add(ordinal_params)

    for task, task_data in data.items():
        for p_name, boundaries in bounds.items():
            task_data[p_name] = np.digitize(task_data[p_name], boundaries)

        res[task] = task_data

    return res, cfg_space


def prepare_data(data: dict[int, pd.DataFrame],
                 cfg_space: ConfigurationSpace) -> dict[int, pd.DataFrame]:
    """Prepares the data for fANOVA. This includes rounding numeric data
    to a certain amount of decimal digits, and converting categorical and
    constant hyperparameters to numeric values. The data should already
    have been imputed.
    """
    res = {}

    for task, task_data in data.items():
        for param_name, param in cfg_space.items():
            if isinstance(param, CategoricalHyperparameter):
                task_data[param_name] = \
                    task_data[param_name].map((lambda option:
                                               param.choices.index(option)))
            elif isinstance(param, Constant):
                task_data[param_name] = 0

        res[task] = task_data.astype(np.float64)\
                             .apply(np.round, decimals=ROUND_PLACES)

    return res


def run_fanova(task_data: pd.DataFrame,
               cfg_space: ConfigurationSpace,
               min_runs: int = 1,
               n_pairs: int = 0) -> dict[str, float] | None:
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

    for index, param_name in enumerate(cfg_space.keys()):
        score = fnv.quantify_importance((index,))[(index,)]
        result[param_name] = score['individual importance']

    if n_pairs > 0:
        pairs = fnv.get_most_important_pairwise_marginals(n=n_pairs)

        result.update({name[0]+'_-_'+name[1]: importance
                       for name, importance in pairs.items()})

    return result


def export_csv(flow_id: int,
               suite_id: int,
               results: pd.DataFrame) -> None:  # pragma: no cover
    # TODO: this is just for current testing. Eventually this
    # will be sent to Dash components without creating a file.
    # The first column is index, so dont plot that!
    results.to_csv(f'fanova_f{flow_id}_s{suite_id}_b.csv')
