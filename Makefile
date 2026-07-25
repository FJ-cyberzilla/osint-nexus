# ==========================================================================
# OSINT NEXUS - ADVANCED RECONNAISSANCE
# ==========================================================================
# Base Theme: Orange
# ==========================================================================

# Colors & Formatting
ORANGE      := \033[38;5;208m
BOLD        := \033[1m
CYAN        := \033[36m
GREEN       := \033[32m
RESET       := \033[0m
MARGIN      := "      "

# Environment Settings
PYTHONPATH   := .
SHELL        := /bin/bash
UV_LINK_MODE := copy
export UV_LINK_MODE

.PHONY: help sync run health db-info test lint format clean

# --- Help Menu ---
help:
	@echo ""
	@echo -e "$(ORANGE)$(BOLD)░█▀█░█▀▀░█░█░█░█░█▀▀░░░░░░░░░█▀█░█▀▀░▀█▀░█▀█░▀█▀$(RESET)"
	@echo -e "$(ORANGE)$(BOLD)░█░█░█▀▀░▄▀▄░█░█░▀▀█░░░▄▄▄░░░█░█░▀▀█░░█░░█░█░░█░$(RESET)"
	@echo -e "$(ORANGE)$(BOLD)░▀░▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░░░░░░░░░▀▀▀░▀▀▀░▀▀▀░▀░▀░░▀░$(RESET)"
	@echo ""
	@echo -e "  $(ORANGE)============================================================$(RESET)"
	@echo -e "  $(MARGIN)$(CYAN)$(BOLD)DEVELOPMENT & OPERATIONAL COMMANDS$(RESET)"
	@echo -e "  $(ORANGE)============================================================$(RESET)"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)sync$(RESET)      $(CYAN)•$(RESET)  Advanced synchronization of dependencies"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)run$(RESET)       $(CYAN)•$(RESET)  Execute OSINT scan (prompts for username)"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)health$(RESET)    $(CYAN)•$(RESET)  Check provider network status & circuit breakers"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)db-info$(RESET)   $(CYAN)•$(RESET)  Inspect schema architecture and database records"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)test$(RESET)      $(CYAN)•$(RESET)  Run comprehensive test suite"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)lint$(RESET)      $(CYAN)•$(RESET)  Verify code quality and complexity"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)format$(RESET)    $(CYAN)•$(RESET)  Apply consistent code formatting"
	@echo -e "  $(MARGIN)$(ORANGE)$(BOLD)clean$(RESET)     $(CYAN)•$(RESET)  Purge caches and temporary artifacts"
	@echo -e "  $(ORANGE)============================================================$(RESET)"
	@echo -e "  $(MARGIN)$(CYAN)$(BOLD)Usage:$(RESET)  make run [USERNAME=<name>]"
	@echo ""

# --- Implementation ---

sync:
	@echo -e "$(ORANGE)>>$(RESET) $(BOLD)Synchronizing environment...$(RESET)"
	@uv sync --all-extras --dev
	@echo -e "$(GREEN)✔ Environment up to date.$(RESET)"

run:
	@echo -e "$(ORANGE)┌────────────────────────────────────────────────────────────┐$(RESET)"
	@if [ -z "$(USERNAME)" ]; then \
		echo -ne "$(ORANGE)│ $(RESET) $(BOLD)Enter Target Username: $(RESET)"; \
		read uname; \
		echo -e "$(ORANGE)│ $(RESET) $(BOLD)Initiating scan for:$(RESET) $(CYAN)$$uname$(RESET)"; \
		echo -e "$(ORANGE)└────────────────────────────────────────────────────────────┘$(RESET)"; \
		export PYTHONPATH=$(PYTHONPATH) && uv run python -m osint_nexus.cli.main --username $$uname; \
	else \
		echo -e "$(ORANGE)│ $(RESET) $(BOLD)Initiating scan for:$(RESET) $(CYAN)$(USERNAME)$(RESET)"; \
		echo -e "$(ORANGE)└────────────────────────────────────────────────────────────┘$(RESET)"; \
		export PYTHONPATH=$(PYTHONPATH) && uv run python -m osint_nexus.cli.main --username $(USERNAME); \
	fi

health:
	@echo -e "$(ORANGE)>>$(RESET) $(BOLD)Querying provider networks & circuit-breaker states...$(RESET)"
	@export PYTHONPATH=$(PYTHONPATH) && uv run python -m osint_nexus.cli.main health

db-info:
	@echo -e "$(ORANGE)>>$(RESET) $(BOLD)Accessing local telemetry database metrics...$(RESET)"
	@export PYTHONPATH=$(PYTHONPATH) && uv run python -m osint_nexus.cli.main db-info

test:
	@echo -e "$(ORANGE)>>$(RESET) $(BOLD)Executing test suite...$(RESET)"
	@export PYTHONPATH=$(PYTHONPATH) && uv run pytest tests/

lint:
	@echo -e "$(ORANGE)>>$(RESET) $(BOLD)Analyzing code quality...$(RESET)"
	@uv run ruff check .

format:
	@echo -e "$(ORANGE)>>$(RESET) $(BOLD)Formatting codebase...$(RESET)"
	@uv run ruff format .

clean:
	@echo -e "$(ORANGE)>>$(RESET) $(BOLD)Purging artifacts...$(RESET)"
	@rm -rf __pycache__ .pytest_cache .ruff_cache .coverage htmlcov *.egg-info build dist data/*.db logs/*.log
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo -e "$(GREEN)✔ Cleanup complete.$(RESET)"
