import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib import rcParams
from io import BytesIO
import base64
import scipy.stats as ss
import scikit_posthocs as sp
import numpy as np


def violinplot(fanova_results: pd.DataFrame,
               show: bool) -> go.Figure:
    """Create a violin plot of the data in fanova_results, and
    show the plot iff show == True.
    """
    fig = go.Figure()

    plot_data = fanova_results.dropna(axis=1, how='all')

    if plot_data.shape[1] == 0:
        print("no columns left after dropping NaN columns")
        return fig

    hyperparameters = list(plot_data.columns)

    for hp in hyperparameters:
        name = hp[0].upper() + hp[1:].replace('_', ' ')
        fig.add_trace(go.Violin(x=[name]*(plot_data.shape[0]),
                                y=plot_data[hp].tolist(),
                                name=name,
                                box_visible=True,
                                meanline_visible=True,
                                spanmode='hard'))

    fig.update_layout(title="Variance Contribution of Hyperparameters",
                      yaxis_title="Variance Contribution",
                      xaxis_tickangle=-45)

    if show:
        fig.show()

    return fig


def crit_diff_diagram(fanova_results: pd.DataFrame) -> str:
    """Create a critical difference diagram of the data in
    fanova_results, and show the plot iff show == True.
    """
    fanova_results.index = list(range(len(fanova_results)))
    dict_data = {val: np.array(list(fanova_results[val])) for val in fanova_results.columns}
    data2 = (
      pd.DataFrame(fanova_results)
      .rename_axis('cv_fold')
      .melt(
          var_name='estimator',
          value_name='score',
          ignore_index=False,
      )
      .reset_index()
    )

    avg_rank = data2.groupby('cv_fold').score.rank().groupby(data2.estimator).mean()
    ss.friedmanchisquare(*dict_data.values())
    test_results = sp.posthoc_conover_friedman(
        data2,
        melted=True,
        block_col='cv_fold',
        block_id_col='cv_fold',
        group_col='estimator',
        y_col='score',
    )
    rcParams.update({'figure.autolayout': True})
    fig,ax = plt.subplots(figsize=[8,4])
    sp.critical_difference_diagram(avg_rank, test_results,ax=ax)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    fig_data = base64.b64encode(buf.getbuffer()).decode("utf8")
    buf.close()
    fig_bar_matplotlib = f'data:image/png;base64,{fig_data}'

    return fig_bar_matplotlib
