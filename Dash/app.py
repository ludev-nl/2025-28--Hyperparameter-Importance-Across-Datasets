import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc 
from home import create_page_home
from page2 import create_page_2
from page3 import create_page_3

# initialise the application 
app = dash.Dash(__name__, suppress_callback_exceptions=True,external_stylesheets=[dbc.themes.VAPOR]) 


# #  Dash constructor, used to initialise the app. 

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-2':
        return create_page_2()
    if pathname == '/page-3':
        return create_page_3()
    else:
        return create_page_home()


if __name__ == '__main__': 
    app.run_server() 
