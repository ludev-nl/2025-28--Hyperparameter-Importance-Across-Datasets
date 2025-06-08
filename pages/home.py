import dash
from dash import html
import dash_bootstrap_components as dbc

# Registers this file as the homepage
dash.register_page(__name__, path="/")

# Layout for the homepage
layout = dbc.Container([
    # Welcome header
    dbc.Row(
        dbc.Col(
            html.H1("Welcome to the fANOVA Web App"),
            width={"size": 6, "offset": 3}
        ),
        className="my-4"
    ),
    # Brief explanation of the app
    dbc.Row(
        dbc.Col(
            html.P(
                "The fANOVA Web App is designed to help you analyze the"
                "importance of hyperparameters across various machine l"
                "earning tasks using functional ANOVA. In this application, yo"
                "u can fetch evaluation runs from OpenML, filter and configure"
                " hyperparameter settings, run the analysis, and visualize the"
                " results. Navigate using the menu on the left to access diffe"
                "rent sections of the app."
            ),
            width={"size": 6, "offset": 3}
        ),
        className="mb-4"
    ),
    # Instructions for how the webapp works (fanova and openML)
    dbc.Row(
        dbc.Col(
            [
                html.H3("How To Use The Web App"),
                html.Ol([
                    html.Li("Go to the \"Experiment\" tab to select the flows an"
                            "d suites you wish to analyze."),
                    html.Li("Configure your hyperparameter setting and filter "
                            "the options as needed."),
                    html.Li("Click the \"Run Fanova\" button to execute the hype"
                            "rparameter importance analysis."),
                    html.Li("Review the visualizations on the results page to "
                            "understand which parameters impact performance."),
                    html.Li("Download CSV files of the results for further inv"
                            "estigation if required.")
                ])
            ],
            width={"size": 6, "offset": 3}
        ),
        className="mb-4"
    ),
    # Link to our GitHub repository
    dbc.Row(
        dbc.Col(
            [
                html.H3("Check Out Our Git"),
                html.A(
                    dbc.Button(
                        "View GitHub Repository",
                        color="primary",
                        ),
                    href=("https://github.com/ludev-nl/2025-28--Hyperparameter"
                          "-Importance-Across-Datasets.gitc"),
                    target="_blank"
                )
            ],
            width={"size": 6, "offset": 3}
        )
    )
], fluid=True)
