# ==========================================================================
# FJ™ CYBERTRONIC SYSTEMS - ADVANCED OSINT RECONNAISSANCE
# ==========================================================================
# Developer   : FJ-cyberzilla
# Base Theme  : Cyber-Orange & Purple Cyberpunk Gradient
# Layout      : Mobile & Desktop Optimized (60-Column Grid)
# ==========================================================================

# --- Color Palette (Purple Gradient & Cyber-Orange) ---
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
RST      := \033[0m
B        := \033[1m

# --- Environment Settings ---
PYTHONPATH   := .
SHELL        := /bin/bash
UV_LINK_MODE := copy
export UV_LINK_MODE

.PHONY: help install sync run health db-info test lint format clean

# --- Interactive TUI Dashboard ---
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

# --- Command Implementations ---

install:
	@echo -e "$(ORG)╭─[ $(P_3)📦 INSTALLATION$(ORG) ]──────────────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Installing dependencies...$(RST)"
	@uv sync
	@echo -e "$(ORG)│$(RST) $(GRN)✔ Installed successfully.$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"

sync:
	@echo -e "$(ORG)╭─[ $(P_3)📦 SYNCHRONIZATION$(ORG) ]───────────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Syncing environment...$(RST)"
	@uv sync
	@echo -e "$(ORG)│$(RST) $(GRN)✔ Environment updated.$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"

run:
	@if [ -z "$(USERNAME)" ]; then \
		echo -e "$(ORG)╭─[ $(CYN)🎯 TARGET ACQUISITION$(ORG) ]───────╮$(RST)"; \
		echo -ne "$(ORG)│$(RST) $(CYN)►$(RST) $(WHT)Enter Username: $(RST)"; \
		read uname; \
		echo -e "$(ORG)│$(RST) $(GRN)✔ Locked:$(RST) $(ORG_L)$$uname$(RST)"; \
		echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"; \
		echo -e "$(P_3)►$(RST) $(WHT)Initiating scan...$(RST)\n"; \
		export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main scan --username $$uname; \
	else \
		echo -e "$(ORG)╭─[ $(CYN)🎯 TARGET ACQUISITION$(ORG) ]───────╮$(RST)"; \
		echo -e "$(ORG)│$(RST) $(GRN)✔ Locked:$(RST) $(ORG_L)$(USERNAME)$(RST)"; \
		echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"; \
		echo -e "$(P_3)►$(RST) $(WHT)Initiating scan...$(RST)\n"; \
		export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main scan --username $(USERNAME); \
	fi

health:
	@echo -e "$(ORG)╭─[ $(GRN)📊 NETWORK TELEMETRY$(ORG) ]──────────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Checking network status...$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main health

db-info:
	@echo -e "$(ORG)╭─[ $(GRN)🗄️  DATABASE ARCHITECTURE$(ORG) ]──────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Inspecting database...$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main db-info

test:
	@echo -e "$(ORG)╭─[ $(ORG_L)🧪 TEST SUITE$(ORG) ]──────────────────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Running tests...$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"
	@export PYTHONPATH=$(PYTHONPATH) && pytest tests/

lint:
	@echo -e "$(ORG)╭─[ $(ORG_L)🔍 CODE QUALITY$(ORG) ]──────────────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Checking quality...$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"
	@ruff check .
	@echo -e "$(GRN)✔ Linting clean.$(RST)"

format:
	@echo -e "$(ORG)╭─[ $(ORG_L)⚙️  FORMATTING$(ORG) ]──────────────────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Applying formatting...$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"
	@ruff format .
	@echo -e "$(GRN)✔ Formatted.$(RST)"

clean:
	@echo -e "$(ORG)╭─[ $(RED)🧹 SYSTEM PURGE$(ORG) ]───────────────╮$(RST)"
	@echo -e "$(ORG)│$(RST) $(GRY)⚡ Purging artifacts...$(RST)"
	@rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov *.egg-info *.egg build dist .venv
	@rm -f data/*.db
	@rm -rf logs/* log/*
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@uv cache clean >/dev/null 2>&1 || true
	@echo -e "$(ORG)│$(RST) $(GRN)✔ Cleanup complete.$(RST)"
	@echo -e "$(ORG)╰──────────────────────────────────────╯$(RST)"
