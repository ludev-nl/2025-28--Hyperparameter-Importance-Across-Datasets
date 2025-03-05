import pandas as pd
# TODO: matplotlib should be replaced by plotly
import matplotlib.pyplot as plt
from matplotlib.collections import Collection


class Visualiser:
    fanova_results: pd.DataFrame = None

    def __init__(self, fanova_results: pd.DataFrame) -> None:
        self.fanova_results = fanova_results

    def violinplot(self, show: bool) -> dict[str, Collection]:
        # TODO: plotly
        plot = plt.violinplot(self.fanova_results, showmedians=True)
        if show:
            plt.show()

        return plot

    def crit_diff_diagram(self, show: bool) -> dict[str, Collection]:
        # TODO: implement
        return None
