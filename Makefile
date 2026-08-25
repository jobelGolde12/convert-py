.PHONY: help install dev test lint format migrate run web worker sweeper clean docker-build docker-up docker-down

help:
	@echo "Convert-Py Makefile"
	@echo ""
	@echo "  install        Install dependencies"
	@echo "  dev            Start dev server (uvicorn + reload)"
	@echo "  test           Run pytest"
	@echo "  lint           Run ruff"
	@echo "  format         Format with ruff"
	@echo "  migrate        Run alembic migrations"
	@echo "  makemigrations Create alembic migration"
	@echo "  run            Start production server"
	@echo "  web            Start web + worker via docker-compose"
	@echo "  clean          Remove temp files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	ruff check app tests

format:
	ruff format app tests

makemigrations:
	alembic revision --autogenerate -m "$(m)"

migrate:
	alembic upgrade head

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

web:
	docker compose -f docker/docker-compose.yml up --build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist .eggs