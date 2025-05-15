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
            html.Center(html.H3('Violin Plot', style={"marginBottom": "20px"})),
            dcc.Graph(id='violin-plot'),
        ], width={'offset': 2, 'size': 8})
    ]),

    dbc.Row([
        dbc.Col([
            html.Center(html.H3('Critical Difference Plot', style={"marginBottom": "20px"})),
            html.Img(id='critical-distance-plot'),
        ], width={'offset': 2, 'size': 8})
    ]),

    html.Div([
        dbc.Button(
            'Export csv',
            disabled=True,
            color='primary',
            id='export_csv_button',
            className='mb-1',
            size='lg',
            outline=True,
            style={"marginTop": "30px"}
        ),
        dcc.Download(id="download-fanovaresults-csv")
    ], className='text-center')
], fluid=True)


@callback(
    Output('export_csv_button', 'disabled'),
    Input('fanova_results', 'data'),
    prevent_initial_call=False
)
def toggle_download_button(data):
    return data is None


@callback(
    Output("download-fanovaresults-csv", "data"),
    Input("export_csv_button", "n_clicks"),
    State("fanova_results", "data"),
    prevent_initial_call=True
)
def export_csv(n_clicks, fanova_results):
    if fanova_results is None:
        raise dash.exceptions.PreventUpdate

    results_df = read_json(StringIO(fanova_results))
    return dcc.send_data_frame(results_df.to_csv, "fanova_results.csv", index=False)