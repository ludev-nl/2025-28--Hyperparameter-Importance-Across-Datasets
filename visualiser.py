import pandas as pd
import plotly.graph_objects as go


def violinplot(fanova_results: pd.DataFrame,
               show: bool) -> go.Figure:
    fig = go.Figure()

    plot_data = fanova_results.dropna(axis=1)

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


def crit_diff_diagram(fanova_results: pd.DataFrame,
                      show: bool) -> go.Figure:
    # TODO: implement
    return None
