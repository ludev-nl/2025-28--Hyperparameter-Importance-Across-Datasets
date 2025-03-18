# Hyperparameter Importance Across Datasets
This project aims to create a [Dash][dash]-based web-service through which users can
apply [functional analysis of variance][fanova] on algorithm hyperparameter
settings and performance data from [OpenML][openml]. In this way, they can make
observations on the relative impact of tuning specific hyperparameters on the
performance of a machine learning algorithm, as outlined in this [paper][hyperparam].

# Requirements
In order to run the code, you need [SWIG 3.0][swig], [PCRE 3][pcre] (including the dev
package), Python 3 and the Python packages specified with version in requirements.txt.
For website deployment, the free version of [Dash][dash] is also needed.

# Testing
In order to test the code, you can run the test.sh file in the repository. This will run
both a static analysis tool for PEP 8 style checking, and repository specific unit tests.

[dash]: https://plotly.com/dash/
[fanova]: https://github.com/automl/fanova
[openml]: https://openml.org
[hyperparam]: https://arxiv.org/abs/1710.04725
[swig]: https://www.swig.org
[pcre]: https://www.pcre.org
