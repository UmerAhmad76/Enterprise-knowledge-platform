.PHONY: up down install dev-api test lint

up:
	docker compose -f deploy/docker/docker-compose.yml up -d

down:
	docker compose -f deploy/docker/docker-compose.yml down

install:
	cd packages/core && pip install -e . && cd ../../apps/api && pip install -e ".[dev]"

dev-api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

test:
	cd apps/api && pytest -q

lint:
	cd apps/api && ruff check app