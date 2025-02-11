import openml as oml
import numpy as np
import pandas as pd
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES

# Example settings
flow_id = 5527
openml100 = 99

def get_tasks(suite_id):
    # Get the relevant Suite object
    suite = oml.study.get_suite(suite_id=suite_id)
    # Extract the tasks
    return suite.tasks

def get_data(tasks, flow_id):
    # Get all runs (incl setups and evaluations) of the given flow on any of the given tasks
    evals = oml.evaluations.list_evaluations_setups(function="predictive_accuracy",
                                                    size=1000,
                                                    tasks=tasks,
                                                    flows=[flow_id],
                                                    output_format="dataframe")
    # Extract the hyperparameters and results
    params = pd.json_normalize(evals["parameters"])
    results = evals["value"]
    return params, results

def process_params(params):
    # Remove constant columns
    params = params[params.columns[params.nunique() > 1]]

    # Split params into numerical and categorical for preprocessing
    p_num = params.apply(pd.to_numeric, errors="coerce", downcast="float")
    p_num = p_num[p_num.columns[p_num.nunique() > 1]]
    p_cat = params.drop(p_num.columns, axis=1)

    # Fill in missing features (as in the paper)
    # Categorical features: most common category
    p_cat = p_cat.fillna(p_cat.mode(axis=0).iloc[0])
    # Numerical features: median
    p_num = p_num.fillna(p_num.median(axis=0))

    # Categorical features are one-hot encoded
    p_cat = pd.get_dummies(p_cat, dtype=float)

    # Merge params
    params = p_num.join(p_cat)

    # If we do not give fANOVA an explicit ConfigSpace, we need to
    # round the data, as it will otherwise infer bounds, round those,
    # and complain that the unrounded data is out of bounds.
    params = params.apply(np.round, decimals=ROUND_PLACES, axis=1)

    return params

# Now we determine the X and Y that fANOVA expects
tasks = get_tasks(openml100)
X, Y = get_data(tasks, flow_id)
X = process_params(X)
