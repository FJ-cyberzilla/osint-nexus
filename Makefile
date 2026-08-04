# ==========================================================================
# FJ™ CYBERTRONIC SYSTEMS - ADVANCED OSINT RECONNAISSANCE
# ==========================================================================
# Refactored for better design and error handling
# ==========================================================================

# --- Colors ---
P_1      := \033[38;5;129m
P_2      := \033[38;5;135m
P_3      := \033[38;5;141m
P_4      := \033[38;5;177m
P_5      := \033[38;5;207m
P_6      := \033[38;5;213m
ORG      := \033[38;5;208m
ORG_L    := \033[38;5;214m
WHT      := \033[1;37m
GRY      := \033[38;5;242m
GRN      := \033[1;32m
CYN      := \033[1;36m
RED      := \033[1;31m
YEL      := \033[38;5;226m
PUR_L    := \033[38;5;183m
RST      := \033[0m
B        := \033[1m

# --- Configuration ---
PYTHONPATH   := .
SHELL        := /bin/bash
UV           := $(shell command -v uv 2> /dev/null)
PYTEST       := pytest
RUFF         := ruff

# --- Helper Functions ---
define check_uv
	@if [ -z "$(UV)" ]; then \
		echo -e "$(RED)Error: uv is not installed. Please install it first.$(RST)"; \
		exit 1; \
	fi
endef

.PHONY: help install sync run health db-info test lint format clean

# --- Targets ---
help:
	@echo ""
	@echo -e "  $(ORG)╭──────────────────────────────────────╮$(RST)"
	@echo -e "  $(ORG)│$(RST)  $(P_1)  ██████╗ ███████╗██╗███╗   ██╗████████╗$(RST)  $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)  $(P_2) ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝$(RST)  $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)  $(P_3) ╚██████╔╝███████║██║██║ ╚████║   ██║   $(RST)  $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)  $(P_4)  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗$(RST)  $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)  $(P_5)  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝$(RST)  $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)  $(P_6)  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║$(RST)  $(ORG)│$(RST)"
	@echo -e "  $(ORG)├──────────────────────────────────────┤$(RST)"
	@echo -e "  $(ORG)│$(RST) $(WHT)FJ™ Cybertronic Systems$(RST)  $(GRY)•$(RST)  $(ORG_L)$(B)Dev:$(RST) $(P_4)FJ-cyberzilla$(RST)  $(ORG)│$(RST)"
	@echo -e "  $(ORG)├──────────────────────────────────────┤$(RST)"
	@echo -e "  $(ORG)│$(RST) $(ORG_L)$(B)SYSTEM COMMANDS & OPERATIONAL MENU$(RST)        $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)                                        $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST) $(P_3)📦 [SETUP]$(RST)                              $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make install$(RST)   $(GRY)→$(RST) $(WHT)Install dependencies$(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make sync$(RST)      $(GRY)→$(RST) $(WHT)Sync environment    $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)                                        $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST) $(CYN)🎯 [EXECUTION]$(RST)                          $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make run$(RST)       $(GRY)→$(RST) $(WHT)Initiate scan       $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)                                        $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST) $(GRN)📊 [TELEMETRY]$(RST)                          $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make health$(RST)    $(GRY)→$(RST) $(WHT)Check network       $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make db-info$(RST)   $(GRY)→$(RST) $(WHT)Inspect database    $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)                                        $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST) $(ORG_L)🛠️  [DEV TOOLS]$(RST)                          $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make test$(RST)      $(GRY)→$(RST) $(WHT)Execute test suite  $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make lint$(RST)      $(GRY)→$(RST) $(WHT)Verify code quality $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make format$(RST)    $(GRY)→$(RST) $(WHT)Format code         $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)│$(RST)   $(WHT)make clean$(RST)     $(GRY)→$(RST) $(WHT)Purge artifacts     $(RST)    $(ORG)│$(RST)"
	@echo -e "  $(ORG)╰──────────────────────────────────────╯$(RST)"
	@echo ""

install:
	$(check_uv)
	@echo -e "$(ORG)⚡ Installing dependencies...$(RST)"
	@$(UV) sync || { echo -e "$(RED)Installation failed.$(RST)"; exit 1; }
	@echo -e "$(GRN)✔ Installed successfully.$(RST)"

sync:
	$(check_uv)
	@echo -e "$(ORG)⚡ Syncing environment...$(RST)"
	@$(UV) sync || { echo -e "$(RED)Sync failed.$(RST)"; exit 1; }
	@echo -e "$(GRN)✔ Environment updated.$(RST)"

run:
	@uname="$(USERNAME)"; \
	if [ -z "$$uname" ]; then \
		echo -e "$(ORG)Enter Username $(PUR_L)(type 'q' to exit):$(RST)"; \
		while [ -z "$$uname" ]; do \
			echo -ne "$(ORG)► $(RST)"; \
			read uname; \
			if [ "$$uname" = "cancel" ] || [ "$$uname" = "q" ]; then \
				echo -e "$(YEL)Operation cancelled.$(RST)"; \
				exit 0; \
			elif [ -z "$$uname" ]; then \
				echo -e "$(RED)Username cannot be empty. Please try again.$(RST)"; \
			fi; \
		done; \
	fi; \
	echo -e "$(ORG)Initiating scan for:$(RST) $(B)$$uname$(RST)"; \
	export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main scan --username $$uname || { echo -e "$(RED)Scan failed.$(RST)"; exit 1; }

health:
	@echo -e "$(ORG)Checking network status...$(RST)"
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main health || { echo -e "$(RED)Health check failed.$(RST)"; exit 1; }

db-info:
	@echo -e "$(ORG)Inspecting database...$(RST)"
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main db-info || { echo -e "$(RED)Database inspection failed.$(RST)"; exit 1; }

test:
	@echo -e "$(ORG)Running tests...$(RST)"
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTEST) --cov=osint_nexus tests/ || { echo -e "$(RED)Tests failed.$(RST)"; exit 1; }

lint:
	@echo -e "$(ORG)Checking quality...$(RST)"
	@$(RUFF) check . || { echo -e "$(RED)Linting failed.$(RST)"; exit 1; }
	@echo -e "$(GRN)✔ Linting clean.$(RST)"

format:
	@echo -e "$(ORG)Applying formatting...$(RST)"
	@$(RUFF) format . || { echo -e "$(RED)Formatting failed.$(RST)"; exit 1; }
	@echo -e "$(GRN)✔ Formatted.$(RST)"

clean:
	@echo -e "$(RED)Purging artifacts...$(RST)"
	@rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov *.egg-info *.egg build dist .venv
	@rm -f data/*.db
	@rm -rf logs/* log/*
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@$(UV) cache clean >/dev/null 2>&1 || true
	@echo -e "$(GRN)✔ Cleanup complete.$(RST)"
