import dash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

dash.register_page(__name__, path='/experiment')

flow_content = html.Div(html.H1("This the flow tab"))

config_content = html.Div(html.H1("This the config tab"))

layout = dbc.Container(
    [
        html.H1("Experiment Setup"),
        dcc.Markdown("explanation text"),
        dbc.Button(
            "Run Fanova",
            color="primary",
            id="button",
            className="mb-3",
        ),
        dbc.Tabs(
            [
                dbc.Tab(flow_content, label="Flow and Suite Selection", tab_id="flow"),
                dbc.Tab(config_content, label="Configuration Space", tab_id="config"),
            ],
            id="tabs",
            active_tab="flow",
        )
    ]
)