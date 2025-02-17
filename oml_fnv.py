import fanova as fnv
import openml as oml
import numpy as np
import pandas as pd
from ConfigSpace.hyperparameters.hp_components import ROUND_PLACES

def get_data(task):
    # First we check if there are even enough runs with this fast function
    evals = oml.evaluations.list_evaluations(function='predictive_accuracy',
                                             tasks=[task],
                                             flows=[flow_id],
                                             output_format='dataframe')
    if len(evals) < min_runs:
        return None
    ids = evals.setup_id.drop_duplicates().values
    tot = len(ids)

    # Then we collect the associated setups with this slow function
    # In batches, because URLs otherwise become too long
    batches = []
    offset = 0
    batch_size = 250
    while offset < tot:
        batch = oml.setups.list_setups(setup=ids[offset:(offset+batch_size)],
                                       output_format='dataframe').parameters
        batches.append(batch)
        offset += batch_size

    # Then we match the evaluations with the setups
    params = pd.concat(batches)
    data = evals.join(params, on='setup_id')

    return data

def process_params(params):
    # Extract the relevant information
    params = params.map((lambda p_list: {p['parameter_name']: p['value'] for p in p_list.values()}))
    params = pd.json_normalize(params)

    # Remove constant columns
    params = params[params.columns[params.nunique() > 1]]

    # Split params into numerical and categorical for preprocessing
    p_num = params.map(pd.to_numeric, errors="coerce", downcast="float")
    p_num = p_num[p_num.columns[p_num.nunique() > 1]]
    p_cat = params.drop(p_num.columns, axis=1)

    # Fill in missing features
    # TODO: this should not be necessary. Maybe issue warning / discard entry instead?
    # Categorical features: most common category
    p_cat = p_cat.fillna(p_cat.mode(axis=0).iloc[0])
    # Numerical features: median
    p_num = p_num.fillna(p_num.median(axis=0))

    # Categorical features are one-hot encoded
    # TODO: actually we should be creating a ConfigSpace with categorical params
    p_cat = pd.get_dummies(p_cat, dtype=float)

    # Merge params
    params = p_num.join(p_cat)

    # If we do not give fANOVA an explicit ConfigSpace, we need to
    # round the data, as it will otherwise infer bounds, round those,
    # and complain that the unrounded data is out of bounds.
    # TODO: possibly not necessary if we use config_spaces
    params = params.apply(np.round, decimals=ROUND_PLACES, axis=1)

    return params

# Example settings
flow_id = 6969
openml100 = 99
min_runs = 500

# Start of the program
tasks = oml.study.get_suite(suite_id=openml100).tasks
results = {}

num = 1
tot = len(tasks)
for task in tasks:
    print(f'Task {task} ({num}/{tot})')
    num += 1

    # We continue if there were not enough data points
    data = get_data(task)
    if data is None:
        continue

    # Extract the relevant data
    X = process_params(data.parameters)
    Y = data.value.to_numpy()

    # Fit the fanova model
    f = fnv.fANOVA(X, Y)

    # Extract the marginal variances
    # TODO: perhaps also pairwise?
    index = 0
    result = {}
    for param in X.columns.values:
        result[param] = f.quantify_importance((index,))[(index,)]['individual importance']
        print(f'- {param}: {result[param]}')
        index += 1

    # Save the result
    results[task] = result

df = pd.DataFrame.from_dict(results, orient='index')
df.to_csv(f'results-f{flow_id}-s{openml100}.csv', index=False)
