import dash
from dash import Input, Output, dcc, html
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd

example_table = {"ID": ['00001', '00002','00003','00004'], "Started in": ['20/04 10:30', '21/04 11:30','22/04 10:30','23/04 10:35']}
df = pd.DataFrame(example_table)
print(df)

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ], style={'backgroundColor':'#f8f9fa'})

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("fANOVA", className="display-4"),
        html.Hr(),
        html.P("Hyperparameter Importance Analysis", className="lead"),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Task Selection", href="/page-1", active="exact"),
                dbc.NavLink("Experiment Management", href="/page-2", active="exact"),
                dbc.NavLink("Analysis", href="/page-3", active="exact"),
                dbc.NavLink("Results", href="/page-4", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return html.Div(
            [
            dbc.Row(
              [
                  dbc.Col(html.Div([html.Center(html.H4(children='Completed Analysis')), html.Center(generate_table(df))]), width=3),
                  dbc.Col(html.Div([html.Center(html.H4(children='Ongoing Analysis')), html.Center(generate_table(df))]), width=3)
              ]
            ),
            dbc.Row(
              [
                  dbc.Col(html.Div(html.Center(dbc.Button("Start New Analysis", color="primary", className="me-1"))), width=6)
              ]
          )
          ]
        )
    elif pathname == "/page-1":
        return html.P("Task Selection Page")
    elif pathname == "/page-2":
        return html.P("Experiment Management Page")
    elif pathname == "/page-3":
        return html.P("Analysis page")
    elif pathname == "/page-4":
        return html.P("Results Page")

    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


if __name__ == "__main__":
    app.run(port=8888)

