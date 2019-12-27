.PHONY: build tests

lint:
	poetry run flake8 --exclude=.venv

mypy:
	poetry run mypy -p bus_tracker

tests:
	pytest tests --cov=bus_tracker/tracker
