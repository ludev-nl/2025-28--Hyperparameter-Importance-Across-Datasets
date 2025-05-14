import dash
from dash import html,dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash_extensions.enrich import Input, Output, State, callback, dcc, html, Serverside
import fanovaservice as fnvs
import visualiser as vis
from pandas import read_json
from io import StringIO

dash.register_page(__name__, path='/results')


@callback(
    Output("violin-plot", "figure"),
    Output("critical-distance-plot", "src"),
    Input("fanova_results", "data"),
)
def display_results(fanova_results):
    if fanova_results is None:
        return None, None

    fanova_df = read_json(StringIO(fanova_results))
    return vis.violinplot(fanova_df, False), vis.crit_diff_diagram(fanova_df)


layout = dbc.Container([
        dbc.Row([
                dbc.Col([
                        html.Center(html.H3('Violin Plot')),
                        dcc.Graph(id='violin-plot'),
                ], width={'offset':2, 'size':8}),
        dbc.Row([
                dbc.Col([
                        html.Center(html.H3('Critical Difference Plot')),
                        html.Img(id='critical-distance-plot'),
                ], width={'offset':2, 'size':8})
        ])
        ]),
        html.Div([
                    dbc.Button(
                    'Export CSV',
                    color='primary',
                    id='button',
                    className='mb-3',
                )
        ], className='text-center')
], fluid=True)
