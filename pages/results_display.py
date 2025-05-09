import dash
from dash import html,dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash_extensions.enrich import Input, Output, State, callback, dcc, html, Serverside
import fanovaservice as fnvs
import visualiser as vis
from pandas import read_json
from io import StringIO

dash.register_page(__name__, path='/results_display')

# # currently use two blank figures as placeholder
# violinplot = go.Figure()
# cdplot = 'data:image/png;base64,'

@callback(
    Output("violin-plot", "figure"),
    Output("critical-distance-plot", "src"),
    Input("fanova_results", "data"),
)
def display_results(fanova_results):
    fanova_df = read_json(StringIO(fanova_results))
    return vis.violinplot(fanova_df, False), vis.crit_diff_diagram(fanova_df)


layout = dbc.Container([
        html.H1('Here are the results:'),
        dbc.Row([
                dbc.Col([
                        html.H5('Violin Plot'),
                        dcc.Graph(id='violin-plot'),
                ], width=6),
                dbc.Col([
                        html.H5('Critical Difference Plot'),
                        html.Img(id='critical-distance-plot'),
                ], width=6)
        ]),
        html.Div([
            html.Div('Download the csv files:'),
                    dbc.Button(
                    'Export CSV',
                    color='primary',
                    id='button',
                    className='mb-3',
                )
        ], className='text-center')
], fluid=True)
