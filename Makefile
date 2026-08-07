# ==========================================================================
#  FJ™ CYBERTRONIC SYSTEMS • OSINT NEXUS MATRIX ENGINE
# ==========================================================================
#  Version : 4.1.1
#  License : MIT
# ==========================================================================

# --- ANSI 256-Color Palette (Dedicated Functional Group Separation) ---
# Structural & Base Branding
C_CYN    := \033[38;5;45m    # Neon Cyan (Branding / Accents)
C_PUR    := \033[38;5;141m   # Deep Violet (Headers & Frames)
C_SLV    := \033[38;5;250m   # Metallic Silver (Subtitles & Standard Output)
C_DIM    := \033[38;5;238m   # Dark Slate Gray (Progress Dots & Dividers)

# Group 1: Setup & Engine Commands
C_ICE    := \033[38;5;123m   # Ice Blue (Setup Targets)

# Group 2: Execution & Operations
C_PNK    := \033[38;5;201m   # Cyber Magenta (Execution Targets)

# Group 3: Telemetry & Database Diagnostics
C_GRN    := \033[38;5;118m   # Matrix Green (Telemetry Targets & Success Indicators)

# Group 4: Quality & Development Tooling
C_ORG    := \033[38;5;208m   # Amber Gold (Dev Targets & Warnings)

# Error & Critical States
C_RED    := \033[38;5;196m   # Critical Red
C_YEL    := \033[38;5;220m   # Bright Yellow

RST      := \033[0m
B        := \033[1m

# --- Configuration & Environment Detection ---
PYTHONPATH   := .
SHELL        := /bin/bash
PYTHON       := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
UV           := $(shell command -v uv 2> /dev/null)
PYTEST       := pytest
RUFF         := ruff

# Environment detection flags
IS_TERMUX    := $(shell [ -d "/data/data/com.termux" ] && echo "true" || echo "false")
IS_ANDROID   := $(shell uname -o 2>/dev/null | grep -qi "android" && echo "true" || echo "false")
IS_LINUX     := $(shell uname -s 2>/dev/null | grep -qi "linux" && echo "true" || echo "false")
IS_MACOS     := $(shell uname -s 2>/dev/null | grep -qi "darwin" && echo "true" || echo "false")
IS_WSL       := $(shell grep -qi "microsoft" /proc/version 2>/dev/null && echo "true" || echo "false")
IS_CONTAINER := $(shell [ -f /.dockerenv ] || [ -f /run/.containerenv ] && echo "true" || echo "false")
HAS_GUI      := $(shell [ -n "$$DISPLAY" ] || [ -n "$$WAYLAND_DISPLAY" ] && echo "true" || echo "false")

.PHONY: help install install-core install-full sync run health db-info test lint format clean

# --- Quoted Animation Macro (Prevents Space/Word Splitting Bugs) ---
define animate_status
	@sp='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'; \
	delay=0.03; \
	msg="$(1)"; \
	for i in $$(seq 1 18); do \
		idx=$$((i % 10)); \
		char=$${sp:$$idx:1}; \
		printf "\r  $(C_CYN)[$(C_PUR)$${char}$(C_CYN)]$(RST) $(C_SLV)%s$(RST) $(C_DIM)...$(RST)" "$$msg"; \
		sleep $$delay; \
	done; \
	printf "\r\033[K"
endef

# --- Dashboard Header ---
define show_banner
	@printf "\n"
	@printf "  $(C_PUR)┌──────────────────────────────────────────────────────────────┐$(RST)\n"
	@printf "  $(C_PUR)│$(RST)  $(C_CYN)$(B)FJ™ CYBERTRONIC SYSTEMS$(RST)  $(C_DIM)•$(RST)  $(C_PUR)OSINT NEXUS MATRIX ENGINE$(RST)  $(C_PUR)│$(RST)\n"
	@printf "  $(C_PUR)│$(RST)  $(C_SLV)Cybernetic Intelligence Platform$(RST) $(C_DIM)|$(RST) $(C_ORG)v4.1.1$(RST)               $(C_PUR)│$(RST)\n"
	@printf "  $(C_PUR)└──────────────────────────────────────────────────────────────┘$(RST)\n\n"
endef

# --- Error & Troubleshooting Handler ---
define render_error
	printf "\n  $(C_RED)┌── [CRITICAL SUBSYSTEM FAILURE] ─────────────────────────────┐$(RST)\n"; \
	printf "  $(C_RED)│$(RST) $(C_ORG)Task Domain:$(RST) $(C_SLV)%s$(RST)\n" "$(1)"; \
	printf "  $(C_RED)│$(RST) $(C_RED)Root Cause :$(RST) $(C_SLV)%s$(RST)\n" "$(2)"; \
	printf "  $(C_RED)├── [ACTIONABLE TROUBLESHOOTING PATHS] ──────────────────────────┤$(RST)\n"; \
	printf "  $(C_RED)│$(RST) $(C_YEL)1.$(RST) Verify python interpreter & virtualenv setup\n"; \
	printf "  $(C_RED)│$(RST) $(C_YEL)2.$(RST) Execute system diagnostics: $(C_CYN)make health$(RST)\n"; \
	printf "  $(C_RED)│$(RST) $(C_YEL)3.$(RST) Re-synchronize environment: $(C_CYN)make sync$(RST)\n"; \
	printf "  $(C_RED)│$(RST) $(C_YEL)4.$(RST) Purge residual artifacts:   $(C_CYN)make clean$(RST)\n"; \
	printf "  $(C_RED)└──────────────────────────────────────────────────────────────┘$(RST)\n\n"
endef

# --- Operational Command Help Menu ---
help:
	@clear
	$(call show_banner)
	@printf "  $(C_CYN)$(B)OPERATIONAL COMMAND MATRIX$(RST)\n\n"
	@printf "  $(C_ICE)⚡ SETUP ENGINE$(RST)\n"
	@printf "    $(C_ICE)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Auto-detect environment & build package$(RST)\n" "make install"
	@printf "    $(C_ICE)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Pure-Python lightweight engine (Mobile/Termux)$(RST)\n" "make install-core"
	@printf "    $(C_ICE)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Complete workstation suite (GUI + Browsers)$(RST)\n" "make install-full"
	@printf "    $(C_ICE)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Synchronize virtual environment dependencies$(RST)\n" "make sync"
	@printf "\n  $(C_PNK)🎯 EXECUTION CORE$(RST)\n"
	@printf "    $(C_PNK)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Initiate targeted identity analysis scan$(RST)\n" "make run"
	@printf "\n  $(C_GRN)📊 TELEMETRY & DATA$(RST)\n"
	@printf "    $(C_GRN)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Network & subsystem health diagnostics$(RST)\n" "make health"
	@printf "    $(C_GRN)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Inspect SQLite matrix database state$(RST)\n" "make db-info"
	@printf "\n  $(C_ORG)🛠️  DEVELOPMENT TOOLING$(RST)\n"
	@printf "    $(C_ORG)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Run pytest test suite with coverage report$(RST)\n" "make test"
	@printf "    $(C_ORG)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Static code analysis & quality verification$(RST)\n" "make lint"
	@printf "    $(C_ORG)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Auto-format codebase using Ruff formatter$(RST)\n" "make format"
	@printf "    $(C_ORG)%-18s$(RST) $(C_DIM)→$(RST) $(C_SLV)Purge workspace cache, venvs & build artifacts$(RST)\n" "make clean"
	@printf "\n"

# --- Smart Environment Installation ---
install:
	@$(call animate_status,Analyzing System Architecture)
	@sleep 0.2
	@printf "\n  $(C_CYN)🔍 System Environment Analysis:$(RST)\n"
	@[ "$(IS_TERMUX)" = "true" ] && printf "  $(C_ORG)  ◈ Termux environment detected$(RST)\n" || true
	@[ "$(IS_ANDROID)" = "true" ] && [ "$(IS_TERMUX)" = "false" ] && printf "  $(C_ORG)  ◈ Android OS detected$(RST)\n" || true
	@[ "$(IS_LINUX)" = "true" ] && printf "  $(C_CYN)  ◈ Linux kernel detected$(RST)\n" || true
	@[ "$(IS_MACOS)" = "true" ] && printf "  $(C_PNK)  ◈ macOS Darwin detected$(RST)\n" || true
	@[ "$(IS_WSL)" = "true" ] && printf "  $(C_ICE)  ◈ Windows Subsystem for Linux (WSL) detected$(RST)\n" || true
	@[ "$(IS_CONTAINER)" = "true" ] && printf "  $(C_PUR)  ◈ Containerized Environment detected$(RST)\n" || true
	@[ "$(HAS_GUI)" = "true" ] && printf "  $(C_GRN)  ◈ Graphical Interface (GUI) available$(RST)\n" || printf "  $(C_DIM)  ◈ Headless terminal environment$(RST)\n"
	@printf "\n"
	@if [ "$(IS_TERMUX)" = "true" ] || [ "$(IS_ANDROID)" = "true" ]; then \
		printf "  $(C_ICE)⚡ Deploying Core Module (Mobile-Optimized)...$(RST)\n"; \
		sleep 0.3; \
		$(MAKE) --no-print-directory install-core; \
	elif [ "$(HAS_GUI)" = "false" ] || [ "$(IS_CONTAINER)" = "true" ]; then \
		printf "  $(C_ICE)⚡ Deploying Core Module (Headless/Server)...$(RST)\n"; \
		sleep 0.3; \
		$(MAKE) --no-print-directory install-core; \
	else \
		printf "  $(C_ICE)⚡ Deploying Full Workstation Suite...$(RST)\n"; \
		sleep 0.3; \
		$(MAKE) --no-print-directory install-full; \
	fi

install-core:
	@$(call animate_status,Installing Core Matrix Package)
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e . > /dev/null 2>&1 || { $(call render_error,INSTALL-CORE,UV package manager installation failed.); exit 1; }; \
	else \
		pip install -e . > /dev/null 2>&1 || { $(call render_error,INSTALL-CORE,Standard Pip package installation failed.); exit 1; }; \
	fi
	@printf "  $(C_GRN)✔ Core Engine initialized successfully$(RST)\n\n"

install-full:
	@$(call animate_status,Installing Full Workstation Suite)
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e ".[full]" > /dev/null 2>&1 || { $(call render_error,INSTALL-FULL,UV full feature installation failed.); exit 1; }; \
	else \
		pip install -e ".[full]" > /dev/null 2>&1 || { $(call render_error,INSTALL-FULL,Standard Pip full feature installation failed.); exit 1; }; \
	fi
	@printf "  $(C_GRN)✔ Full Workstation Suite operational$(RST)\n\n"

sync:
	@$(call animate_status,Synchronizing Environment Dependencies)
	@if [ "$(IS_TERMUX)" = "true" ] || [ "$(IS_ANDROID)" = "true" ]; then \
		pip install -e . || { $(call render_error,SYNC,Pip installation in mobile environment failed.); exit 1; }; \
	elif [ -n "$(UV)" ]; then \
		$(UV) sync || { $(call render_error,SYNC,UV virtualenv sync failed.); exit 1; }; \
	else \
		pip install -e . || { $(call render_error,SYNC,Pip installation fallback failed.); exit 1; }; \
	fi
	@printf "  $(C_GRN)✔ Virtual environment synchronized$(RST)\n\n"

# --- Target Execution Commands ---
run:
	@$(call show_banner)
	@uname="$(USERNAME)"; \
	if [ -z "$$uname" ]; then \
		printf "  $(C_PNK)┌── [Target Selection] ─────────────────────────────────────────┐$(RST)\n"; \
		printf "  $(C_PNK)│$(RST) Enter Target Username $(C_PUR)(type 'q' to abort)$(RST): "; \
		while [ -z "$$uname" ]; do \
			read uname; \
			if [ "$$uname" = "cancel" ] || [ "$$uname" = "q" ]; then \
				printf "\n  $(C_YEL)⚠️  Operation Aborted by Operator$(RST)\n\n"; \
				exit 0; \
			elif [ -z "$$uname" ]; then \
				printf "  $(C_RED)❌ Username Required$(RST): "; \
			fi; \
		done; \
		printf "  $(C_PNK)└───────────────────────────────────────────────────────────────┘$(RST)\n"; \
	fi; \
	printf "\n  $(C_PNK)🚀 Initiating Target Scan: $(C_ICE)$(B)%s$(RST)\n\n" "$$uname"; \
	export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m osint_nexus.cli.main scan --username $$uname || \
		{ $(call render_error,RUN,Target scan module execution encountered an unhandled error.); exit 1; }

health:
	@$(call animate_status,Running Network Diagnostics)
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m osint_nexus.cli.main health || \
		{ $(call render_error,HEALTH,System health telemetry failure detected.); exit 1; }

db-info:
	@$(call animate_status,Querying Database Metadata)
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m osint_nexus.cli.main db-info || \
		{ $(call render_error,DB-INFO,Unable to inspect or query SQLite database matrix.); exit 1; }

# --- Development & Code Quality Control ---
test:
	@$(call animate_status,Executing Test Suite)
	@mkdir -p logs
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTEST) --cov=osint_nexus --cov-report=xml:logs/coverage.xml tests/ || \
		{ $(call render_error,TEST,Pytest execution failed or code coverage threshold not met.); exit 1; }
	@printf "  $(C_GRN)✔ All unit tests passed successfully$(RST)\n\n"

lint:
	@$(call animate_status,Executing Code Quality Analysis)
	@$(RUFF) check . || { $(call render_error,LINT,Ruff linter detected formatting or code quality errors.); exit 1; }
	@printf "  $(C_GRN)✔ Code quality verification passed$(RST)\n\n"

format:
	@$(call animate_status,Formatting Codebase)
	@$(RUFF) format . || { $(call render_error,FORMAT,Ruff formatter failed to structure source files.); exit 1; }
	@printf "  $(C_GRN)✔ Codebase successfully formatted$(RST)\n\n"

clean:
	@$(call animate_status,Purging Workspace Caches and Build Artifacts)
	@rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov *.egg-info *.egg build dist .venv
	@rm -f data/*.db 2>/dev/null || true
	@rm -rf logs/* log/* 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@if [ -n "$(UV)" ]; then $(UV) cache clean >/dev/null 2>&1 || true; fi
	@printf "  $(C_GRN)✔ Workspace purged successfully$(RST)\n\n"
