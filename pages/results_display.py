import dash
from dash import html

dash.register_page(__name__, path='/results_display')

layout = html.Div([
    html.H1('This is our results display page'),
    html.Div('This is our results display page content.'),
])