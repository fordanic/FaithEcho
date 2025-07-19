.PHONY: lint test precommit build

lint:
	ruff format --check
	ruff check .
	mypy src/faith_echo tests

test:
	pytest -q

precommit:
	pre-commit run --all-files

poetry-lock:
	poetry lock

poetry-install:
	poetry install --with dev --no-interaction --no-root

build:
	docker compose build
