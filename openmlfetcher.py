# TODO: only needed for testing
from os import makedirs
from os.path import exists

import pandas as pd

from openml import flows, study, evaluations, setups, exceptions


def fetch_flows() -> pd.DataFrame | None:
    """Fetch all flows on openml, in a dataframe indexed on flow ID, and
    with columns for the name and version (which even together are not
    unique), or None if no flows exist.
    """
    f = flows.list_flows(output_format='dataframe')
    if f is None or f.empty:
        return None
    return f.set_index('id')[['name', 'version']]


def fetch_suites() -> pd.DataFrame | None:
    """Fetch all suites on openml, in a dataframe indexed on suite ID, and
    with columns for the name (called 'alias'), or None if no flows exist.
    """
    suites = study.list_suites(output_format='dataframe')
    if suites is None or suites.empty:
        return None
    return suites.set_index('id')[['alias']]


def fetch_tasks(suite_id: int) -> list[int] | None:
    """Fetch the list of task IDs in the benchmark suite specified
    by suite_id. Returns None if the suite does not exist.
    """
    tasks = None

    try:
        tasks = study.get_suite(suite_id=suite_id).tasks
    except exceptions.OpenMLServerException:
        # TODO: we might want to tell the user in some way
        # that this suite does not exist
        pass

    return tasks


def fetch_runs(flow_id: int,
               task_id: int,
               max_runs: int | None = None) -> pd.DataFrame | None:
    """Fetch the hyperparameter setups and resulting evaluations
    for the algorithm with flow_id in th task with task_id, in a
    dataframe with index run_id and value and parameters in all
    separate columns. If specified, retrieve at most max_runs
    setup-evaluation combinations.
    """
    # First we check if there are even enough runs with this fast
    # function. This does not throw errors for invalid ids.
    evals = evaluations.list_evaluations(function='predictive_accuracy',
                                         tasks=[task_id],
                                         flows=[flow_id],
                                         output_format='dataframe',
                                         size=max_runs)
    if evals.empty:
        return None

    # Then we collect the associated setups with this slow function
    # In batches, because URLs otherwise become too long
    ids = evals.setup_id.drop_duplicates().values
    tot = len(ids)
    batches = []
    offset = 0
    batch_size = 250
    while offset < tot:
        batch = setups.list_setups(setup=ids[offset:(offset+batch_size)],
                                   output_format='dataframe')['parameters']
        batches.append(batch)
        offset += batch_size

    # Split the parameters into separate columns
    params = pd.concat(batches)
    params = params.map((lambda p_list: {p['parameter_name']: p['value']
                                         for p in p_list.values()}))
    params = pd.json_normalize(params).set_index(params.index)

    # Finally we match the evaluations with the normalised setups
    evals = evals.set_index('run_id')[['setup_id', 'value']]
    data = evals.join(params, on='setup_id').drop(columns=['setup_id'])

    return data


def coerce_types(data: pd.DataFrame) -> pd.DataFrame:
    """Coerce the types in data and return the resulting dataframe.
    All columns will be either numeric or string d_type.
    """
    p_num = data.map(pd.to_numeric, errors="coerce")
    p_cat = data.loc[:, p_num.isna().all()].astype('string')
    p_num[p_cat.columns] = p_cat

    return p_num


def export_csv(flow_id: int,
               suite_id: int,
               data: dict[int, pd.DataFrame]) -> None:  # pragma: no cover
    # TODO: this is just for current testing. Eventually this
    # will be sent to Dash components without creating a file.
    folder_name = f'./openml_f{flow_id}_s{suite_id}/'

    if not exists(folder_name):
        makedirs(folder_name)

    for (task, task_data) in data.items():
        task_data.to_csv(folder_name + f't{task}.csv')
