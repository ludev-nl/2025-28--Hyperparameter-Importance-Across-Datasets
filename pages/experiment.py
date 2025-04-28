import dash
from dash import Input, Output, State, dcc, html, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from ConfigSpace import ConfigurationSpace, CategoricalHyperparameter, UniformFloatHyperparameter, UniformIntegerHyperparameter, Constant

# TODO: change paths/folder structure
# import sys
# sys.path.append('../')

import sys
import os

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'openmlfetcher')))

import openmlfetcher as fetcher
import fanovaservice as fnvs

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dash.register_page(__name__, path='/experiment')


# TODO: Exact items will be changed later
items = [
    dbc.DropdownMenuItem("Item 1"),
    dbc.DropdownMenuItem("Item 2"),
    dbc.DropdownMenuItem("Item 3"),
]


#list of options for the flow selection dropdown bar
options_df = fetcher.fetch_flows()
#convert the fetched data into the right format for the dropdown menu
#returns a list of dictionaries
def df_to_dict_list(df, col):
    return [dict(label=str(id) + '.' + row[col], value = id)
            for id, row in df.iterrows()]

options = df_to_dict_list(options_df, 'full_name')



flow_content = html.Div([
    # html.H1("This is the flow tab", className="mb-4"),
                            html.Br(),
                            dbc.Row([
                                        dbc.Col(html.Div("Flow Selection:"))
                                    ]),
                            dbc.Row([
                                        dbc.Col(html.Div(
                                                    dcc.Dropdown(id='Flow-input')
                                                )),
                                    ]),
                            html.Br(),
                            dbc.Row([
                                        dbc.Col(html.Div("Suite Selection:"))
                                    ]),
                            dbc.Row([
                                        dbc.Col(html.Div(
                                                    dcc.Dropdown(df_to_dict_list(fetcher.fetch_suites(), 'alias'), id='suite_dropdown')
                                                )),
                                    ]),

                            html.Br(),
                            dbc.Row(html.Center(html.Div(
                                [
                                    dbc.Button("Fetch", id= "Fetch", outline = True, size="lg", color = "primary", className="mb-4"),
                                ]
                            ))),

                            html.Br(),
                            dbc.Row([
                                        dbc.Col(
                                                html.Div(
                                                    [
                                                        dbc.Progress(id="progress", value=0, striped=True, animated=True, className="mt-2")
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


# Callback for the flow selection dropdown menu
@callback(
    Output("Flow-input", "options"),
    Input("Flow-input", "search_value")
)
def update_multi_options(search_value):

    #prevents the program from searching the 100k entries from the start.
    #Browser crashes if the search is done with less than 4 characters
    #minimum lenght is added to make sure the program shows previously selected items
    #rather than an empty seachbar

    if not search_value:
        raise PreventUpdate

    if len(search_value) < 3:
        return []

    lst = [o for o in options if search_value in o['label']]

    return lst[:50]


# progress bar will show after callback
@app.callback(
    Output("progress", "value"),
    Output("progress-interval", "disabled"),
    Input("progress-interval", "n_intervals"),
    Input("animation-toggle", "n_clicks"),
    State("progress", "value"),
)
def update_progress(n_intervals, n_clicks, current_value):
    if n_clicks > 0:
        return 0, True

    new_value = min(current_value + 10, 100)
    return new_value, new_value >= 100


@callback(
    Output("progress-interval", "disabled"),
    Input("Fetch", "n_clicks"),
    State("Flow-input", "value"),
    State("suite_dropdown", "value"),
    prevent_initial_call=True,
    background=True,
    running=[
        (Output("Fetch", "disabled"), True, False),
    ],
    progress=[Output("progress", "value"), Output("progress", "max")]

)
#TODO: max_runs have to be deleted 
def start_progress(set_progress, n_clicks, flow_id, suite_id): 
    tasks = fetcher.fetch_tasks(suite_id)
    set_progress(('0', str(len(tasks))))
    data = {}
    #TODO: eventually not just first 10
    i = 0
    for task in tasks:
        task_data = fetcher.fetch_runs(flow_id, task, max_runs=50)
        set_progress((str(i), str(len(tasks))))
        i+=1 
        if task_data is None:
            continue
        data[task] = fetcher.coerce_types(task_data)
    return False

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

#placeholder code for configspace
cfg_space = ConfigurationSpace.from_json("example_cfgspace.json")
hyperparameters = list(cfg_space.keys())

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
                                            dbc.Col(html.Div(
                                                        dcc.Dropdown(hyperparameters,id='hyperparameter')
                                                    ),width={'size':6,'offset':3}),
                                      ]),
                              html.Br(),
                              dbc.Row(id='range'),
                              html.Br(),
                              dbc.Row([
                                            dbc.Col(
                                                table,
                                                width = {"size": 6, "offset": 3},
                                            )
                                      ]),
                          ])

@callback(
    Output(component_id='range', component_property='children'),
    Input(component_id='hyperparameter', component_property='value'),
    prevent_initial_call=True
)
def show_adequate_range(hyperparameter):
    hyperparameter_value = cfg_space[hyperparameter]
    if isinstance(hyperparameter_value, UniformFloatHyperparameter):
        return(
        dbc.Col(width=3),
        dbc.Col(
                    html.Div("min:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="text",id="min_float_value",value=str(hyperparameter_value.lower)),
                    width=2
                ),
        dbc.Col(
                    html.Div("max:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="text",id="max_float_value",value=str(hyperparameter_value.upper),
                              pattern=r"([+-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+))"),
                    width=2
                ),
        )
    elif isinstance(hyperparameter_value, UniformIntegerHyperparameter):
        return(
        dbc.Col(width=3),
        dbc.Col(
                    html.Div("min:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="number",id="min_int_value",value=hyperparameter_value.lower),
                    width=2
                ),
        dbc.Col(
                    html.Div("max:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="number",id="max_int_value",value=hyperparameter_value.upper),
                    width=2
                ),
        )
    elif isinstance(hyperparameter_value, CategoricalHyperparameter):
        return(
        dbc.Col(width=3),
        dbc.Col(
                    html.Div(dcc.Dropdown(hyperparameter_value.choices,hyperparameter_value.choices,multi=True)),
                    width=6
                ),
        )
    else:
        return None


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
                outline = True,
                size = "lg",
                color="primary",
                id="fanova",
                className="mb-4",
            ),
        ),
        dbc.Row([
            dbc.Col(
                    html.Div(
                        [
                            dbc.Progress(id="progress", value=0, striped=True, animated=True, className="mt-2")
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
    ]
)
