# TODO: only needed for testing
from os import makedirs
from os.path import exists

import pandas as pd

from openml import study, evaluations, setups, exceptions


class OpenMLFetcher:
    flow_id: int = None
    suite_id: int = None
    tasks: list[int] = []
    results: dict[int, pd.DataFrame] = {}

    def __init__(self, flow_id: int, suite_id: int) -> None:
        self.flow_id = flow_id
        self.suite_id = suite_id

    def fetch_tasks(self) -> list[int]:
        try:
            self.tasks = study.get_suite(suite_id=self.suite_id).tasks
        except exceptions.OpenMLServerException:
            # TODO: we might want to tell the user in some way
            # that this suite does not exist
            return None

        return self.tasks

    def fetch_runs(self, task_id: int, max_runs: int = None) -> pd.DataFrame:
        # First we check if there are even enough runs with this fast
        # function. This does not throw errors for invalid ids.
        evals = evaluations.list_evaluations(function='predictive_accuracy',
                                             tasks=[task_id],
                                             flows=[self.flow_id],
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
                                       output_format='dataframe').parameters
            batches.append(batch)
            offset += batch_size

        # Split the parameters into separate columns
        params = pd.concat(batches)
        params = params.map((lambda p_list: {p['parameter_name']: p['value']
                                             for p in p_list.values()}))
        params = pd.json_normalize(params).set_index(params.index)

        # Cast the columns to appropriate types
        p_num = params.map(pd.to_numeric, errors="coerce")
        p_num = p_num.dropna(axis=1, how='all')
        p_cat = params.drop(p_num.columns, axis=1).astype('string')
        params = p_num.join(p_cat)

        # Finally we match the evaluations with the normalised setups
        data = evals.set_index('setup_id')[['value']].join(params)
        self.results[task_id] = data

        return data

    def export_csv(self):
        # TODO: this is just for current testing. Eventually this
        # will be sent to Dash components without creating a file.
        folder_name = f'./openml_f{self.flow_id}_s{self.suite_id}/'

        if not exists(folder_name):
            makedirs(folder_name)

        for (task, data) in self.results.items():
            data.to_csv(folder_name + f't{task}.csv')
