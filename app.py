import dash
from dash import DiskcacheManager, CeleryManager
import dash_bootstrap_components as dbc
import diskcache
from dash_extensions.enrich import DashProxy, ServersideOutputTransform, Input, Output, dcc, html, Serverside, callback, RedisBackend, FileSystemBackend
from openmlfetcher import fetch_flows
from celery import Celery
from redis import StrictRedis
import sys


debug = 'debug' in sys.argv
deploy = ('gunicorn' in sys.argv[0]
          or 'celery' in sys.argv[0])


if deploy:
    redis_url = 'redis://localhost:6379/0'
    redis_inst = StrictRedis.from_url(redis_url)

    try:
        redis_inst.ping()
    except:
        sys.stderr.write('Make sure you have a Redis server running.')
        sys.exit()

    celery_app = Celery(__name__, backend=redis_url, broker=redis_url)
    manager = CeleryManager(celery_app, cache_by=(lambda: 0), expire=3600)
    backend = RedisBackend(default_timeout=3600, host="localhost", port=6379, db=0)

    print('Run `celery -A app:celery_app worker --loglevel=INFO` in a separate window '
          + 'in this folder with your venv active before opening the webpage.')
else:
    cache = diskcache.Cache("./cache")
    manager = DiskcacheManager(cache, cache_by=(lambda: 0), expire=3600)
    backend = FileSystemBackend()


app = DashProxy(__name__,
                use_pages=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                background_callback_manager=manager,
                transforms=[ServersideOutputTransform([backend])])


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
}

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginRight": "2rem",
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
                dbc.NavLink("Experiment", href="/experiment", active="exact"),
                dbc.NavLink("Results", href="/results", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(dash.page_container, style=CONTENT_STYLE)

app.layout = html.Div([
    #store elements that can be used to store the data over pages
    #storage_type is used to specify how long the data is stored for.
    #session means that data is cleared after browser is closed

    dcc.Store(id="fanova_results", storage_type="session", data=None),
    dcc.Store(id='flows', storage_type='session', data=None),
    dcc.Location(id="url"),
    sidebar,
    content


    ])

@callback(
    Output('flows', 'data'),
    Input('flows', 'id'),
    background=True,
    prevent_initial_call=False,
    cache_args_to_ignore=[0]
)
def load_flows(id):
    options_df = fetch_flows()
    options_df['id_str'] = options_df.index.astype(str)
    return Serverside(options_df)

if deploy:
    app.register_celery_tasks()
    server = app.server

if __name__ == "__main__":
    debug = 'debug' in sys.argv
    app.run(port=8888, debug=debug)


