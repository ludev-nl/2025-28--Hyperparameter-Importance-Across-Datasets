import dash
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from ConfigSpace import ConfigurationSpace, CategoricalHyperparameter, UniformFloatHyperparameter, UniformIntegerHyperparameter, Constant
from dash_extensions.enrich import Input, Output, State, callback, dcc, html, Serverside
from re import escape, split
import pandas as pd

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


#list of options for the flow selection dropdown bar
options_df = fetcher.fetch_flows()
options_df['id_str'] = options_df.index.astype(str)
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
                                                        dbc.Progress(id="progress_open_ML", value=0, striped=True, animated=True, className="mt-2")
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

    def mask (df, token):
        if token.isnumeric():
            col = 'id_str'
        else:
            col = 'full_name'
        return df[col].str.contains(token)

    if not search_value:
        raise PreventUpdate

    if len(search_value) < 3:
        return []

    search_value = escape(search_value)
    results = options_df
    for token in split('[ .]', search_value):
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
    ],
    progress=[Output("progress_open_ML", "value"), Output("progress_open_ML", "max")]
)
def fetch_openml_data(set_progress, n_clicks, flow_id, suite_id):
    tasks = fetcher.fetch_tasks(suite_id)

    if tasks is None:
        raise PreventUpdate

    set_progress(('0', str(len(tasks))))
    data = {}
    i = 1
    for task in tasks:
        #TODO: max_runs have to be deleted
        task_data = fetcher.fetch_runs(flow_id, task, max_runs=200)
        set_progress((str(i), str(len(tasks))))
        i += 1
        if task_data is None:
            continue
        data[task] = fetcher.coerce_types(task_data)

    set_progress(('0', '100'))

    return fnvs.auto_configspace(data).to_serialized_dict(), \
           Serverside(data)

@callback(
    Output("fanova_results", "data"),
    Input("fanova", "n_clicks"),
    State("raw_configspace", "data"),
    State("raw_data_store", "data"),
    prevent_initial_call=True,
    background=True,
    running=[
        (Output("fanova", "disabled"), True, False),
    ],
    progress=[Output("progress", "value"), Output("progress", "max")]
)
def run_fanova(set_progress, n_clicks, cfg_space, data):
    if cfg_space is None or data is None:
        raise PreventUpdate

    min_runs = 50
    # Finally we prepare to run fanova
    imputed_data, extended_cfg_space = fnvs.impute_data(data, cfg_space)
    processed_data = fnvs.prepare_data(imputed_data, extended_cfg_space)
    # Running fanova takes quite long, so I split it per task
    results = {}
    set_progress(('0', str(len(processed_data))))
    i = 0
    for task, task_data in processed_data.items():
        i += 1
        set_progress((str(i), str(len(processed_data))))
        result = fnvs.run_fanova(task_data, extended_cfg_space, min_runs)
        if result:
            results[task] = result
    results = pd.DataFrame.from_dict(results, orient='index')

    set_progress(('0', '100'))

    json_results = results.to_json()
    return json_results


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
cfg_space = {hyper['name']: hyper for hyper in ConfigurationSpace.from_json("example_cfgspace.json").to_serialized_dict()['hyperparameters']}
print(cfg_space)
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
                                                        id='hyperparameter_dd'
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
                              dcc.Store(id='filtered_config_int'),
                              dcc.Store(id='filtered_config_float'),
                              dcc.Store(id='filtered_config_cat'),
                              dcc.Store(id='filtered_config'),
                              html.Div(id='config')
                          ])

@callback(
    Output(component_id='range', component_property='children'),
    Input(component_id='hyperparameter', component_property='value'),
    State(component_id='filtered_config', component_property='data'),
    State(component_id='raw_configspace', component_property='data'),
    prevent_initial_call=True
)
def show_adequate_range(hyperparameter, filtered_config, raw_configspace):
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

# @callback(
#     Output(component_id='hyperparameter_dd', component_property='children'),
#     Input(component_id='raw_configspace', component_property='data')
# )
# def update_param_dropdown(raw_configspace):
#     return dcc.Dropdown(list(raw_configspace.keys()),id='hyperparameter')

@callback(
    Output(component_id='filtered_config_float', component_property='data'),
    Input(component_id='min_float_value', component_property='value'),
    Input(component_id='max_float_value', component_property='value'),
    State(component_id='hyperparameter', component_property='value'),
    State(component_id='filtered_config_float', component_property='data'),
    State(component_id='raw_configspace', component_property='data'),
    prevent_initial_call=True
)
def update_float_range_hyperparameter(min_float_value,max_float_value,hyperparameter,filtered_config_float,raw_configspace):
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
    State(component_id='hyperparameter', component_property='value'),
    State(component_id='filtered_config_int', component_property='data'),
    State(component_id='raw_configspace', component_property='data'),
    prevent_initial_call=True
)
def update_int_range_hyperparameter(min_int_value,max_int_value,hyperparameter,filtered_config_int,raw_configspace):
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
    State(component_id='hyperparameter', component_property='value'),
    State(component_id='filtered_config_cat', component_property='data'),
    State(component_id='raw_configspace', component_property='data'),
    prevent_initial_call=True
)
def update_categorical_hyperparameter(categories,hyperparameter,filtered_config_cat, raw_configspace):
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
    Output(component_id='config', component_property='children'),
    Input(component_id='filtered_config', component_property='data'),
    prevent_initial_call=True
)
def display_filtered(filtered_config):
    return str(filtered_config)

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
                disabled = True
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
