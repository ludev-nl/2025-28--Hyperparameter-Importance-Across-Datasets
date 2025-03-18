import pandas as pd
import numpy as np
import plotly.graph_objects as go
import Orange


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
        fig = go.Figure()

        plot_data = self.fanova_results.dropna(axis=1)
        if plot_data.shape[1] == 0:
            print("No columns left after dropping NaN columns")
            return None
        
        hyperparameters = list(plot_data.columns)
        ranks = np.argsort(np.argsort(-plot_data.to_numpy(), axis=1), axis=1) + 1
        mean_ranks = np.mean(ranks, axis=0)

        # Caluclate critical distance
        from scipy.stats import friedmanchisquare
        from Orange.evaluation.scoring import compute_CD
        _, p_value = friedmanchisquare(*plot_data.to_numpy().T)
        cd = compute_CD(mean_ranks, plot_data.shape[0]) if p_value < 0.05 else 0

        # Plot average ranks for every hyperparameter
        for i, (hp, rank) in enumerate(zip(hyperparameters, mean_ranks)):
            fig.add_trace(go.Scatter(
                x=[rank],
                y=[hp],
                mode='markers',
                name=hp,
                marker=dict(size=10)
            ))

        # Add critical distance line
        fig.add_shape(
            type="line",
            x0=min(mean_ranks) - cd,
            y0=0,
            x1=max(mean_ranks) + cd,
            y1=0,
            line=dict(color="red", width=2, dash="dash"),
        )

        # Update layout
        fig.update_layout(
            title="Critical Distance Diagram",
            xaxis_title="Average Rank",
            yaxis_title="Hyperparameters",
            showlegend=False,
            yaxis=dict(autorange="reversed")
        )

        if show:
            fig.show()

        return fig
