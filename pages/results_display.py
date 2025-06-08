import dash
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Input, Output, State, callback, dcc, html
import backend.visualiser as vis
from pandas import read_json
from io import StringIO

dash.register_page(__name__, path="/results")


# responsible for displaying the plots
@callback(
    Output("violin_plot", "figure"),
    Output("critical_distance_img", "src"),
    Input("fanova_results", "data"),
)
def display_results(fanova_results):
    if fanova_results is None:
        return None, None

    fanova_df = read_json(StringIO(fanova_results))

    violin = vis.violinplot(fanova_df, False)
    crit_diff = (vis.crit_diff_diagram(fanova_df)
                 if len(fanova_df.columns) > 2 else None)
    return violin, crit_diff


layout = dbc.Container([
    # dcc.Store(id="fetched_ids", storage_type="session"),
    dbc.Row([
        dbc.Col([
            html.Center(html.H3("Violin Plot",
                                style={"marginBottom": "20px"})),
            dcc.Graph(id="violin_plot"),
        ], width={"offset": 2, "size": 8})
    ]),

    dbc.Row([
        dbc.Col([
            html.Center(html.H3("Critical Difference Plot",
                                style={"marginBottom": "20px"})),
            html.Img(id="critical_distance_img"),
        ], width={"offset": 2, "size": 8})
    ]),

    html.Div([
        dbc.Button(
            "Export csv",
            disabled=True,
            color="primary",
            id="export_csv_button",
            className="mb-1",
            size="lg",
            outline=True,
            style={"marginTop": "30px"}
        ),
        dcc.Download(id="download-fanovaresults-csv")
    ], className="text-center")
], fluid=True)


# responsible for enabling/disabling the download button if ther is/nt data
@callback(
    Output("export_csv_button", "disabled"),
    Input("fanova_results", "data"),
    prevent_initial_call=False
)
def toggle_download_button(data):
    return data is None


# handles the download of the fanova results by the client
@callback(
    Output("download-fanovaresults-csv", "data"),
    Input("export_csv_button", "n_clicks"),
    State("fanova_results", "data"),
    State("fetched_ids", "data"),
    prevent_initial_call=True
)
def export_csv(n_clicks, fanova_results, fetched_ids):
    if fanova_results is None:
        raise dash.exceptions.PreventUpdate

    results_df = read_json(StringIO(fanova_results))

    flow_id = (fetched_ids.get("flow_id", "unkouwn")
               if fetched_ids else "unknouwn")
    suite_id = (fetched_ids.get("suite_id", "unkouwn")
                if fetched_ids else "unkouwn")
    filename = f"fanova_results_f{flow_id}_s{suite_id}.csv"
    return dcc.send_data_frame(results_df.to_csv, filename, index=False)
