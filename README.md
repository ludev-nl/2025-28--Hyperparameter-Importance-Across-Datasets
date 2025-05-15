# Hyperparameter Importance Across Datasets
This project aims to create a [Dash][dash]-based web-service through which users can
apply [functional analysis of variance][fanova] on algorithm hyperparameter
settings and performance data from [OpenML][openml]. In this way, they can make
observations on the relative impact of tuning specific hyperparameters on the
performance of a machine learning algorithm, as outlined in this [paper][hyperparam].

# Requirements
In order to run the code, you need [SWIG 3.0][swig], [PCRE 3][pcre] (including the dev
package), Python 3 and the Python packages specified in requirements.txt. During our
development, we used Python 3.12.3 along with the package versions listed in freeze.txt.

# Deployment
For development, the wesite can be deployed using
```
    python app.py
```
and visiting the address listed there. In this case, we use a filesystem backend, and all
cached data is stored in a `./file_system_backend/` folder that needs to be cleaned out manually.
For deployment testing, you can run
```
    supervisord -n
```
and visit http://127.0.0.1:8000. In that case, you need to have a Redis backend running on
`redis://localhost:6379/0` which will take care of storing cached data and removing old entries.


# Testing
In order to test the backend code, you can run the test.sh file in the repository. This will run
both static analysis tools for PEP 8 style checking and type checking, and repository specific unit tests.

[dash]: https://plotly.com/dash/
[fanova]: https://github.com/automl/fanova
[openml]: https://openml.org
[hyperparam]: https://arxiv.org/abs/1710.04725
[swig]: https://www.swig.org
[pcre]: https://www.pcre.org
