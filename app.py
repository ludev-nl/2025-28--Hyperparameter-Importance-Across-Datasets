import dash
from dash import DiskcacheManager, CeleryManager
import dash_bootstrap_components as dbc
from dash_extensions.enrich import (
    DashProxy,
    ServersideOutputTransform,
    Input,
    Output,
    dcc,
    html,
    Serverside,
    callback)
from backend.openmlfetcher import fetch_flows, fetch_suites
import sys


debug = 'debug' in sys.argv
deploy = ('gunicorn' in sys.argv[0]
          or 'celery' in sys.argv[0])


if deploy:
    from dash_extensions.enrich import RedisBackend as DashRedisBackend
    from celery import Celery
    from redis import StrictRedis
    from redis.exceptions import ConnectionError

    # Redis configuration
    host = 'localhost'
    port = 6379
    db = 0
    cache_expiry = 24 * 60 * 60

    redis_url = 'redis://' + host + ':' + str(port) + '/' + str(db)
    redis_inst = StrictRedis.from_url(redis_url)

    try:
        redis_inst.ping()
    except ConnectionError:
        sys.stderr.write('Make sure you have a Redis server running.')
        sys.exit()

    # Configure the redis backend for Celery's job queue
    celery_app = Celery(__name__, backend=redis_url, broker=redis_url)
    manager = CeleryManager(celery_app, cache_by=(lambda: 0))
    rb = manager.handle.backend.expires = cache_expiry

    # Configure the redis backend for Serverside Output Transform
    backend = DashRedisBackend(
        default_timeout=cache_expiry+5,
        host=host, port=port, db=db
        )
else:
    from dash_extensions.enrich import FileSystemBackend
    from diskcache import Cache

    cache = Cache("./cache")
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
    # store elements that can be used to store the data over pages
    # storage_type is used to specify how long the data is stored for.
    # session means that data is cleared after browser is closed

    dcc.Store(id="fanova_results", storage_type="session", data=None),
    dcc.Store(id="fetched_ids", storage_type="session", data=None),
    dcc.Store(id='flows', storage_type='session', data=None),
    dcc.Store(id='suites', storage_type='session', data=None),
    dcc.Location(id="url"),
    sidebar,
    content


    ])


@callback(
    Output('flows', 'data'),
    Output('suites', 'data'),
    Input('flows', 'id'),
    background=True,
    prevent_initial_call=False,
    cache_args_to_ignore=[0]
)
def load_flows(id):
    options_df = fetch_flows()
    options_df['id_str'] = options_df.index.astype(str)

    suites_df = fetch_suites()

    if options_df is None or suites_df is None:
        raise dash.exceptions.PreventUpdate

    return Serverside(options_df), Serverside(suites_df)


if deploy:
    app.register_celery_tasks()
    server = app.server

if __name__ == "__main__":
    debug = 'debug' in sys.argv
    app.run(port=8888, debug=debug)
