.PHONY: help build run test lint format clean

help:
	@echo "Available commands:"
	@echo "  make build   : Sync dependencies"
	@echo "  make run     : Run scan: make run USERNAME=<target>"
	@echo "  make test    : Run tests"
	@echo "  make lint    : Run ruff linting"
	@echo "  make format  : Run ruff formatting"
	@echo "  make clean   : Clean build artifacts"

build:
	uv sync

run:
	@if [ -z "$(USERNAME)" ]; then \
		echo "Usage: make run USERNAME=<username>"; \
	else \
		export PYTHONPATH=. && uv run python -m osint_nexus.cli.main --username $(USERNAME); \
	fi

test:
	uv run pytest tests/

lint:
	uv run ruff check .

format:
	uv run ruff format .

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov *.egg-info build dist osint_results.db osint.log .venv
