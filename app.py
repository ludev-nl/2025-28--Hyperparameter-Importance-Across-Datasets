import dash
from dash import Input, Output, dcc, html
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("fANOVA", className="display-4"),
        html.Hr(),
        html.P("Hyperparameter Importance Analysis", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Experiment Management", href="/experiment", active="exact"),
                dbc.NavLink("Results Display", href="/results_display", active="exact"),
                dbc.NavLink("Results Loading", href="/results_loading", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(dash.page_container, style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

if __name__ == "__main__":
    app.run(port=8888)

