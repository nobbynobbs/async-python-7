.PHONY: build tests

install:
	poetry install --no-dev

install-dev:
	poetry install

lint:
	poetry run flake8 --exclude=.venv

mypy:
	poetry run mypy -p bus_tracker

tests:
	pytest tests --cov=bus_tracker/tracker
