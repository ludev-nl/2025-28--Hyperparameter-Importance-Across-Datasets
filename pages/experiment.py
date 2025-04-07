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
                            html.Br(),
                            dbc.Row([
                                        dbc.Col(html.Div("Flow Selection:"))
                                    ]),
                            dbc.Row([
                                        dbc.Col(html.Div(
                                                    dcc.Dropdown(["Hyperp 1", "hyparam","1352 hyp"],id='num_hyperparameter')
                                                )),
                                    ]),
                            html.Br(),
                            dbc.Row([
                                        dbc.Col(html.Div("Suite Selection:"))
                                    ]),
                            dbc.Row([
                                        dbc.Col(html.Div(
                                                    dcc.Dropdown(["Hyperp 1", "hyparam","1352 hyp"],id='num_hyperparameter')
                                                )),
                                    ]), 
 
                            html.Br(),
                            dbc.Row(html.Center(html.Div(
                                [
                                    dbc.Button("Fetch", outline = True, size="lg", color = "primary", className="mb-4"), 
                                ]
                            ))),
        
                            html.Br(),
                            dbc.Row([   
                                        dbc.Col(
                                                html.Div(
                                                    [
                                                        dcc.Interval(id="progress-interval", n_intervals=0, interval=500, disabled=True),  
                                                        dbc.Progress(id="progress", value=25, striped=True, animated=True, className="mt-2")
                                                    ]
                                                            ),
                                                        width={"size":9, "offset":1},
                                                        align="center"
                                                ),
                                        dbc.Col(
                                                html.Div(
                                                    [
                                                    dbc.Button(
                                                    "Cancel",
                                                    id="animation-toggle",
                                                    className="mt-2",
                                                    color="danger",
                                                    outline=True,
                                                    n_clicks=0),
                                                    ]
                                                        ),
                                                    width={"size":1}
                                                )
                                                       
                                
                            ]), 
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


#placeholder code for table
table_header = [html.Thead(html.Tr([html.Th("Task ID"), html.Th("Original runs"), html.Th("Filtered runs")]))]

row1 = html.Tr([html.Td("3"), html.Td("500"), html.Td("20")])
row2 = html.Tr([html.Td("6"), html.Td("460"), html.Td("100")])
row3 = html.Tr([html.Td("11"), html.Td("600"), html.Td("150")])

table_body = [html.Tbody([row1, row2, row3])]

table = dbc.Table(
    table_header + table_body,
    bordered=True,
    hover=True,
    responsive=True,
    striped=True,
    )

config_content = html.Div([
                              html.Br(),
                              dbc.Row([
                                          dbc.Col(html.Div("Minimal runs:")),
                                          dbc.Col(
                                                      dbc.Input(
                                                        type="number",id="min_runs",value=0
                                                    )
                                                )
                                      ]),
                              html.Br(),
                              dbc.Row(html.Center(html.Div("Choose hyperparameter configuration space:"))),
                              html.Br(),
                              dbc.Row([
                                            dbc.Col(html.Div("Categorical:")),
                                            dbc.Col(html.Div("Numerical:"))
                                      ]),
                              dbc.Row([
                                            dbc.Col(html.Div(
                                                        dcc.Dropdown(["Hyperp 1", "hyparam","1352 hyp"],id='num_hyperparameter')
                                                    )),
                                            dbc.Col(html.Div(
                                                        dcc.Dropdown(["Hyperp 1", "hyparam","1352 hyp"],id='cat_hyperparameter')
                                                    ))
                                      ]),
                              html.Br(),
                              dbc.Row([
                                            dbc.Col(
                                                        html.Div(
                                                            dcc.Dropdown(["Random Forest", "Transformer","k-Neighbours"],
                                                                         ["Random Forest", "Transformer","k-Neighbours"],
                                                                         id='categories',
                                                                         multi=True)
                                                                ),
                                                        width=6
                                                    ),
                                            dbc.Col(
                                                        html.Div("min:"),
                                                        width=1
                                                    ),
                                            dbc.Col(
                                                        dbc.Input(type="text",id="min_value",value="0.0"),
                                                        width=2
                                                    ),
                                            dbc.Col(
                                                        html.Div("max:"),
                                                        width=1
                                                    ),
                                            dbc.Col(
                                                        dbc.Input(type="text",id="max_value",value="0.0",
                                                                  pattern=r"([+-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+))"),
                                                        width=2
                                                    ),
                                      ]),
                              html.Br(),
                              dbc.Row([
                                            dbc.Col(
                                                table,
                                                width = {"size": 6, "offset": 3},
                                            )
                                      ]),
                          ])

layout = dbc.Container(
    [
        html.H1("Experiment Setup"),
        dcc.Markdown('''
                1. Choose which flows and suites you want to include in the analysis. Click the fetch button to fetch them.
                2. Filter your configuration space by selecting which hyperparameter configurations should be included. By default, all configurations are included.
                3. Click the 'Run Fanova' button and wait for the results.
                '''),
        dbc.Tabs(
            [
                dbc.Tab(flow_content, label="Flow and Suite Selection", tab_id="flow"),
                dbc.Tab(config_content, label="Configuration Space", tab_id="config"),
            ],
            id="tabs",
            active_tab="flow",
        ),
        html.Center(
            dbc.Button(
                "Run Fanova",
                color="primary",
                id="button",
                className="mb-3",
            ),
        )
    ]
)
