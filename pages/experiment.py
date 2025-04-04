import dash
from dash import Input, Output, dcc, html
import dash_bootstrap_components as dbc

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

dash.register_page(__name__, path='/experiment')

flow_content = html.Div(html.H1("This the flow tab"))

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
                                                        html.Div(dcc.Dropdown(["Random Forest", "Transformer","k-Neighbours"],id='categories')),
                                                    ),
                                            dbc.Col(
                                                        html.Div([
                                                                     dcc.RangeSlider(0,20,marks=None,id='range')
                                                                 ]),
                                                    ),
                                      ])
                          ])

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
