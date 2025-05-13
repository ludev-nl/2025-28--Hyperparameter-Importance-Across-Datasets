import dash
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from ConfigSpace import ConfigurationSpace
from dash_extensions.enrich import Input, Output, State, callback, dcc, html, Serverside
from re import split
import pandas as pd

import sys
import os

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'openmlfetcher')))

import openmlfetcher as fetcher
import fanovaservice as fnvs

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dash.register_page(__name__, path='/experiment')

#convert the fetched data into the right format for the dropdown menu
#returns a list of dictionaries
def df_to_dict_list(df, col):
    return [dict(label=str(id) + '.' + row[col], value = id)
            for id, row in df.iterrows()]

flow_content = html.Div([
    # html.H1("This is the flow tab", className="mb-4"),
                            html.Br(),
                            dbc.Row([
                                        dbc.Col(html.Div("Flow Selection:"))
                                    ]),
                            dbc.Row([
                                        dbc.Col(html.Div(
                                                    dcc.Dropdown(id='Flow-input',
                                                                 persistence=True,
                                                                 persistence_type='session')
                                                )),
                                    ]),
                            html.Br(),
                            dbc.Row([
                                        dbc.Col(html.Div("Suite Selection:"))
                                    ]),
                            dbc.Row([
                                        dbc.Col(html.Div(
                                                    dcc.Dropdown(df_to_dict_list(fetcher.fetch_suites(), 'alias'),
                                                                 id='suite_dropdown',
                                                                 persistence=True,
                                                                 persistence_type='session')
                                                )),
                                    ]),

                            html.Br(),
                            dbc.Row(html.Center(html.Div(
                                [
                                    dbc.Button("Fetch", id= "Fetch", outline = True, size="lg", color = "primary", className="mb-4",disabled=False),
                                ]
                            ))),

                            dbc.Row([
                                        dbc.Col(
                                                html.Div(
                                                    [
                                                        dbc.Progress(id="progress_open_ML", value=0, striped=True, animated=True, className="mt-2",  style={"visibility": "hidden"})
                                                    ]
                                                            ),
                                                        width={"size":9, "offset":1},
                                                        align="center",



                                                ),
                                        dbc.Col(
                                                html.Div(
                                                    [
                                                    dbc.Button(
                                                    "Cancel",
                                                    id="cancel_button",
                                                    className="mt-2",
                                                    color="danger",
                                                    outline=True,
                                                    n_clicks=0,
                                                    style={'display':'none'}),
                                                    ]
                                                        ),
                                                    width={"size":1}
                                                )


                            ]),
                        ])


# Callback for the flow selection dropdown menu
@callback(
    Output("Flow-input", "options"),
    Input("Flow-input", "search_value"),
    State('flows', 'data'),
    prevent_initial_call=True
)
def update_multi_options(search_value, flows):
    def mask (df: pd.DataFrame, token: str):
        if token.isnumeric():
            col = 'id_str'
        else:
            col = 'full_name'

        return df[col].str.contains(token, case=False, regex=False)

    if not search_value or flows is None:
        raise PreventUpdate

    if len(search_value) < 3:
        return []

    results = flows
    for token in split('[ .]', search_value):
        if len(token) < 3:
            continue
        results = results[mask(results, token)]

    lst = df_to_dict_list(results, 'full_name')

    return lst[:50]


@callback(
    Output("raw_configspace", 'data'),
    Output("raw_data_store", 'data'),
    Input("Fetch", "n_clicks"),
    State("Flow-input", "value"),
    State("suite_dropdown", "value"),
    prevent_initial_call=True,
    background=True,
    running=[
        (Output("Fetch", "disabled"), True, False),
        (Output("fanova", "disabled"), True, False),
        (Output("progress_open_ML", "style"), {"visibility": "visible"}, {"visibility": "hidden"}),
        (Output("cancel_button", "style"), {"visibility": "visible"}, {"visibility": "hidden"})
    ],
    progress=[Output("progress_open_ML", "value"), Output("progress_open_ML", "max")],
    progress_default=['0', '100'],
    cache_args_to_ignore=[0] # Ignore the button clicks
)
def fetch_openml_data(set_progress, n_clicks, flow_id, suite_id):
    if flow_id is None or suite_id is None:
        raise PreventUpdate

    tasks = fetcher.fetch_tasks(suite_id)

    if tasks is None:
        raise PreventUpdate

    # TODO: eventually all of them, when done debugging
    tasks = tasks[:10]

    data = {}

    i = 1
    for task in tasks:
        # TODO: eventually all of them, when done debugging
        task_data = fetcher.fetch_runs(flow_id, task, max_runs=200)
        set_progress((str(i), str(len(tasks))))
        i += 1
        if task_data is None:
            continue
        data[task] = fetcher.coerce_types(task_data)

    return (fnvs.auto_configspace(data).to_serialized_dict(),
            Serverside(data))


@callback(
    Output('fanova', 'disabled'),
    Input('raw_data_store', 'data'),
    prevent_initial_call=False
)
def toggle_fanova_button(data):
    return data is None


@callback(
    Output("fanova_results_local", "data"),
    Input("fanova", "n_clicks"),
    State('raw_data_store', 'data'),
    State("filtered_data", "data"),
    State('min_runs', 'value'),
    prevent_initial_call=True,
    background=True,
    running=[
        (Output("fanova", "disabled"), True, False),
        (Output('progress', 'color'), 'primary', 'success'),
        (Output("progress_fanova", "style"), {"visibility": "visible"}, {"visibility": "hidden"}),
        (Output("cancel_button2", "style"), {"visibility": "visible"}, {"visibility": "hidden"})
    ],
    progress=[Output("progress_fanova", "value"), Output("progress_fanova", "max")],
    progress_default=['0', '100'],
    cache_args_to_ignore=[0] # Ignore the button clicks
)
def run_fanova(set_progress, n_clicks, raw_data, filtered_data, min_runs):
    if raw_data is None and filtered_data is None:
        raise PreventUpdate

    data = filtered_data if (filtered_data is not None and len(filtered_data) != 0) else raw_data
    cfg_space = fnvs.auto_configspace(data)

    # Finally we prepare to run fanova
    imputed_data, extended_cfg_space = fnvs.impute_data(data, cfg_space)
    processed_data = fnvs.prepare_data(imputed_data, extended_cfg_space)
    # Running fanova takes quite long, so I split it per task
    results = {}
    i = 0
    for task, task_data in processed_data.items():
        i += 1
        set_progress((str(i), str(len(processed_data))))
        result = fnvs.run_fanova(task_data, extended_cfg_space, min_runs)
        if result:
            results[task] = result
    results = pd.DataFrame.from_dict(results, orient='index')

    return results.to_json()


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
                                                        dcc.Dropdown(id='hyperparameter_dd')
                                                    ),width={'size':6,'offset':3}),
                                      ]),
                              html.Br(),
                              dbc.Row(id='range'),
                              html.Br(),
                              html.Center(
                                  dbc.Button(
                                      'Filter',
                                      id='filter_button',
                                      outline = True,
                                      size = "lg",
                                      color="primary",
                                      className="mb-4",
                                  )
                              ),
                              dbc.Row([
                                            dbc.Col(dash.dash_table.DataTable(id='runs_table',
                                                                              editable=False,
                                                                              cell_selectable=False)),
                                            dbc.Col(dash.dash_table.DataTable(id='nan_table',
                                                                              editable=False,
                                                                              cell_selectable=False)),
                                      ]),
                              dcc.Store(id='filtered_config_int', storage_type='session'),
                              dcc.Store(id='filtered_config_float', storage_type='session'),
                              dcc.Store(id='filtered_config_cat', storage_type='session'),
                              dcc.Store(id='filtered_config', storage_type='session'),
                          ])


@callback(
    Output('runs_table', 'style_data_conditional'),
    Input('min_runs', 'value'),
    Input('runs_table', 'data'),
    prevent_initial_call=True
)
def table_formatting(min_runs, data):
    return [
        {
            'if': {
                'filter_query': f'{{Filtered runs}} < {min_runs}',
                'column_id': 'Filtered runs'
            },
            'backgroundColor': '#FF4136'
        }
    ]


@callback(
    Output(component_id='hyperparameter_dd', component_property='options'),
    Input(component_id='raw_configspace', component_property='data'),
    prevent_initial_call=True
)
def update_param_dropdown(raw_configspace):
    return [param['name'] for param in raw_configspace['hyperparameters']
            if param['type'] != 'constant']


def transform_cfg_space(cfg):
    return {p['name']: p for p in cfg['hyperparameters']}


@callback(
    Output(component_id='range', component_property='children'),
    Input(component_id='hyperparameter_dd', component_property='value'),
    State(component_id='filtered_config', component_property='data'),
    State(component_id='raw_configspace', component_property='data'),
    prevent_initial_call=True
)
def show_adequate_range(hyperparameter, filtered_config, raw_configspace):
    if hyperparameter is None:
        return None

    raw_configspace = transform_cfg_space(raw_configspace)

    if filtered_config is not None and hyperparameter in filtered_config.keys():
        hyperparameter_value = filtered_config[hyperparameter]
    else:
        hyperparameter_value = raw_configspace[hyperparameter]

    if hyperparameter_value['type'] == 'uniform_float':
        return(
        dbc.Col(width=3),
        dbc.Col(
                    html.Div("min:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="text",id="min_float_value",value=str(hyperparameter_value['lower'])),
                    width=2
                ),
        dbc.Col(
                    html.Div("max:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="text",id="max_float_value",value=str(hyperparameter_value['upper']),
                              pattern=r"([+-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+))"),
                    width=2
                ),
        )
    elif hyperparameter_value['type'] == 'uniform_int':
        return(
        dbc.Col(width=3),
        dbc.Col(
                    html.Div("min:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="number",id="min_int_value",value=hyperparameter_value['lower']),
                    width=2
                ),
        dbc.Col(
                    html.Div("max:"),
                    width=1
                ),
        dbc.Col(
                    dbc.Input(type="number",id="max_int_value",value=hyperparameter_value['upper']),
                    width=2
                ),
        )
    elif hyperparameter_value['type'] == 'categorical':
        return(
        dbc.Col(width=3),
        dbc.Col(
                    html.Div(dcc.Dropdown(raw_configspace[hyperparameter]['choices'],hyperparameter_value['choices'],multi=True, id='categories')),
                    width=6
                ),
        )
    else:
        return None


@callback(
    Output(component_id='filtered_config_float', component_property='data'),
    Input(component_id='min_float_value', component_property='value'),
    Input(component_id='max_float_value', component_property='value'),
    Input(component_id='raw_configspace', component_property='data'),
    State(component_id='hyperparameter_dd', component_property='value'),
    State(component_id='filtered_config_float', component_property='data'),
    prevent_initial_call=True
)
def update_float_range_hyperparameter(min_float_value,max_float_value,raw_configspace,hyperparameter,filtered_config_float):
    if dash.callback_context.triggered_id == 'raw_configspace':
        return None

    raw_configspace = transform_cfg_space(raw_configspace)

    if filtered_config_float is None:
        filtered_config_float = {}
    if (float(min_float_value) == raw_configspace[hyperparameter]['lower']) and (float(max_float_value) == raw_configspace[hyperparameter]['upper']):
        if hyperparameter in filtered_config_float.keys():
            del filtered_config_float[hyperparameter]
        return filtered_config_float
    filtered_config_float[hyperparameter] = {'type': 'uniform_float', 'name': raw_configspace[hyperparameter]['name'], 'lower': float(min_float_value), 'upper': float(max_float_value)}
    return filtered_config_float

@callback(
    Output(component_id='filtered_config_int', component_property='data'),
    Input(component_id='min_int_value', component_property='value'),
    Input(component_id='max_int_value', component_property='value'),
    Input(component_id='raw_configspace', component_property='data'),
    State(component_id='hyperparameter_dd', component_property='value'),
    State(component_id='filtered_config_int', component_property='data'),
    prevent_initial_call=True
)
def update_int_range_hyperparameter(min_int_value,max_int_value,raw_configspace,hyperparameter,filtered_config_int):
    if dash.callback_context.triggered_id == 'raw_configspace':
        return None

    raw_configspace = transform_cfg_space(raw_configspace)

    if filtered_config_int is None:
        filtered_config_int = {}
    if (min_int_value == raw_configspace[hyperparameter]['lower']) and (max_int_value == raw_configspace[hyperparameter]['upper']):
        if hyperparameter in filtered_config_int.keys():
            del filtered_config_int[hyperparameter]
        return filtered_config_int
    else:
        filtered_config_int[hyperparameter] = {'type': 'uniform_int', 'name': raw_configspace[hyperparameter]['name'], 'lower': min_int_value, 'upper': max_int_value}
        return filtered_config_int

@callback(
    Output(component_id='filtered_config_cat', component_property='data'),
    Input(component_id='categories', component_property='value'),
    Input(component_id='raw_configspace', component_property='data'),
    State(component_id='hyperparameter_dd', component_property='value'),
    State(component_id='filtered_config_cat', component_property='data'),
    prevent_initial_call=True
)
def update_categorical_hyperparameter(categories, raw_configspace, hyperparameter, filtered_config_cat):
    if dash.callback_context.triggered_id == 'raw_configspace':
        return None

    raw_configspace = transform_cfg_space(raw_configspace)

    if filtered_config_cat is None:
        filtered_config_cat = {}
    if (set(categories) == set(raw_configspace[hyperparameter]['choices'])):
        if hyperparameter in filtered_config_cat.keys():
            del filtered_config_cat[hyperparameter]
        return filtered_config_cat
    filtered_config_cat[hyperparameter] = {'type': 'categorical', 'name': raw_configspace[hyperparameter]['name'], 'choices': categories}
    return filtered_config_cat

@callback(
    Output(component_id='filtered_config', component_property='data'),
    Input(component_id='filtered_config_int', component_property='data'),
    Input(component_id='filtered_config_float', component_property='data'),
    Input(component_id='filtered_config_cat', component_property='data'),
    prevent_initial_call=True
)
def concat_filtered(filtered_config_int, filtered_config_float, filtered_config_cat):
    dict = {}
    for config in (filtered_config_int,filtered_config_float,filtered_config_cat):
        if config is not None:
            dict.update(config)
    return dict

@callback(
    Output(component_id='filtered_data', component_property='data'),
    Output(component_id='runs_table', component_property='data'),
    Output(component_id='nan_table', component_property='data'),
    Input(component_id='filter_button', component_property='n_clicks'),
    Input(component_id='raw_data_store', component_property='data'),
    State(component_id='raw_configspace', component_property='data'),
    State(component_id='filtered_config', component_property='data'),
    prevent_initial_call=True
)
def filter_action(n_clicks, raw_data, raw_space, filter_cfg):
    def nan_count(data, col):
        counts = [df[col].isna().sum() for df in data.values()]
        return sum(counts)

    if raw_data is None or len(raw_data) == 0:
        return None, None, None

    if dash.callback_context.triggered_id == 'raw_data_store':
        return (None,
                [{'Task': id, 'Runs': len(raw_data[id])}
                 for id in raw_data.keys()],
                [{'Hyperparameter': p['name'], 'Missing values': nan_count(raw_data, p['name'])}
                 for p in raw_space['hyperparameters'] if p['type'] != 'constant'])

    serialized = {'hyperparameters': filter_cfg.values()}
    filter_space = ConfigurationSpace.from_serialized_dict(serialized)

    filtered = fnvs.filter_data(raw_data, filter_space)

    runs = [{'Task': id,
             'Original runs': len(raw_data[id]),
             'Filtered runs': len(filtered[id])}
            for id in raw_data.keys()]

    nans = [{'Hyperparameter': p['name'],
             'Original missing values': nan_count(raw_data, p['name']),
             'Filtered missing values': nan_count(filtered, p['name'])}
            for p in raw_space['hyperparameters'] if p['type'] != 'constant']

    return Serverside(filtered), runs, nans


@callback(
    Output('fanova_results', 'data'),
    Input('fanova_results_local', 'data')
)
def update_global_results(data):
    return data


layout = dbc.Container(
    [
        dcc.Store(id="raw_data_store", storage_type="session", data=None),
        dcc.Store(id="filtered_data", storage_type= "session", data=None),
        dcc.Store(id="raw_configspace", storage_type= "session", data=None),
        dcc.Store(id="fanova_results_local", storage_type= "session", data=None),
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
        html.Hr(),
        html.Center(
            dbc.Button(
                "Run Fanova",
                outline = True,
                size = "lg",
                color="primary",
                id="fanova",
                className="mb-4",
                disabled = True
            ),
        ),
        dbc.Row([
            dbc.Col(
                    html.Div(
                        [
                            dbc.Progress(id="progress_fanova", value=0, striped=True, animated=True, className="mt-2", style={"visibility": "hidden"})
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
                        id="cancel_button2",
                        className="mt-2",
                        color="danger",
                        outline=True,
                        style={'visibility':'hidden'},
                        n_clicks=0),
                        ]
                            ),
                        width={"size":1}
                    )
                            ]),
    ]
)
