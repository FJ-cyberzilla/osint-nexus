.PHONY: help build run test clean

help:
	@echo "Available commands:"
	@echo "  make build   : Install dependencies"
	@echo "  make run     : Run scan: make run USERNAME=<target>"
	@echo "  make test    : Run tests"
	@echo "  make clean   : Clean build artifacts"

build:
	pip install -r requirements.txt
	pip install .

run:
	@if [ -z "$(USERNAME)" ]; then \
		echo "Usage: make run USERNAME=<username>"; \
	else \
		export PYTHONPATH=. && python3 -m osint_nexus.cli.main --username $(USERNAME); \
	fi

test:
	export PYTHONPATH=. && pytest tests/

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov *.egg-info build dist osint_results.db osint.log
