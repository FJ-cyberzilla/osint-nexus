# ==============================================================================
# OSINT-Nexus | Industrial Automation Framework
# Author: FJ-cyberzilla
# ==============================================================================

APP_NAME    := OSINT-Nexus
VERSION     := 1.0.0
AUTHOR      := FJ-cyberzilla
CLI_TOOL    := ./cmd/nexus-cli/main.go
BUILD_DIR   := bin
LOG_DIR     := logs

# ------------------------------------------------------------------------------
# Aesthetic Styling & Truecolor (24-bit RGB Gradients)
# ------------------------------------------------------------------------------
BOLD        := \033[1m
RESET       := \033[0m

# Truecolor RGB Gradient for Banner
G1          := \033[38;2;147;51;234m
G2          := \033[38;2;126;34;206m
G3          := \033[38;2;99;102;241m
G4          := \033[38;2;59;130;246m
G5          := \033[38;2;14;165;233m
G6          := \033[38;2;6;182;212m

# Status Palette
C_PURPLE    := \033[38;2;168;85;247m
C_CYAN      := \033[38;2;56;189;248m
C_GREEN     := \033[38;2;74;222;128m
C_RED       := \033[38;2;248;113;113m
C_YELLOW    := \033[38;2;250;204;21m
C_GRAY      := \033[38;2;100;116;139m

# Status Symbols
CHECK       := $(C_GREEN)✔$(RESET)
CROSS       := $(C_RED)✘$(RESET)
WARN        := $(C_YELLOW)⚡$(RESET)
GEAR        := $(C_PURPLE)⚙$(RESET)

# Helper Macro for Timed Execution
TIMER_START = @START_TIME=$$(date +%s%N)
TIMER_END   = @ELAPSED=$$(( ($$(date +%s%N) - $$START_TIME) / 1000000 )); \
              printf "  $(C_GRAY)└─ Completed in $${ELAPSED}ms$(RESET)\n\n"

.PHONY: all banner build lint test complexity run diagnosis about version clean help

# Default Target
all: banner build test ## Execute primary build and validation suite

banner:
	@printf "$(G1)$(BOLD)   ___  ____ ___ _  ████████╗   _  ███████╗██╗  ██╗██╗   ██╗███████╗$(RESET)\n"
	@printf "$(G2)$(BOLD)  / _ \/ __// _ \ |    ██╔══╝  / | ██╔════╝╚██╗██╔╝██║   ██║██╔════╝$(RESET)\n"
	@printf "$(G3)$(BOLD) / // /\ \ / // / |    ██║     | | █████╗   ╚███╔╝ ██║   ██║███████╗$(RESET)\n"
	@printf "$(G4)$(BOLD)/____/___//____/  |_   ██║     |_| ██╔══╝   ██╔██╗ ██║   ██║╚════██║$(RESET)\n"
	@printf "$(G5)$(BOLD)                       ██║         ███████╗██╔╝ ██╗╚██████╔╝███████║$(RESET)\n"
	@printf "$(G6)$(BOLD)                       ╚═╝         ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝$(RESET)\n"
	@printf "$(C_CYAN)$(BOLD)  :: $(APP_NAME) Framework :: v$(VERSION) :: Author: $(AUTHOR) ::$(RESET)\n\n"

build: banner ## Build engine binaries with embedded build metadata
	$(TIMER_START)
	@printf "$(C_PURPLE)$(GEAR) [BUILD]$(RESET) Compiling core engine target...\n"
	@mkdir -p $(BUILD_DIR)
	@GO_FILES=$$(find . -name "*.go" | wc -l | tr -d ' '); \
	 printf "  $(C_GRAY)├─ Processing $${GO_FILES} source files...$(RESET)\n"
	@go build -ldflags "-X main.Version=$(VERSION) -X main.Author=$(AUTHOR)" -o $(BUILD_DIR)/nexus ./cmd/nexus/ \
		&& printf "  $(C_GRAY)├─ Target binary:$(RESET) $(C_CYAN)$(BUILD_DIR)/nexus$(RESET)\n  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Build Succeeded$(RESET)]\n" \
		|| (printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Build Failed$(RESET)]\n" && exit 1)
	$(TIMER_END)

lint: banner ## Run static code analysis and quality checks
	$(TIMER_START)
	@printf "$(C_PURPLE)$(GEAR) [LINT]$(RESET) Executing static analysis suite...\n"
	@if [ -d /data/data/com.termux ]; then \
		printf "  $(C_YELLOW)$(WARN) Termux environment detected. Skipping golangci-lint.$(RESET)\n"; \
	else \
		LINT_FILES=$$(find . -name "*.go" -not -path "./vendor/*" | wc -l | tr -d ' '); \
		printf "  $(C_GRAY)├─ Scanning $${LINT_FILES} source files...$(RESET)\n"; \
		golangci-lint run ./... \
			&& printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Lint Clean$(RESET)]\n" \
			|| printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Lint Issues Detected$(RESET)]\n"; \
	fi
	$(TIMER_END)

test: banner ## Run unit test suite with coverage reporting
	$(TIMER_START)
	@printf "$(C_PURPLE)$(GEAR) [TEST]$(RESET) Running package tests...\n"
	@TEST_COUNT=$$(go test -list . ./... 2>/dev/null | grep -E '^Test' | wc -l | tr -d ' '); \
	 printf "  $(C_GRAY)├─ Executing $${TEST_COUNT} unit tests...$(RESET)\n"
	@go test -v ./... \
		&& printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)All Tests Passed$(RESET)]\n" \
		|| printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Test Failures Encountered$(RESET)]\n"
	$(TIMER_END)

complexity: banner ## Analyze code complexity metrics using gocyclo
	$(TIMER_START)
	@printf "$(C_PURPLE)$(GEAR) [METRICS]$(RESET) Calculating cyclomatic complexity...\n"
	@printf "  $(C_GRAY)├─ Threshold Limit:$(RESET) $(C_YELLOW)> 15$(RESET)\n"
	@gocyclo -over 15 . \
		&& printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Complexity Low$(RESET)]\n" \
		|| printf "  $(C_GRAY)└─ Status:$(RESET) [$(WARN) $(C_YELLOW)High Complexity Functions Found$(RESET)]\n"
	$(TIMER_END)

run: ## Run engine dynamically (Usage: make run <args>)
	@printf "$(C_PURPLE)$(GEAR) [EXEC]$(RESET) Spawning application instance...\n"
	@printf "  $(C_GRAY)├─ Arguments:$(RESET) $(C_CYAN)$(filter-out $@,$(MAKECMDGOALS))$(RESET)\n"
	@go run ./cmd/nexus/ $(filter-out $@,$(MAKECMDGOALS))

%:
	@:

diagnosis: banner ## Execute runtime diagnostics and environment checks
	$(TIMER_START)
	@printf "$(C_PURPLE)$(GEAR) [DIAGNOSIS]$(RESET) Querying system state via CLI tool...\n"
	@go run $(CLI_TOOL) status \
		&& printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Diagnostics Completed$(RESET)]\n" \
		|| printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Diagnostics Error$(RESET)]\n"
	$(TIMER_END)

about: banner ## Display module metadata and framework details
	@go run $(CLI_TOOL) about

version: ## Display clean semver string
	@printf "$(VERSION)\n"

clean: banner ## Purge binary artifacts, logs, build output, and module caches
	$(TIMER_START)
	@printf "$(C_PURPLE)$(GEAR) [CLEAN]$(RESET) Purging generated artifacts...\n"
	@if [ -d "$(BUILD_DIR)" ]; then rm -rf $(BUILD_DIR); printf "  $(C_GRAY)├─ Removed target directory:$(RESET) $(C_CYAN)$(BUILD_DIR)/$(RESET)\n"; fi; \
	 if [ -d "$(LOG_DIR)" ]; then rm -rf $(LOG_DIR)/*; printf "  $(C_GRAY)├─ Flushed log directory:$(RESET) $(C_CYAN)$(LOG_DIR)/$(RESET)\n"; fi; \
	 TMP_COUNT=$$(find . -name "*.tmp" -type f | wc -l | tr -d ' '); \
	 find . -name "*.tmp" -type f -delete; \
	 printf "  $(C_GRAY)├─ Deleted $${TMP_COUNT} temporary files$(RESET)\n"; \
	 go clean -cache -modcache -testcache; \
	 printf "  $(C_GRAY)├─ Purged Go build and module caches$(RESET)\n"; \
	 printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)System Cleaned$(RESET)]\n"
	$(TIMER_END)

help: banner ## Display this interactive help interface
	@printf "$(C_CYAN)$(BOLD)Available Command Targets:$(RESET)\n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(C_PURPLE)%-16s$(RESET) $(C_GRAY)│$(RESET) %s\n", $$1, $$2}'
	@printf "\n"
