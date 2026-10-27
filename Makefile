# ==============================================================================
# OSINT-Nexus | Industrial Automation Framework
# Author: FJ-cyberzilla
# Version: 1.0.0
# ==============================================================================

APP_NAME    := OSINT-Nexus
VERSION     := 1.0.0
AUTHOR      := FJ-cyberzilla
CLI_TOOL    := ./cmd/nexus-cli/
BUILD_DIR   := bin
LOG_DIR     := logs
BINARY      := $(BUILD_DIR)/nexus-cli

# ------------------------------------------------------------------------------
# Shell & Global Settings
# ------------------------------------------------------------------------------
SHELL           := /bin/bash
.SHELLFLAGS     := -eu -o pipefail -c
.DEFAULT_GOAL   := all
MAKEFLAGS       += --no-print-directory

GIT_COMMIT      := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_TIME      := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
GO_FILES        := $(shell find . -name "*.go" -not -path "./vendor/*" 2>/dev/null | wc -l | tr -d ' ')

# ------------------------------------------------------------------------------
# Environment Detection
# ------------------------------------------------------------------------------
UNAME_S := $(shell uname -s 2>/dev/null || echo "unknown")
UNAME_A := $(shell uname -a 2>/dev/null || echo "unknown")

ifneq ($(findstring Darwin,$(UNAME_S)),)
  $(error OSINT-Nexus does not support macOS or iOS. Use Linux, WSL2, or Termux.)
endif

ifneq ($(wildcard /data/data/com.termux),)
  ENV_TYPE := TERMUX
else ifneq ($(findstring microsoft,$(UNAME_A)),)
  ENV_TYPE := WSL2
else ifeq ($(OS),Windows_NT)
  ENV_TYPE := POWERSHELL
else
  ENV_TYPE := LINUX
endif

# ------------------------------------------------------------------------------
# ANSI Aesthetic Palette
# ------------------------------------------------------------------------------
ESC          := $(shell printf '\033')
RESET        := $(ESC)[0m
BOLD         := $(ESC)[1m
DIM          := $(ESC)[2m

# Banner gradient stops (Pagga wordmark, 6 rows, 6 colors L→R)
B1           := $(ESC)[38;2;168;85;247m   # purple
B2           := $(ESC)[38;2;139;92;246m   # violet
B3           := $(ESC)[38;2;99;102;241m   # indigo
B4           := $(ESC)[38;2;59;130;246m   # blue
B5           := $(ESC)[38;2;56;189;248m   # sky
B6           := $(ESC)[38;2;125;211;252m  # light

# Status palette
C_PURPLE     := $(ESC)[38;2;168;85;247m
C_CYAN       := $(ESC)[38;2;56;189;248m
C_GREEN      := $(ESC)[38;2;74;222;128m
C_RED        := $(ESC)[38;2;248;113;113m
C_YELLOW     := $(ESC)[38;2;250;204;21m
C_GRAY       := $(ESC)[38;2;100;116;139m
C_WHITE      := $(ESC)[38;2;226;232;240m

# Vintage accents
V_GREEN      := $(ESC)[38;2;130;180;130m
V_YELLOW     := $(ESC)[38;2;210;180;100m
V_ORANGE     := $(ESC)[38;2;230;140;70m

# Environment colors
C_TERMUX     := $(ESC)[38;2;255;165;0m
C_WSL2       := $(ESC)[38;2;0;200;120m
C_LINUX      := $(ESC)[38;2;100;150;255m
C_POWERSHELL := $(ESC)[38;2;255;220;0m

ifeq ($(ENV_TYPE),TERMUX)
  ENV_COLOR := $(C_TERMUX)
else ifeq ($(ENV_TYPE),WSL2)
  ENV_COLOR := $(C_WSL2)
else ifeq ($(ENV_TYPE),LINUX)
  ENV_COLOR := $(C_LINUX)
else
  ENV_COLOR := $(C_POWERSHELL)
endif

# Symbols
CHECK        := $(C_GREEN)✔$(RESET)
CROSS        := $(C_RED)✘$(RESET)
WARN_SYM     := $(C_YELLOW)⚡$(RESET)
GEAR         := $(C_PURPLE)⚙$(RESET)
BRANCH       := $(C_GRAY)├─$(RESET)
END_BRANCH   := $(C_GRAY)└─$(RESET)

# ------------------------------------------------------------------------------
# Helper Macros
# ------------------------------------------------------------------------------
define TIMER_START
START_TIME=$$(date +%s%N);
endef

define TIMER_END
ELAPSED=$$(( ($$(date +%s%N) - $$START_TIME) / 1000000 )); \
printf "  $(C_GRAY)└─ $(DIM)Completed in $${ELAPSED}ms$(RESET)\n\n"
endef

# ------------------------------------------------------------------------------
# Phony Targets
# ------------------------------------------------------------------------------
.PHONY: all banner build install lint test coverage bench complexity run \
        diagnosis about version clean clean-all help fmt vet check stats

# ==============================================================================
# Default
# ==============================================================================
all: banner help

# ==============================================================================
# Banner — Pagga wordmark with 6-stop gradient
# ==============================================================================
banner:
	@printf '\n'
	@printf '%s\n' '$(B1)░█▀█░█▀▀░▀█▀░█▀█░▀█▀░░░░░█▀█░█▀▀░█░█░█░█░█▀▀░░$(RESET)'
	@printf '%s\n' '$(B2)░█░█░▀▀█░░█░░█░█░░█░░▄▄▄░█░█░█▀▀░▄▀▄░█░█░▀▀█░░$(RESET)'
	@printf '%s\n' '$(B3)░▀▀▀░▀▀▀░▀▀▀░▀░▀░░▀░░░░░░▀░▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░░$(RESET)'
	@printf '\n'
	@printf '%s\n' '  $(C_WHITE)$(BOLD)Industrial Automation Framework$(RESET)  $(C_GRAY)·$(RESET)  $(V_YELLOW)FJ Cybertronic Systems$(RESET)'
	@printf '%s\n' '  $(C_GRAY)env$(RESET) $(ENV_COLOR)$(BOLD)$(ENV_TYPE)$(RESET)  $(C_GRAY)·$(RESET)  $(C_GRAY)commit$(RESET) $(C_CYAN)$(GIT_COMMIT)$(RESET)  $(C_GRAY)·$(RESET)  $(C_GRAY)v$(VERSION)$(RESET)'
	@printf '\n'

# ==============================================================================
# Install
# ==============================================================================
install: build ## Prepare environment and build the application
	@printf "$(GEAR) $(C_PURPLE)$(BOLD)[INSTALL]$(RESET) Initializing environment...\n"
	@mkdir -p $(LOG_DIR)
	@printf "  $(BRANCH) $(C_WHITE)Creating log directory $(C_CYAN)$(LOG_DIR)/$(RESET)\n"
	@printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Environment Ready$(RESET)]\n\n"

# ==============================================================================
# Build
# ==============================================================================
build: banner ## Build engine binary with embedded build metadata
	@$(TIMER_START) \
	printf "$(GEAR) $(C_PURPLE)$(BOLD)[BUILD]$(RESET) Compiling core engine target...\n"; \
	printf "  $(BRANCH) $(C_WHITE)Processing $(C_CYAN)$(GO_FILES)$(RESET) source files\n"; \
	mkdir -p $(BUILD_DIR); \
	if go build \
		-ldflags "-s -w -X main.Version=$(VERSION) -X main.Author=$(AUTHOR) -X main.Commit=$(GIT_COMMIT) -X main.BuildTime=$(BUILD_TIME)" \
		-o $(BINARY) $(CLI_TOOL); then \
		rm -f main nexus 2>/dev/null || true; \
		SIZE=$$(du -h $(BINARY) | cut -f1); \
		printf "  $(BRANCH) $(C_WHITE)Target binary: $(C_CYAN)$(BINARY)$(RESET) $(C_GRAY)($${SIZE})$(RESET)\n"; \
		printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Build Succeeded$(RESET)]\n"; \
	else \
		printf "  $(END_BRANCH) Status: [$(CROSS) $(C_RED)Build Failed$(RESET)]\n"; \
		exit 1; \
	fi; \
	$(TIMER_END)

# ==============================================================================
# Lint
# ==============================================================================
lint: banner ## Run static code analysis and quality checks
	@$(TIMER_START) \
	printf "$(GEAR) $(C_PURPLE)$(BOLD)[LINT]$(RESET) Executing static analysis suite...\n"; \
	if [ "$(ENV_TYPE)" = "TERMUX" ]; then \
		printf "  $(END_BRANCH) $(WARN_SYM) $(C_YELLOW)Skipped on Termux$(RESET)\n"; \
	elif ! command -v golangci-lint >/dev/null 2>&1; then \
		printf "  $(END_BRANCH) Status: [$(CROSS) $(C_RED)golangci-lint not installed$(RESET)]\n"; \
		exit 1; \
	else \
		printf "  $(BRANCH) $(C_WHITE)Scanning $(C_CYAN)$(GO_FILES)$(RESET) source files\n"; \
		if golangci-lint run ./...; then \
			printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Lint Clean$(RESET)]\n"; \
		else \
			printf "  $(END_BRANCH) Status: [$(CROSS) $(C_RED)Lint Issues Detected$(RESET)]\n"; \
			exit 1; \
		fi; \
	fi; \
	$(TIMER_END)

# ==============================================================================
# Tests — animated spinner + streaming results
# ==============================================================================
test: banner ## Run unit test suite with coverage reporting
	@START_TIME=$$(date +%s%N); \
	printf "$(GEAR) $(C_PURPLE)$(BOLD)[TEST]$(RESET) Running package tests...\n"; \
	TEST_COUNT=$$(go test -list '.*' ./... 2>/dev/null | grep -c '^Test' || echo 0); \
	printf "  $(BRANCH) $(C_WHITE)Executing $(C_CYAN)$${TEST_COUNT}$(RESET) unit tests\n\n"; \
	LOG=$$(mktemp); \
	( \
		sp='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'; \
		i=0; \
		while kill -0 $$$$ 2>/dev/null; do \
			c=$${sp:$$((i % 10)):1}; \
			printf "\r  $(C_PURPLE)%s$(RESET)  $(C_GRAY)Testing$(RESET)  $(C_CYAN)%d$(RESET) $(C_GRAY)packages...$(RESET)" "$$c" "$$i"; \
			i=$$((i+1)); \
			sleep 0.08; \
			[ $$i -ge 500 ] && break; \
		done; \
	) & \
	SPIN_PID=$$!; \
	set +e; \
	go test -v -timeout 60s -cover -coverprofile=coverage.out ./... > "$$LOG" 2>&1; \
	TEST_EXIT=$$?; \
	set -e; \
	kill $$SPIN_PID 2>/dev/null || true; \
	wait $$SPIN_PID 2>/dev/null || true; \
	printf "\r%-70s\r" ""; \
	sed \
		-e 's/^=== RUN/$(C_GRAY)=== RUN$(RESET)/' \
		-e 's/--- PASS/$(C_GREEN)--- PASS$(RESET)/' \
		-e 's/--- FAIL/$(C_RED)--- FAIL$(RESET)/' \
		-e 's/^PASS/$(C_GREEN)PASS$(RESET)/' \
		-e 's/^FAIL/$(C_RED)FAIL$(RESET)/' \
		-e 's/^ok  /$(C_GREEN)ok  $(RESET)/' \
		"$$LOG"; \
	rm -f "$$LOG"; \
	printf "\n"; \
	if [ $$TEST_EXIT -eq 0 ]; then \
		printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)All Tests Passed$(RESET)]\n"; \
	else \
		printf "  $(END_BRANCH) Status: [$(CROSS) $(C_RED)Test Failures Encountered$(RESET)]\n"; \
		exit 1; \
	fi; \
	$(TIMER_END)

# ==============================================================================
# Coverage
# ==============================================================================
coverage: test ## Generate HTML coverage report
	@printf "\n$(GEAR) $(C_PURPLE)$(BOLD)[COVERAGE]$(RESET) Generating coverage report...\n"
	@go tool cover -html=coverage.out -o coverage.html
	@printf "  $(END_BRANCH) Report: $(C_CYAN)coverage.html$(RESET)\n\n"

# ==============================================================================
# Benchmarks
# ==============================================================================
bench: banner ## Run performance benchmarks
	@$(TIMER_START) \
	printf "$(GEAR) $(C_PURPLE)$(BOLD)[BENCH]$(RESET) Running performance benchmarks...\n\n"; \
	if go test -bench=. -benchmem -run=^$$ ./...; then \
		printf "\n  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Benchmarks Complete$(RESET)]\n"; \
	else \
		printf "\n  $(END_BRANCH) Status: [$(CROSS) $(C_RED)Benchmark Failures$(RESET)]\n"; \
		exit 1; \
	fi; \
	$(TIMER_END)

# ==============================================================================
# Complexity
# ==============================================================================
complexity: banner ## Analyze cyclomatic complexity using gocyclo
	@$(TIMER_START) \
	printf "$(GEAR) $(C_PURPLE)$(BOLD)[METRICS]$(RESET) Calculating cyclomatic complexity...\n"; \
	if [ "$(ENV_TYPE)" = "TERMUX" ]; then \
		printf "  $(END_BRANCH) $(WARN_SYM) $(C_YELLOW)Skipped on Termux$(RESET)\n"; \
	elif ! command -v gocyclo >/dev/null 2>&1; then \
		printf "  $(END_BRANCH) $(CROSS) $(C_RED)gocyclo not installed$(RESET)\n"; \
		exit 1; \
	else \
		printf "  $(BRANCH) $(C_WHITE)Threshold: $(C_YELLOW)> 15$(RESET)\n"; \
		if gocyclo -over 15 .; then \
			printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Complexity Acceptable$(RESET)]\n"; \
		else \
			printf "  $(END_BRANCH) Status: [$(WARN_SYM) $(C_YELLOW)High Complexity Functions Found$(RESET)]\n"; \
		fi; \
	fi; \
	$(TIMER_END)

# ==============================================================================
# Format & Vet
# ==============================================================================
fmt: banner ## Format all Go source files
	@printf "$(GEAR) $(C_PURPLE)$(BOLD)[FMT]$(RESET) Formatting source files...\n"
	@go fmt ./...
	@printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Formatted$(RESET)]\n\n"

vet: banner ## Run go vet static analysis
	@printf "$(GEAR) $(C_PURPLE)$(BOLD)[VET]$(RESET) Running go vet...\n"
	@if go vet ./...; then \
		printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Vet Clean$(RESET)]\n\n"; \
	else \
		printf "  $(END_BRANCH) Status: [$(CROSS) $(C_RED)Vet Issues$(RESET)]\n\n"; \
		exit 1; \
	fi

check: fmt vet lint test ## Run all quality gates

# ==============================================================================
# Run
# ==============================================================================
run: ## Run engine (Usage: make run)
	@printf "$(GEAR) $(C_PURPLE)$(BOLD)[EXEC]$(RESET) Spawning application instance...\n"
	@if [ ! -f "$(BINARY)" ]; then \
		printf "  $(WARN_SYM) $(C_YELLOW)Binary missing — building first$(RESET)\n"; \
		$(MAKE) build; \
	fi
	@args="$(ARGS)"; \
	printf "  $(BRANCH) $(C_WHITE)Arguments: $(C_CYAN)$$args$(RESET)\n"; \
	printf "  $(END_BRANCH) $(C_GRAY)──────────────────────────────$(RESET)\n\n"; \
	$(BINARY) $$args

# ==============================================================================
# About / Version / Stats
# ==============================================================================
about: banner ## Display module metadata
	@if [ ! -f "$(BINARY)" ]; then $(MAKE) build; fi
	@$(BINARY)

version: ## Display clean semver string
	@printf "$(C_CYAN)$(VERSION)$(RESET)\n"

stats: ## Show project statistics
	@printf "$(GEAR) $(C_PURPLE)$(BOLD)[STATS]$(RESET) Project statistics\n"
	@printf "  $(BRANCH) Go files:  $(C_CYAN)$(GO_FILES)$(RESET)\n"
	@printf "  $(BRANCH) LOC:       $(C_CYAN)$$(find . -name '*.go' -not -path './vendor/*' -exec cat {} + | wc -l)$(RESET)\n"
	@printf "  $(BRANCH) Packages:  $(C_CYAN)$$(go list ./... 2>/dev/null | wc -l)$(RESET)\n"
	@printf "  $(END_BRANCH) Commit:  $(C_CYAN)$(GIT_COMMIT)$(RESET)\n\n"

# ==============================================================================
# Clean
# ==============================================================================
clean: banner ## Purge build artifacts, logs, temp files
	@$(TIMER_START) \
	printf "$(GEAR) $(C_PURPLE)$(BOLD)[CLEAN]$(RESET) Purging generated artifacts...\n"; \
	if [ -d "$(BUILD_DIR)" ]; then rm -rf $(BUILD_DIR); printf "  $(BRANCH) Removed $(C_CYAN)$(BUILD_DIR)/$(RESET)\n"; fi; \
	if [ -d "$(LOG_DIR)" ]; then rm -rf $(LOG_DIR)/*; printf "  $(BRANCH) Flushed $(C_CYAN)$(LOG_DIR)/$(RESET)\n"; fi; \
	rm -f data/nexus.db data/nexus.db-shm data/nexus.db-wal coverage.out coverage.html; \
	printf "  $(BRANCH) Removed database & coverage artifacts\n"; \
	TMP_COUNT=$$(find . -name "*.tmp" -type f 2>/dev/null | wc -l | tr -d ' '); \
	find . -name "*.tmp" -type f -delete 2>/dev/null || true; \
	printf "  $(BRANCH) Deleted $(C_CYAN)$${TMP_COUNT}$(RESET) temp files\n"; \
	printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Workspace Cleaned$(RESET)]\n"; \
	$(TIMER_END)

clean-all: clean ## Purge artifacts AND Go caches
	@printf "$(GEAR) $(C_PURPLE)$(BOLD)[CLEAN-ALL]$(RESET) Purging Go caches...\n"
	@go clean -cache -modcache -testcache
	@printf "  $(END_BRANCH) Status: [$(CHECK) $(C_GREEN)Caches Purged$(RESET)]\n\n"

# ==============================================================================
# Help — clean single-accent layout
# ==============================================================================
help: ## Display this help interface
	@printf '\n'
	@printf '  $(C_GRAY)Available command targets$(RESET)\n\n'
	@awk 'BEGIN {FS = ":.*?## "} \
		/^[a-zA-Z_-]+:.*?## .*$$/ { \
			printf "  $(C_CYAN)%-16s$(RESET) $(C_GRAY)%s$(RESET)\n", $$1, $$2 \
		}' $(MAKEFILE_LIST)
	@printf '\n'
	@printf '  $(C_GRAY)Usage$(RESET)  $(C_WHITE)make$(RESET) $(C_CYAN)<target>$(RESET)\n'
	@printf '         $(C_WHITE)make$(RESET) $(C_CYAN)run$(RESET) $(C_GRAY)ARGS="-d --verbose"$(RESET)\n\n'
