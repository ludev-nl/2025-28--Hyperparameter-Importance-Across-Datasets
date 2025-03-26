import numpy as np
import pandas as pd

from fanova import fANOVA
from ConfigSpace import ConfigurationSpace 
from  ConfigSpace import UniformFloatHyperparameter
from ConfigSpace import CategoricalHyperparameter
# TODO: might be unnecessary if we implement configspace
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

        cs = ConfigurationSpace()

        col_temp = {}
        task_temp = {}
        unique_temp = []
        first = 1
        for task, unfilered_data in self.raw_data.items():
            data = unfilered_data.drop(columns=['value'], errors='ignore') 
            num_cols = data.select_dtypes(include=['number']).columns
            cat_cols = data.select_dtypes(exclude=['number']).columns

            #ad numerical hyperparameters
            for col in num_cols:
                min_val = data[col].min()
                max_val = data[col].max()

                if (first == 1):
                    col_temp[col] = (min_val, max_val)
                else: 
                    prev_min, prev_max = col_temp[col]
                    col_temp[col] = (min(prev_min, min_val), max(prev_max, max_val))
                # if (first == 1):
                #     col_temp[col] = (min_val, max_val)
                #     print(col_temp[col][0])
                # elif (min_val < col_temp[col][0] and max_val > col_temp[col][1]): 
                #     col_temp[col] = (min_val, max_val)
                # elif (min_val < col_temp[col][0] and max_val < col_temp[col][1]):
                #     col_temp[col] = (min_val, col_temp[col][1])
                # elif (min_val > col_temp[col][0] and max_val > col_temp[col][1]):
                #     col_temp[col] = (col_temp[col][0], max_val)
                # elif (min_val > col_temp[col][0] and max_val < col_temp[col][1]):
                #     col_temp[col] = (col_temp[col][0], col_temp[col][1])
            first = 0 
            
            #add categorical hyperparameters
            for col in cat_cols:
                unique_values = list(data[col].dropna().unique())  #drop NaN values
                unique_temp = unique_temp + unique_values
                # if unique_values:
                #     cs.add(CategoricalHyperparameter(col, choices=unique_values))
        
        for col, (min_val, max_val) in col_temp.items():
            if (min_val != max_val):
                cs.add_hyperparameter(UniformFloatHyperparameter(col, lower=min_val, upper=max_val))


        unique_values = list(set(unique_temp))  #drop NaN values
        cs.add(CategoricalHyperparameter(col, choices=unique_values))

        self.auto_cfg_space = cs 
        return cs
        # one_hot_data = {}
        # for (task, data) in self.raw_data.items():
        #     cat = data.select_dtypes(exclude='number').columns
        #     one_hot_data[task] = pd.get_dummies(data, columns=cat, dtype=float)
        # self.raw_data = one_hot_data

        # return self.auto_cfg_space

    def impute_data(self):
        # TODO: impute using fillna with some value out of range
        # (see configspace for range). Also think about how this
        # should affect the configspace given to fanova.

        imputed_data = {}
        for (task, data) in self.raw_data.items():
            imputed_data[task] = data.fillna(0)

        self.raw_data = imputed_data

        pass

    def filter_data(self, task_id: int) -> tuple[pd.DataFrame, np.ndarray]:
        # Extract the relevant data
        data = self.raw_data[task_id]
        X = data.drop(labels="value", axis=1)
        Y = data.value.to_numpy()

        # TODO: filter X (and Y) using user configspace if applicable

        return X, Y

    def run_fanova(self, min_runs: int) -> pd.DataFrame:
        results = {}
        for task in self.raw_data.keys():
            X, Y = self.filter_data(task)

            if len(X) < min_runs:
                continue

            # TODO: use correct configspace
            X = X.apply(np.round, decimals=ROUND_PLACES, axis=1)
            X = X[X.columns[X.nunique() > 1]]
            fnv = fANOVA(X, Y)

            result = {}
            index = 0
            for param in X.columns.values:
                score = fnv.quantify_importance((index,))[(index,)]
                result[param] = score['individual importance']
                index += 1

            # TODO: most important pairwise marginals

            results[task] = result

        self.results = pd.DataFrame.from_dict(results, orient='index')

        return self.results

    def export_csv(self, flow_id, suite_id):
        # TODO: this is just for current testing. Eventually this
        # will be sent to Dash components without creating a file.
        # The first column is index, so dont plot that!
        self.results.to_csv(f'fanova_f{flow_id}_s{suite_id}.csv')
