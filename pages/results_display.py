import dash
from dash import html,dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash_extensions.enrich import Input, Output, State, callback, dcc, html, Serverside
import fanovaservice as fnvs
import visualiser as vis
from pandas import read_json

dash.register_page(__name__, path='/results_display')

# currently use two blank figures as placeholder
violinplot = go.Figure()
cdplot = go.Figure()

@callback(
    Input("fanova_results", "data"),
    Output("violin-plot", "figure")
)
def display_results(fanova_results):
    fanova_df = read_json(fanova_results)
    return vis.violinplot(fanova_df, False)
    

layout = dbc.Container([
        html.H1('Here are the results:'),
        dbc.Row([
                dbc.Col([
                        html.H5('Violin Plot'),
                        dcc.Graph(figure=violinplot, id='violin-plot'),
                ], width=6),
                dbc.Col([
                        html.H5('Critical Difference Plot'),
                        dcc.Graph(figure=cdplot, id='cd-plot'),
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