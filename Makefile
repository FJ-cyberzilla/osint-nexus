# ==========================================================================
#  ✦ OSINT NEXUS ✦ FJ™ CYBERTRONIC SYSTEMS
#  ─── Cybernetic Intelligence Framework ───
#  Version : 4.1.1  |  License : MIT
# ==========================================================================

# ─── Terminal Color System ────────────────────────────────────────────────
C_CYN    := \033[38;5;45m
C_PUR    := \033[38;5;141m
C_BLU    := \033[38;5;75m
C_SLV    := \033[38;5;252m
C_DIM    := \033[38;5;240m
C_ICE    := \033[38;5;123m
C_PNK    := \033[38;5;198m
C_GRN    := \033[38;5;119m
C_ORG    := \033[38;5;215m
C_GOLD   := \033[38;5;220m
C_RED    := \033[38;5;196m
C_YLW    := \033[38;5;226m
C_MAG    := \033[38;5;165m
C_PASS   := \033[38;5;118m
C_FAIL   := \033[38;5;196m
C_INFO   := \033[38;5;39m

RST      := \033[0m
B        := \033[1m
DIM      := \033[2m
ITL      := \033[3m

# ─── Configuration ──────────────────────────────────────────────────────
PYTHONPATH   := .
SHELL        := /bin/bash
PYTHON       := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
UV           := $(shell command -v uv 2> /dev/null)
PYTEST       := pytest
RUFF         := ruff

# Environment Detection
IS_TERMUX    := $(shell [ -d "/data/data/com.termux" ] && echo "true" || echo "false")
IS_ANDROID   := $(shell uname -o 2>/dev/null | grep -qi "android" && echo "true" || echo "false")
IS_LINUX     := $(shell uname -s 2>/dev/null | grep -qi "linux" && echo "true" || echo "false")
IS_MACOS     := $(shell uname -s 2>/dev/null | grep -qi "darwin" && echo "true" || echo "false")
IS_WSL       := $(shell grep -qi "microsoft" /proc/version 2>/dev/null && echo "true" || echo "false")
IS_CONTAINER := $(shell [ -f /.dockerenv ] || [ -f /run/.containerenv ] && echo "true" || echo "false")
HAS_GUI      := $(shell [ -n "$$DISPLAY" ] || [ -n "$$WAYLAND_DISPLAY" ] && echo "true" || echo "false")

.PHONY: help install install-core install-full sync run health db-info test lint format clean about

# ─── Animated Status ─────────────────────────────────────────────────────
define animate_status
	@sp='◐◓◑◒'; \
	delay=0.04; \
	msg="$(1)"; \
	for i in $$(seq 1 12); do \
		idx=$$((i % 4)); \
		char=$${sp:$$idx:1}; \
		printf "\r  $(C_CYN)$(B)$$char$(RST)  $(C_SLV)%s$(RST)  $(DIM)⋯$(RST)" "$$msg"; \
		sleep $$delay; \
	done; \
	printf "\r\033[K"
endef

# ─── Help Menu ──────────────────────────────────────────────────────────
help:
	@clear
	@printf "\n"
	@printf "  $(C_PUR)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "  $(C_CYN)$(B)  FJ™ CYBERTRONIC SYSTEMS  $(C_DIM)✦$(RST)  $(C_PUR)OSINT NEXUS$(RST)\n"
	@printf "  $(C_SLV)$(ITL)  Cybernetic Intelligence Framework$(RST)  $(C_DIM)v4.1.1$(RST)\n"
	@printf "  $(C_PUR)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "\n"
	@printf "  $(C_ICE)$(B)⚡ SETUP ENGINE$(RST)\n"
	@printf "    $(C_ICE)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Auto-detect and build environment$(RST)\n" "make install"
	@printf "    $(C_ICE)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Lightweight engine (Mobile/Termux)$(RST)\n" "make install-core"
	@printf "    $(C_ICE)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Complete workstation suite (GUI + Browsers)$(RST)\n" "make install-full"
	@printf "    $(C_ICE)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Synchronize virtual environment dependencies$(RST)\n" "make sync"
	@printf "\n"
	@printf "  $(C_PNK)$(B)🎯 EXECUTION CORE$(RST)\n"
	@printf "    $(C_PNK)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Initiate targeted identity scan$(RST)\n" "make run"
	@printf "\n"
	@printf "  $(C_GRN)$(B)📊 TELEMETRY & DATA$(RST)\n"
	@printf "    $(C_GRN)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Network & subsystem health diagnostics$(RST)\n" "make health"
	@printf "    $(C_GRN)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Inspect SQLite matrix database$(RST)\n" "make db-info"
	@printf "\n"
	@printf "  $(C_ORG)$(B)🛠️  DEVELOPMENT TOOLING$(RST)\n"
	@printf "    $(C_ORG)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Run test suite with coverage report$(RST)\n" "make test"
	@printf "    $(C_ORG)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Static analysis & code qualification$(RST)\n" "make lint"
	@printf "    $(C_ORG)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Auto-format codebase with Ruff$(RST)\n" "make format"
	@printf "    $(C_ORG)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Purge workspace caches & build artifacts$(RST)\n" "make clean"
	@printf "    $(C_ORG)%-18s$(RST)  $(C_DIM)→$(RST)  $(C_SLV)Display application information$(RST)\n" "make about"
	@printf "\n"
	@printf "  $(C_DIM)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "  $(C_DIM)  $(ITL)Type 'make <command>' to execute$(RST)\n"
	@printf "\n"

# ─── About ──────────────────────────────────────────────────────────────
about:
	@printf "\n"
	@printf "  $(C_PUR)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "  $(C_CYN)$(B)  ✦ OSINT NEXUS ✦$(RST)  $(C_DIM)—$(RST)  $(C_SLV)$(ITL)Identity Intelligence Platform$(RST)\n"
	@printf "  $(C_PUR)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "  $(C_ORG)  Author$(RST)  $(C_DIM):$(RST)  $(C_SLV)FJ-cyberzilla$(RST)\n"
	@printf "  $(C_ORG)  Repo$(RST)    $(C_DIM):$(RST)  $(C_SLV)github.com/FJ-cyberzilla/osint-nexus$(RST)\n"
	@printf "  $(C_PUR)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "\n"

# ─── Install Targets ────────────────────────────────────────────────────
install:
	@$(call animate_status,Analyzing System Architecture)
	@sleep 0.2
	@printf "\n  $(C_BLU)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "  $(C_CYN)$(B)  ✦ SYSTEM ANALYSIS$(RST)\n"
	@printf "  $(C_BLU)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "\n"
	@[ "$(IS_TERMUX)" = "true" ] && printf "  $(C_ICE)◈$(RST)  $(C_SLV)Termux environment detected$(RST)\n" || true
	@[ "$(IS_ANDROID)" = "true" ] && [ "$(IS_TERMUX)" = "false" ] && printf "  $(C_ICE)◈$(RST)  $(C_SLV)Android OS detected$(RST)\n" || true
	@[ "$(IS_LINUX)" = "true" ] && printf "  $(C_GRN)◈$(RST)  $(C_SLV)Linux kernel detected$(RST)\n" || true
	@[ "$(IS_MACOS)" = "true" ] && printf "  $(C_PNK)◈$(RST)  $(C_SLV)macOS Darwin detected$(RST)\n" || true
	@[ "$(IS_WSL)" = "true" ] && printf "  $(C_PUR)◈$(RST)  $(C_SLV)WSL detected$(RST)\n" || true
	@[ "$(IS_CONTAINER)" = "true" ] && printf "  $(C_GOLD)◈$(RST)  $(C_SLV)Containerized environment$(RST)\n" || true
	@[ "$(HAS_GUI)" = "true" ] && printf "  $(C_PASS)◈$(RST)  $(C_SLV)GUI available$(RST)\n" || printf "  $(C_DIM)◈$(RST)  $(C_SLV)Headless terminal$(RST)\n"
	@printf "\n"
	@if [ "$(IS_TERMUX)" = "true" ] || [ "$(IS_ANDROID)" = "true" ]; then \
		printf "  $(C_ICE)$(B)▶$(RST)  Deploying $(C_ICE)Core Module$(RST) $(C_DIM)(Mobile-Optimized)$(RST)\n"; \
		sleep 0.3; \
		$(MAKE) --no-print-directory install-core; \
	elif [ "$(HAS_GUI)" = "false" ] || [ "$(IS_CONTAINER)" = "true" ]; then \
		printf "  $(C_ICE)$(B)▶$(RST)  Deploying $(C_ICE)Core Module$(RST) $(C_DIM)(Headless/Server)$(RST)\n"; \
		sleep 0.3; \
		$(MAKE) --no-print-directory install-core; \
	else \
		printf "  $(C_PNK)$(B)▶$(RST)  Deploying $(C_PNK)Full Workstation Suite$(RST)\n"; \
		sleep 0.3; \
		$(MAKE) --no-print-directory install-full; \
	fi

install-core:
	@$(call animate_status,Installing Core Package)
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e . > /dev/null 2>&1 || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)INSTALL-CORE$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)UV package manager installation failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1); \
	else \
		pip install -e . > /dev/null 2>&1 || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)INSTALL-CORE$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Standard pip installation failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1); \
	fi
	@printf "  $(C_PASS)$(B)✓$(RST)  Core engine initialized successfully\n\n"

install-full:
	@$(call animate_status,Installing Full Suite)
	@if [ -n "$(UV)" ]; then \
		$(UV) pip install -e ".[full]" > /dev/null 2>&1 || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)INSTALL-FULL$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)UV full feature installation failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1); \
	else \
		pip install -e ".[full]" > /dev/null 2>&1 || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)INSTALL-FULL$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Standard pip full installation failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1); \
	fi
	@printf "  $(C_PASS)$(B)✓$(RST)  Full workstation suite operational\n\n"

sync:
	@$(call animate_status,Synchronizing Dependencies)
	@if [ "$(IS_TERMUX)" = "true" ] || [ "$(IS_ANDROID)" = "true" ]; then \
		pip install -e . || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)SYNC$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Pip installation in mobile environment failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1); \
	elif [ -n "$(UV)" ]; then \
		$(UV) sync || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)SYNC$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)UV virtualenv sync failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1); \
	else \
		pip install -e . || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)SYNC$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Pip installation fallback failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1); \
	fi
	@printf "  $(C_PASS)$(B)✓$(RST)  Virtual environment synchronized\n\n"

# ─── Run Target ─────────────────────────────────────────────────────────
run:
	@printf "\n"
	@printf "  $(C_PUR)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "  $(C_CYN)$(B)  FJ™ CYBERTRONIC SYSTEMS  $(C_DIM)✦$(RST)  $(C_PUR)OSINT NEXUS$(RST)\n"
	@printf "  $(C_SLV)$(ITL)  Cybernetic Intelligence Framework$(RST)  $(C_DIM)v4.1.1$(RST)\n"
	@printf "  $(C_PUR)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"
	@printf "\n"
	@uname="$(USERNAME)"; \
	if [ -z "$$uname" ]; then \
		printf "  $(C_PNK)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"; \
		printf "  $(C_PNK)$(B)  ✦ TARGET SELECTION$(RST)\n"; \
		printf "  $(C_PNK)$(B)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RST)\n"; \
		printf "  $(C_SLV)  Enter target username$(RST)  $(C_DIM)(type 'q' to abort)$(RST): "; \
		while [ -z "$$uname" ]; do \
			read uname; \
			if [ "$$uname" = "cancel" ] || [ "$$uname" = "q" ]; then \
				printf "\n  $(C_GOLD)$(B)⚠$(RST)  $(C_YLW)Operation aborted by operator$(RST)\n\n"; \
				exit 0; \
			elif [ -z "$$uname" ]; then \
				printf "  $(C_RED)$(B)✗$(RST)  $(C_FAIL)Username required$(RST): "; \
			fi; \
		done; \
	fi; \
	printf "\n  $(C_PNK)$(B)▶$(RST)  $(C_SLV)Scanning target$(RST)  $(C_CYN)$(B)%s$(RST)\n\n" "$$uname"; \
	export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m osint_nexus.cli.main scan --username $$uname || \
		(printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)RUN$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Target scan module encountered an unhandled error$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1)

# ─── Health & Database ─────────────────────────────────────────────────
health:
	@$(call animate_status,Running Diagnostics)
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m osint_nexus.cli.main health || \
		(printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)HEALTH$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)System health telemetry failure detected$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1)

db-info:
	@$(call animate_status,Querying Database)
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m osint_nexus.cli.main db-info || \
		(printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)DB-INFO$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Unable to inspect SQLite database$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1)

# ─── Development ────────────────────────────────────────────────────────
test:
	@$(call animate_status,Executing Tests)
	@mkdir -p logs
	@export PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m pytest --cov=osint_nexus --cov-report=xml:logs/coverage.xml tests/ || \
		(printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)TEST$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Pytest execution failed or coverage threshold not met$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check logs or verify system status$(RST)\n\n"; exit 1)
	@printf "  $(C_PASS)$(B)✓$(RST)  All unit tests passed successfully\n\n"

lint:
	@$(call animate_status,Analyzing Code Quality)
	@$(RUFF) check . || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)LINT$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Ruff detected code quality errors$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Run 'make format' or fix issues manually$(RST)\n\n"; exit 1)
	@printf "  $(C_PASS)$(B)✓$(RST)  Code quality verification passed\n\n"

format:
	@$(call animate_status,Formatting Codebase)
	@$(RUFF) format . || (printf "\n  $(C_RED)$(B)✗$(RST)  $(C_RED)CRITICAL$(RST)  $(C_DIM)—$(RST)  $(C_CYN)FORMAT$(RST)\n  $(C_YLW)⚠$(RST)  $(C_SLV)Ruff formatter failed$(RST)\n  $(C_MAG)✦$(RST)  $(C_SLV)Check if Ruff is installed correctly$(RST)\n\n"; exit 1)
	@printf "  $(C_PASS)$(B)✓$(RST)  Codebase successfully formatted\n\n"

clean:
	@$(call animate_status,Purging Workspace)
	@rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov *.egg-info *.egg build dist .venv
	@rm -f data/*.db 2>/dev/null || true
	@rm -rf logs/* log/* 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@if [ -n "$(UV)" ]; then $(UV) cache clean >/dev/null 2>&1 || true; fi
	@printf "  $(C_PASS)$(B)✓$(RST)  Workspace purged successfully\n\n"
