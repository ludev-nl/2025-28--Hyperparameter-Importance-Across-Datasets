# Style checks
python3 -m flake8
# Type checks
python3 -m mypy --disable-error-code import-untyped openmlfetcher.py fanovaservice.py visualiser.py
# Unit tests
python3 -W ignore::DeprecationWarning -m unittest tests/*.py
