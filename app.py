import dash
from dash import Input, Output, dcc, html, DiskcacheManager
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
import diskcache
# from dash_extensions.enrich import  DashProxy, Serverside, ServersideOutputTransform
  # Diskcache for non-production apps when developing locally

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)


app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP],background_callback_manager=background_callback_manager)
# app = DashProxy(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP],background_callback_manager=background_callback_manager,transforms=[ServersideOutputTransform()])


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

app.layout = html.Div([
    #store elements that can be used to store the data over pages
    #storage_type is used to specify how long the data is stored for.
    #session means that data is cleared after browser is closed

    #datatype is a dictionary
    dcc.Store(id="raw_data_store", storage_type="session", data={}),
    dcc.Store(id="filtered_data", storage_type= "session", data={}),
    #datatype is config space element, but that is initialised with None type
    dcc.Store(id="raw_configspace",storage_type= "session", data=None),
    dcc.Store(id="filtered_configspace",storage_type= "session", data=None),
    dcc.Location(id="url"),
    sidebar,
    content


    ])






if __name__ == "__main__":
    app.run(port=8888)


