import dash
from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

dash.register_page(__name__, path='/experiment')

# TODO: Exact items will be changed later
items = [
    dbc.DropdownMenuItem("Item 1"),
    dbc.DropdownMenuItem("Item 2"),
    dbc.DropdownMenuItem("Item 3"),
]

flow_content = html.Div([
    # html.H1("This is the flow tab", className="mb-4"),

    html.Div(
        [
            dbc.DropdownMenu(items, label="Flow Selection", color="warning", className="mb-4"),
            dbc.DropdownMenu(items, label="Suite Selection", color="info", className="mb-4"),
        ],
        style={"display": "flex", "flexDirection": "column", "width": "400px"},
    ),

    html.Div(
        [
            dbc.Button("Fetch", outline = True, size="lg", color = "primary", className="mb-4"), 
        ]
    ),

       html.Div(
        [
            dcc.Interval(id="progress-interval", n_intervals=0, interval=500, disabled=True),  
            dbc.Progress(id="progress", value=25, striped=True, animated=True, className="mt-2"),
            dbc.Button(
                "Cancel",
                id="animation-toggle",
                className="mt-2",
                n_clicks=0,
            ),
        ]
    ),
])

# progress bar will show after callback
# @app.callback(
#     Output("progress", "value"),
#     Output("progress-interval", "disabled"),
#     Input("progress-interval", "n_intervals"),
#     Input("animation-toggle", "n_clicks"),
#     State("progress", "value"),
# )
# def update_progress(n_intervals, n_clicks, current_value):
#     if n_clicks > 0:
#         return 0, True  

#     new_value = min(current_value + 10, 100)
#     return new_value, new_value >= 100  


# @app.callback(
#     Output("progress-interval", "disabled"),
#     Input("Fetch-button", "n_clicks"),
#     prevent_initial_call=True  
# )
# def start_progress(n_clicks):
#     return False 

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