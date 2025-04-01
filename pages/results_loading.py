import dash
from dash import html

dash.register_page(__name__, path='/results_loading')

layout = html.Div([
    html.H1('This is our results loading page'),
    html.Div('This is our results loading page content.'),
])