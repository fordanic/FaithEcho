.PHONY: lint test precommit build proto

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

proto:
	python -m grpc_tools.protoc \
		-I src/faith_echo/proto \
		--python_out=src/faith_echo/proto \
		src/faith_echo/proto/language_service.proto
