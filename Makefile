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
I        := \033[3m

# --- Configuration & Environment Detection ---
PYTHONPATH   := .
SHELL        := /bin/bash
UV           := $(shell command -v uv 2> /dev/null)
PYTEST       := pytest
RUFF         := ruff

# Enhanced precise system detection
IS_TERMUX    := $(shell [ -d "/data/data/com.termux" ] && echo "true" || echo "false")
IS_ANDROID   := $(shell uname -o 2>/dev/null | grep -qi "android" && echo "true" || echo "false")
IS_LINUX     := $(shell uname -s 2>/dev/null | grep -qi "linux" && echo "true" || echo "false")
IS_MACOS     := $(shell uname -s 2>/dev/null | grep -qi "darwin" && echo "true" || echo "false")
IS_WSL       := $(shell grep -qi "microsoft" /proc/version 2>/dev/null && echo "true" || echo "false")
IS_CONTAINER := $(shell [ -f /.dockerenv ] && echo "true" || echo "false")
HAS_GUI      := $(shell [ -n "$$DISPLAY" ] && echo "true" || echo "false")

.PHONY: help install install-core install-full sync run health db-info test lint format clean

# --- Smooth Animated Spinner ---
define animate_status
	@sp='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'; \
	delay=0.04; \
	for i in $(shell seq 1 20); do \
		printf "\r  $(C_CYN)$${sp:$$((i % 10)):1}$(RST)  $(C_WHT)%s$(RST)..." "$(1)"; \
		sleep $$delay; \
	done; \
	printf "\r\033[K"
endef

# --- Compact Banner (reduced size) ---
define show_banner
	@printf "\n  $(C_PUR)╭─$(C_CYN) FJ™ Cybertronic $(C_ORG)v3.1.7$(C_PUR) ───$(C_GRY)◆$(C_PUR)───╮$(RST)\n"
	@printf "  $(C_PUR)│$(RST)  $(C_WHT)%s$(RST)  $(C_PUR)│$(RST)\n" "OSINT Nexus Recon"
	@printf "  $(C_PUR)╰──────────────────────────╯$(RST)\n\n"
endef

# --- Default Target ---
help:
	@clear
	$(call show_banner)
	@printf "  $(C_YEL)$(B)OPERATIONAL COMMANDS$(RST)\n\n"
	@printf "  $(C_CYN)📦 SETUP$(RST)\n"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Auto-detect & install\n" "make install"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Pure-Python (Termux/Mobile)\n" "make install-core"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Complete suite (GUI+Browser)\n" "make install-full"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Sync venv dependencies\n" "make sync"
	@printf "\n  $(C_PNK)🎯 EXECUTION$(RST)\n"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Target username scan\n" "make run"
	@printf "\n  $(C_GRN)📊 TELEMETRY$(RST)\n"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Network health diagnostics\n" "make health"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Inspect SQLite database\n" "make db-info"
	@printf "\n  $(C_ORG)🛠️  DEV TOOLS$(RST)\n"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Test suite + coverage\n" "make test"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Code quality check\n" "make lint"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Auto-format codebase\n" "make format"
	@printf "    $(C_WHT)%-18s$(RST) $(C_GRY)→$(RST) Purge cache & artifacts\n" "make clean"
	@printf "\n"

# --- Smart Installation with Precise Detection ---
install:
	@$(call animate_status,"Precise environment detection")
	@sleep 0.3
	@printf "\n  $(C_BLU)🔍 System Analysis:$(RST)\n"
	@[ "$(IS_TERMUX)" = "true" ] && printf "  $(C_ORG)📱 Termux environment detected$(RST)\n" || true
	@[ "$(IS_ANDROID)" = "true" ] && [ "$(IS_TERMUX)" = "false" ] && printf "  $(C_ORG)📱 Android (non-Termux) detected$(RST)\n" || true
	@[ "$(IS_LINUX)" = "true" ] && printf "  $(C_CYN)🐧 Linux detected$(RST)\n" || true
	@[ "$(IS_MACOS)" = "true" ] && printf "  $(C_PNK)🍎 macOS detected$(RST)\n" || true
	@[ "$(IS_WSL)" = "true" ] && printf "  $(C_BLU)🪟 WSL (Windows Subsystem) detected$(RST)\n" || true
	@[ "$(IS_CONTAINER)" = "true" ] && printf "  $(C_PUR)📦 Container environment$(RST)\n" || true
	@[ "$(HAS_GUI)" = "true" ] && printf "  $(C_GRN)🖥️  GUI display available$(RST)\n" || printf "  $(C_GRY)🖥️  No GUI (headless)$(RST)\n"
	@printf "\n"
	@if [ "$(IS_TERMUX)" = "true" ] || [ "$(IS_ANDROID)" = "true" ]; then \
		printf "  $(C_ORG)➡️  Installing Core (mobile-optimized)...$(RST)\n"; \
		sleep 0.5; \
		$(MAKE) --no-print-directory install-core; \
	elif [ "$(HAS_GUI)" = "false" ] || [ "$(IS_CONTAINER)" = "true" ]; then \
		printf "  $(C_BLU)➡️  Installing Core (headless/server)...$(RST)\n"; \
		sleep 0.5; \
		$(MAKE) --no-print-directory install-core; \
	else \
		printf "  $(C_CYN)➡️  Installing Full suite (desktop)...$(RST)\n"; \
		sleep 0.5; \
		$(MAKE) --no-print-directory install-full; \
	fi

install-core:
	@$(call animate_status,"Core Engine Installation")
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e . 2>&1 | tail -1 || { printf "\n  $(C_RED)❌ Core installation failed$(RST)\n"; exit 1; }; \
	else \
		pip install -e . 2>&1 | tail -1 || { printf "\n  $(C_RED)❌ Core installation failed$(RST)\n"; exit 1; }; \
	fi
	@printf "\r\033[K  $(C_GRN)✔ Core Engine ready$(RST)\n"

install-full:
	@$(call animate_status,"Full Suite Installation")
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e ".[full]" 2>&1 | tail -1 || { printf "\n  $(C_RED)❌ Full installation failed$(RST)\n"; exit 1; }; \
	else \
		pip install -e ".[full]" 2>&1 | tail -1 || { printf "\n  $(C_RED)❌ Full installation failed$(RST)\n"; exit 1; }; \
	fi
	@printf "\r\033[K  $(C_GRN)✔ Full OSINT Suite ready$(RST)\n"

sync:
	@$(call animate_status,"Syncing Environment")
	@if [ -n "$(UV)" ]; then \
		$(UV) sync || { printf "\n  $(C_RED)❌ Sync failed$(RST)\n"; exit 1; }; \
	else \
		pip install -e . || { printf "\n  $(C_RED)❌ Sync failed$(RST)\n"; exit 1; }; \
	fi
	@printf "\r\033[K  $(C_GRN)✔ Environment synchronized$(RST)\n"

# --- Operations ---
run:
	@$(call show_banner)
	@uname="$(USERNAME)"; \
	if [ -z "$$uname" ]; then \
		printf "  $(C_CYN)╭─ Target Selection ─╮$(RST)\n"; \
		printf "  $(C_CYN)│$(RST) Username $(C_PNK)(q=cancel)$(RST): "; \
		while [ -z "$$uname" ]; do \
			read uname; \
			if [ "$$uname" = "cancel" ] || [ "$$uname" = "q" ]; then \
				printf "\n  $(C_YEL)⚠️  Cancelled$(RST)\n\n"; \
				exit 0; \
			elif [ -z "$$uname" ]; then \
				printf "  $(C_RED)❌ Required$(RST): "; \
			fi; \
		done; \
		printf "  $(C_CYN)╰─────────────────────╯$(RST)\n"; \
	fi; \
	printf "\n  $(C_ORG)🚀 Recon: $(C_WHT)$(B)%s$(RST)\n\n" "$$uname"; \
	export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main scan --username $$uname || \
		{ printf "\n  $(C_RED)❌ Scan failed$(RST)\n"; exit 1; }

health:
	@$(call animate_status,"Health Diagnostics")
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main health || \
		{ printf "\n  $(C_RED)❌ Health check failed$(RST)\n"; exit 1; }

db-info:
	@$(call animate_status,"Database Query")
	@export PYTHONPATH=$(PYTHONPATH) && python -m osint_nexus.cli.main db-info || \
		{ printf "\n  $(C_RED)❌ Database inspection failed$(RST)\n"; exit 1; }

# --- Development & Quality Control ---
test:
	@$(call animate_status,"Running Test Suite")
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTEST) --cov=osint_nexus tests/ || \
		{ printf "\n  $(C_RED)❌ Tests failed$(RST)\n"; exit 1; }

lint:
	@$(call animate_status,"Code Quality Analysis")
	@$(RUFF) check . || { printf "\n  $(C_RED)❌ Linting errors$(RST)\n"; exit 1; }
	@printf "\r\033[K  $(C_GRN)✔ Code quality perfect$(RST)\n"

format:
	@$(call animate_status,"Formatting Codebase")
	@$(RUFF) format . || { printf "\n  $(C_RED)❌ Format failed$(RST)\n"; exit 1; }
	@printf "\r\033[K  $(C_GRN)✔ Code formatted$(RST)\n"

clean:
	@$(call animate_status,"System Cleanup")
	@rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov *.egg-info *.egg build dist .venv
	@rm -f data/*.db 2>/dev/null || true
	@rm -rf logs/* log/* 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@if [ -n "$(UV)" ]; then $(UV) cache clean >/dev/null 2>&1 || true; fi
	@printf "\r\033[K  $(C_GRN)✔ Cleanup complete$(RST)\n"
