.PHONY: lint test precommit build

lint:
ruff format --check
ruff check .

test:
pytest -q

precommit:
pre-commit run --all-files

build:
docker compose build
