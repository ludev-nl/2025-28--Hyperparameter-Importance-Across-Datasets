import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/results_loading')

layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                        html.Div('Running fANOVA...', className='mb-2'),
                        dbc.Progress(value=50, id='running_fanova', animated=False, striped=True, className='mb-5'),
                ], width=6, className='mx-auto')
            ])
        ])