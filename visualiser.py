import pandas as pd
import plotly.graph_objects as go


class Visualiser:
    fanova_results: pd.DataFrame = None

    def __init__(self, fanova_results: pd.DataFrame) -> None:
        self.fanova_results = fanova_results

    def violinplot(self, show: bool) -> go.Figure:
        # TODO: plotly
        fig = go.Figure()

        # TODO: I think missing values should just be ignored,
        # so only the remaining values should be used
        # drop columns containing null values
        plot_data = self.fanova_results.dropna(axis=1)

        if plot_data.shape[1] == 0:
            print("no columns left after dropping NaN columns")
            return fig

        hyperparameters = list(plot_data.columns)

        for hp in hyperparameters:
            fig.add_trace(go.Violin(x=[hp]*(plot_data.shape[0]),
                                    y=plot_data[hp].tolist(),
                                    name=hp,
                                    box_visible=True,
                                    meanline_visible=True))

        fig.update_layout(title="Variance Contribution of Hyperparameters",
                          yaxis_title="Variance Contribution",
                          xaxis_tickangle=-45)

        if show:
            fig.show()

        return fig

    def crit_diff_diagram(self, show: bool) -> go.Figure:
        # TODO: implement
        return None
