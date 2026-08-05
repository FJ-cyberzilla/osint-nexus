# ==========================================================================
#  FJ™ CYBERTRONIC SYSTEMS • OSINT NEXUS RECON ENGINE
# ==========================================================================
#  Version : 3.1.7
#  License : MIT
# ==========================================================================

# --- ANSI 256-Color Palette & Styling ---
C_CYN    := \033[38;5;45m
C_BLU    := \033[38;5;39m
C_PUR    := \033[38;5;141m
C_PNK    := \033[38;5;201m
C_ORG    := \033[38;5;208m
C_YEL    := \033[38;5;220m
C_GRN    := \033[38;5;118m
C_RED    := \033[38;5;196m
C_WHT    := \033[1;37m
C_GRY    := \033[38;5;242m
C_DIM    := \033[38;5;238m
RST      := \033[0m
B        := \033[1m

# --- Configuration & Environment Detection ---
PYTHONPATH   := .
SHELL        := /bin/bash
UV           := $(shell command -v uv 2> /dev/null)
PYTEST       := pytest
RUFF         := ruff

# Detect Termux / Android environment
IS_TERMUX    := $(shell if [ -d "/data/data/com.termux" ] || uname -o 2>/dev/null | grep -iq "android"; then echo "true"; else echo "false"; fi)

.PHONY: help install install-core install-full sync run health db-info test lint format clean

# --- Visual Animation Helper ---
define animate_status
	@sp='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'; \
	delay=0.05; \
	for i in {1..15}; do \
		printf "\r  $(C_CYN)$${sp:i%10:1}$(RST)  $(C_WHT)%s$(RST)..." "$(1)"; \
		sleep $$delay; \
	done; \
	printf "\r\033[K"
endef

# --- Default Target ---
help:
	@clear
	@echo ""
	@echo -e "  $(C_PUR)╭──────────────────────────────────────────────────────────╮$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_CYN)██████╗ ███████╗██╗███╗   ██╗████████╗$(RST) $(C_PNK)███╗   ██╗██╗██╗$(RST)  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_CYN)██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝$(RST) $(C_PNK)████╗  ██║██║██║$(RST)  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_CYN)██║   ██║███████╗██║██╔██╗ ██║   ██║   $(RST) $(C_PNK)██╔██╗ ██║██║██║$(RST)  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_CYN)██║   ██║╚════██║██║██║╚██╗██║   ██║   $(RST) $(C_PNK)██║╚██╗██║██║╚═╝$(RST)  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_CYN)╚██████╔╝███████║██║██║ ╚████║   ██║   $(RST) $(C_PNK)██║ ╚████║██║██╗$(RST)  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)   $(C_DIM)╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝   $(RST) $(C_DIM)╚═╝  ╚═══╝╚═╝╚═╝$(RST)  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)├──────────────────────────────────────────────────────────┤$(RST)"
	@echo -e "  $(C_PUR)│$(RST) $(C_WHT)$(B)FJ™ Cybertronic Systems$(RST) $(C_GRY)•$(RST) $(C_ORG)v3.1.7$(RST) $(C_GRY)•$(RST) $(C_PUR)Dev: FJ-cyberzilla$(RST)  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)├──────────────────────────────────────────────────────────┤$(RST)"
	@echo -e "  $(C_PUR)│$(RST) $(C_YEL)$(B)SYSTEM COMMANDS & OPERATIONAL MENU$(RST)                       $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)                                                          $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_CYN)📦 [SETUP & ENVIRONMENT]$(RST)                               $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make install$(RST)      $(C_GRY)→$(RST) Auto-detect platform & install setup   $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make install-core$(RST) $(C_GRY)→$(RST) Pure-Python setup (Termux/Mobile)    $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make install-full$(RST) $(C_GRY)→$(RST) Complete suite (PyQt6/Playwright)     $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make sync$(RST)         $(C_GRY)→$(RST) Sync virtual environment dependencies $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)                                                          $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_PNK)🎯 [EXECUTION]$(RST)                                          $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make run$(RST)          $(C_GRY)→$(RST) Initiate target username scan         $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)                                                          $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_GRN)📊 [TELEMETRY & DATABASE]$(RST)                                $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make health$(RST)       $(C_GRY)→$(RST) Run network/provider health diagnostics $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make db-info$(RST)      $(C_GRY)→$(RST) Inspect local scan SQLite database    $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)                                                          $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)  $(C_ORG)🛠️  [DEVELOPMENT & QUALITY]$(RST)                               $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make test$(RST)         $(C_GRY)→$(RST) Execute full test suite with coverage $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make lint$(RST)         $(C_GRY)→$(RST) Verify code quality via Ruff          $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make format$(RST)       $(C_GRY)→$(RST) Automatically format codebase         $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)│$(RST)    $(C_WHT)make clean$(RST)        $(C_GRY)→$(RST) Purge build artifacts, cache, and DB  $(C_PUR)│$(RST)"
	@echo -e "  $(C_PUR)╰──────────────────────────────────────────────────────────╯$(RST)"
	@echo ""

# --- Smart Installation Targets ---
install:
	@$(call animate_status,"Detecting environment profile")
	@if [ "$(IS_TERMUX)" = "true" ]; then \
		echo -e "  $(C_ORG)📱 Android/Termux detected! Running Core installation...$(RST)"; \
		$(MAKE) --no-print-directory install-core; \
	else \
		echo -e "  $(C_CYN)💻 Desktop Linux/Unix detected! Running Full installation...$(RST)"; \
		$(MAKE) --no-print-directory install-full; \
	fi

install-core:
	@$(call animate_status,"Installing Pure-Python Core Engine")
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e . || { echo -e "  $(C_RED)❌ Core installation failed.$(RST)"; exit 1; }; \
	else \
		pip install -e . || { echo -e "  $(C_RED)❌ Core installation failed.$(RST)"; exit 1; }; \
	fi
	@echo -e "  $(C_GRN)✔ Core Engine installed successfully (Termux Ready).$(RST)\n"

install-full:
	@$(call animate_status,"Installing Full Suite (Speedups + GUI + Browser)")
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e ".[full]" || { echo -e "  $(C_RED)❌ Full installation failed.$(RST)"; exit 1; }; \
	else \
		pip install -e ".[full]" || { echo -e "  $(C_RED)❌ Full installation failed.$(RST)"; exit 1; }; \
	fi
	@echo -e "  $(C_GRN)✔ Full OSINT Suite installed successfully.$(RST)\n"

sync:
	@$(call animate_status,"Synchronizing Virtual Environment")
	@if [ -n "$(UV)" ]; then \
		$(UV) sync || { echo -e "  $(C_RED)❌ Environment sync failed.$(RST)"; exit 1; }; \
	else \
		pip install -e . || { echo -e "  $(C_RED)❌ Environment sync failed.$(RST)"; exit 1; }; \
	fi
	@echo -e "  $(C_GRN)✔ Virtual environment synchronized.$(RST)\n"

# --- Operations ---
run:
	@uname="$(USERNAME)"; \
	if [ -z "$$uname" ]; then \
		echo ""; \
		echo -e "  $(C_CYN)╭── Target Username Selection ──────────────────────╮$(RST)"; \
		echo -e "  $(C_CYN)│$(RST) Enter Username $(C_PNK)(or 'q' / 'cancel' to exit)$(RST):"; \
		while [ -z "$$uname" ]; do \
			echo -ne "  $(C_CYN)► $(RST)"; \
			read uname; \
			if [ "$$uname" = "cancel" ] || [ "$$uname" = "q" ]; then \
				echo -e "  $(C_YEL)⚠️  Operation cancelled.$(RST)\n"; \
				exit 0; \
			elif [ -z "$$uname" ]; then \
				echo -e "  $(C_RED)❌ Username cannot be empty. Try again.$(RST)"; \
			fi; \
		done; \
		echo -e "  $(C_CYN)╰───────────────────────────────────────────────────╯$(RST)"; \
	fi; \
	echo -e "\n  $(C_ORG)🚀 Initiating OSINT Recon Scan for:$(RST) $(C_WHT)$(B)$$uname$(RST)"; \
	export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main scan --username $$uname || { echo -e "  $(C_RED)❌ Scan aborted or failed.$(RST)"; exit 1; }

health:
	@$(call animate_status,"Running Network & Provider Health Diagnostics")
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main health || { echo -e "  $(C_RED)❌ Health check failed.$(RST)"; exit 1; }

db-info:
	@$(call animate_status,"Querying Local Recon Database")
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main db-info || { echo -e "  $(C_RED)❌ Database inspection failed.$(RST)"; exit 1; }

# --- Development & Quality Control ---
test:
	@$(call animate_status,"Executing Pytest Test Suite")
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTEST) --cov=osint_nexus tests/ || { echo -e "  $(C_RED)❌ Test suite failed.$(RST)"; exit 1; }

lint:
	@$(call animate_status,"Analyzing Code Quality with Ruff")
	@$(RUFF) check . || { echo -e "  $(C_RED)❌ Linting errors detected.$(RST)"; exit 1; }
	@echo -e "  $(C_GRN)✔ Codebase clean. Zero linting issues.$(RST)\n"

format:
	@$(call animate_status,"Formatting Codebase")
	@$(RUFF) format . || { echo -e "  $(C_RED)❌ Code formatting failed.$(RST)"; exit 1; }
	@echo -e "  $(C_GRN)✔ Formatting applied successfully.$(RST)\n"

clean:
	@$(call animate_status,"Purging Cache, Artifacts, and Temporary Files")
	@rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov *.egg-info *.egg build dist .venv
	@rm -f data/*.db
	@rm -rf logs/* log/*
	@find . -type d -name "__pycache__" -exec rm -rf {} + >/dev/null 2>&1 || true
	@if [ -n "$(UV)" ]; then $(UV) cache clean >/dev/null 2>&1 || true; fi
	@echo -e "  $(C_GRN)✔ System cleanup complete.$(RST)\n"
