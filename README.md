# Hyperparameter Importance Across Datasets
This project aims to create a [Dash][dash]-based web-service through which users can
apply [functional analysis of variance][fanova] on algorithm hyperparameter
settings and performance data from [OpenML][openml]. In this way, they can make
observations on the relative impact of tuning specific hyperparameters on the
performance of a machine learning algorithm, as outlined in this [paper][hyperparam].
The development team of this project consists of seven students taking part in the
2025 Software Engineering course of Leiden University.

# Deployment
Our webapp can be deployed in two ways: using a Docker container, or by creating your
own virtual environment. In both cases, it is also possible to use the webapp as a
local app, without actual server deployment.

## Docker
You may use the provided Dockerfile to build a Docker image of the webapp, negating
the need of managing dependencies. This can be achieved using the following command:
```
    docker build -t hpiad .
```
This Docker image can now be ran using the following command:
```
    docker run -p 127.0.0.1:8000:8000/tcp hpiad
```
Here 127.0.0.1:8000 may be replaced by any other host port as needed, and will be
the port on which you can access the webapp (Localhost 8000 in this example).

## Virtual Environment
It is also possible to run the webapp directly. In this case, you will need the
[swig 3.0.12][swig], [libpcre3-dev][pcre] and [redis][redis] system packages, and
set up a Python 3.12 environment with the requirements in docs/deploy.txt. This
file also details the exact version of all packages used. For a general overview
of the packages we directly use (without their own dependencies), refer to
docs/requirements.txt. The app can then be ran by starting redis-server and using the command
```
    supervisord -n -c ./docs/supervisord.conf
```
The app will be available on port 0.0.0.0:8000. This port can be changed by specifying
the bind parameter of gunicorn in docs/supervisord.conf.

# Development
For developmen the above methods listed in Deployment may also be used, but there is
also the option to use a simple filesystem caching and result backend, instead of
Redis, Celery and Supervisor. You will still need [swig 3.0.12][swig] and [libpcre3-dev][pcre],
and the Python packages required can be taken from docs/requirements.txt. The app can
then be ran simply using the command
```
    python app.py [debug]
```
The debug flag toggles Dash's debug functionalities. The webapp will be shown on Localhost
port 8888.

## Testing
Our testing workflow includes flake8 codestyle checks for all Python code, static type
checking for backend code, and a unit test suite for backend code. These tests can be run
using the test.sh script, and require the additional dependencies listed in docs/test.txt.


[dash]: https://plotly.com/dash/
[fanova]: https://github.com/automl/fanova
[openml]: https://openml.org
[hyperparam]: https://arxiv.org/abs/1710.04725
[swig]: https://www.swig.org
[pcre]: https://www.pcre.org
[redis]: https://redis.io/
