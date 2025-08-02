.PHONY: lint test precommit build proto

lint:
	ruff format --check
	ruff check .
	mypy src/faith_echo services tests

unit-tests:
	pytest -q tests/unit

integration-tests:
	pytest -q tests/integration

e2e-tests:
	pytest -q tests/e2e

smoke-tests:
	pytest -q tests/smoke

contract-tests:
	pytest -q tests/contracts

tests-with-coverage:
	pytest -q tests --cov=src/faith_echo --cov=services

tests-all:
	pytest -q tests

precommit:
	pre-commit run --all-files

poetry-lock:
	poetry lock

poetry-install:
	poetry install --with dev --no-interaction --no-root

build:
	docker compose build

proto:
	python -m grpc_tools.protoc \
		-I src/faith_echo/proto \
		--python_out=src/faith_echo/proto \
		src/faith_echo/proto/language_service.proto
