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
# Build Restriction Policy
# ------------------------------------------------------------------------------
# Strictly prohibited: Ad-hoc installation of tools/dependencies via Makefile.
# All tasks must use only the pre-defined targets. See docs/BUILD_RESTRICTIONS.md.

# ------------------------------------------------------------------------------
# Environment Detection
# ------------------------------------------------------------------------------
# Detect Apple platforms first to block them
ifneq ($(shell uname | grep -i darwin),)
  $(error "OSINT-Nexus does not support macOS or iOS. Please use Linux, WSL2, or a native terminal environment.")
endif

# Detect other environments
ifneq ($(wildcard /data/data/com.termux),)
  ENV_TYPE := TERMUX
else ifneq ($(shell uname -a | grep -i microsoft),)
  ENV_TYPE := WSL2
else ifneq ($(OS),Windows_NT)
  ENV_TYPE := LINUX
else
  ENV_TYPE := POWERSHELL
endif

# ------------------------------------------------------------------------------
# Aesthetic Styling & Truecolor (24-bit RGB Gradients)
# ------------------------------------------------------------------------------
BOLD        := \033[1m
RESET       := \033[0m

# Truecolor RGB Gradient for Banner
G1          := \033[38;2;147;51;234m
G2          := \033[38;2;126;34;206m
G3          := \033[38;2;50;50;200m
G4          := \033[38;2;50;150;250m
G5          := \033[38;2;100;200;250m
G6          := \033[38;2;150;220;250m

# Status Palette
C_PURPLE    := \033[38;2;168;85;247m
C_CYAN      := \033[38;2;56;189;248m
C_GREEN     := \033[38;2;74;222;128m
C_RED       := \033[38;2;248;113;113m
C_YELLOW    := \033[38;2;250;204;21m
C_GRAY      := \033[38;2;100;116;139m
VINTAGE_GREEN := \033[38;2;130;180;130m
VINTAGE_YELLOW := \033[38;2;210;180;100m
VINTAGE_GRADIENT_ORANGE := \033[38;2;230;140;70m

# Environment Specific Colors
C_TERMUX := \033[38;2;255;165;0m
C_WSL2   := \033[38;2;0;100;0m
C_LINUX  := \033[38;2;0;0;255m
C_POWERSHELL := \033[38;2;255;255;0m

ifeq ($(ENV_TYPE),TERMUX)
  ENV_COLOR := $(C_TERMUX)
else ifeq ($(ENV_TYPE),WSL2)
  ENV_COLOR := $(C_WSL2)
else ifeq ($(ENV_TYPE),LINUX)
  ENV_COLOR := $(C_LINUX)
else
  ENV_COLOR := $(C_POWERSHELL)
endif

# Status Symbols
CHECK       := $(C_GREEN)✔$(RESET)
CROSS       := $(C_RED)✘$(RESET)
WARN        := $(C_YELLOW)⚡$(RESET)
GEAR        := $(C_PURPLE)⚙$(RESET)

# Helper Macro for Timed Execution
TIMER_START = START_TIME=$$(date +%s%N)
TIMER_END   = ELAPSED=$$(( ($$(date +%s%N) - $$START_TIME) / 1000000 )); \
              printf "  $(C_GRAY)└─ Completed in $${ELAPSED}ms$(RESET)\n\n"

.PHONY: all banner build lint test bench complexity run diagnosis about version clean help

# Default Target
all: banner build test ## Execute primary build and validation suite

banner:
	@printf "$(G1)$(BOLD)██████╗ ███████╗██╗███╗   ██╗████████╗   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗$(RESET)\n"
	@printf "$(G2)$(BOLD)██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝$(RESET)\n"
	@printf "$(G3)$(BOLD)██║   ██║███████╗██║██╔██╗ ██║   ██║█████╗██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗$(RESET)\n"
	@printf "$(G4)$(BOLD)██║   ██║╚════██║██║██║╚██╗██║   ██║╚════╝██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║$(RESET)\n"
	@printf "$(G5)$(BOLD)╚██████╔╝███████║██║██║ ╚████║   ██║      ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║$(RESET)\n"
	@printf "$(G6)$(BOLD) ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝      ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝$(RESET)\n"
	@printf "$(VINTAGE_GREEN)$(BOLD)  :: $(APP_NAME) Framework :: v$(VERSION) :: Author: $(AUTHOR) ::          │$(RESET)\n"
	@printf "$(ENV_COLOR)$(BOLD)  :: Environment: $(ENV_TYPE) ::$(RESET)\n\n"

build: banner ## Build engine binaries with embedded build metadata
	@START_TIME=$$(date +%s%N); \
	printf "$(C_PURPLE)$(GEAR) [BUILD]$(RESET) Compiling core engine target...\n"; \
	mkdir -p $(BUILD_DIR); \
	GO_FILES=$$(find . -name "*.go" | wc -l | tr -d ' '); \
	printf "  $(C_GRAY)├─ Processing $${GO_FILES} source files...$(RESET)\n"; \
	if go build -ldflags "-X main.Version=$(VERSION) -X main.Author=$(AUTHOR)" -o $(BUILD_DIR)/nexus ./cmd/nexus/; then \
		printf "  $(C_GRAY)├─ Target binary:$(RESET) $(C_CYAN)$(BUILD_DIR)/nexus$(RESET)\n  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Build Succeeded$(RESET)]\n"; \
	else \
		printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Build Failed$(RESET)]\n"; exit 1; \
	fi; \
	ELAPSED=$$(( ($$(date +%s%N) - $$START_TIME) / 1000000 )); \
	printf "  $(C_GRAY)└─ Completed in $${ELAPSED}ms$(RESET)\n\n"

lint: banner ## Run static code analysis and quality checks
	@$(TIMER_START); \
	printf "$(C_PURPLE)$(GEAR) [LINT]$(RESET) Executing static analysis suite...\n"; \
	if [ "$(ENV_TYPE)" != "TERMUX" ]; then \
		LINT_FILES=$$(find . -name "*.go" -not -path "./vendor/*" | wc -l | tr -d ' '); \
		printf "  $(C_GRAY)├─ Scanning $${LINT_FILES} source files...$(RESET)\n"; \
		if golangci-lint run ./...; then \
			printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Lint Clean$(RESET)]\n"; \
		else \
			printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Lint Issues Detected$(RESET)]\n"; \
		fi; \
	else \
		printf "  $(C_YELLOW)$(WARN) Termux environment detected. Skipping golangci-lint to prevent crash.$(RESET)\n"; \
	fi; \
	$(TIMER_END)

test: banner ## Run unit test suite with coverage reporting
	@$(TIMER_START); \
	printf "$(C_PURPLE)$(GEAR) [TEST]$(RESET) Running package tests...\n"; \
	TEST_COUNT=$$(go test -list . ./... 2>/dev/null | grep -E '^Test' | wc -l | tr -d ' '); \
	printf "  $(C_GRAY)├─ Executing $${TEST_COUNT} unit tests...$(RESET)\n"; \
	if go test -v -timeout 30s ./...; then \
		printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)All Tests Passed$(RESET)]\n"; \
	else \
		printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Test Failures Encountered$(RESET)]\n"; \
	fi; \
	$(TIMER_END)

bench: banner ## Run performance benchmarks
	@$(TIMER_START); \
	printf "$(C_PURPLE)$(GEAR) [BENCH]$(RESET) Running performance benchmarks...\n"; \
	if go test -bench=. -benchmem ./...; then \
		printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Benchmarks Passed$(RESET)]\n"; \
	else \
		printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Benchmark Failures Encountered$(RESET)]\n"; \
	fi; \
	$(TIMER_END)


complexity: banner ## Analyze code complexity metrics using gocyclo
	@$(TIMER_START); \
	printf "$(C_PURPLE)$(GEAR) [METRICS]$(RESET) Calculating cyclomatic complexity...\n"; \
	if [ "$(ENV_TYPE)" != "TERMUX" ]; then \
		printf "  $(C_GRAY)├─ Threshold Limit:$(RESET) $(C_YELLOW)> 15$(RESET)\n"; \
		if gocyclo -over 15 .; then \
			printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Complexity Low$(RESET)]\n"; \
		else \
			printf "  $(C_GRAY)└─ Status:$(RESET) [$(WARN) $(C_YELLOW)High Complexity Functions Found$(RESET)]\n"; \
		fi; \
	else \
		printf "  $(C_YELLOW)$(WARN) Termux environment detected. Skipping gocyclo to prevent crash.$(RESET)\n"; \
	fi; \
	$(TIMER_END)

run: ## Run engine dynamically (Usage: make run <args>)
	@printf "$(C_PURPLE)$(GEAR) [EXEC]$(RESET) Spawning application instance...\n"
	@printf "  $(C_GRAY)├─ Arguments:$(RESET) $(C_CYAN)$(filter-out $@,$(MAKECMDGOALS))$(RESET)\n"
	@go run ./cmd/nexus/ $(filter-out $@,$(MAKECMDGOALS))

%:
	@:

diagnosis: banner ## Execute runtime diagnostics and environment checks
	@$(TIMER_START); \
	printf "$(C_PURPLE)$(GEAR) [DIAGNOSIS]$(RESET) Querying system state via CLI tool...\n"; \
	if go run $(CLI_TOOL) status; then \
		printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)Diagnostics Completed$(RESET)]\n"; \
	else \
		printf "  $(C_GRAY)└─ Status:$(RESET) [$(CROSS) $(C_RED)Diagnostics Error$(RESET)]\n"; \
	fi; \
	$(TIMER_END)

about: banner ## Display module metadata and framework details
	@go run $(CLI_TOOL) about

version: ## Display clean semver string
	@printf "$(VERSION)\n"

clean: banner ## Purge binary artifacts, logs, build output, and module caches
	@START_TIME=$$(date +%s%N); \
	printf "$(C_PURPLE)$(GEAR) [CLEAN]$(RESET) Purging generated artifacts...\n"; \
	if [ -d "$(BUILD_DIR)" ]; then rm -rf $(BUILD_DIR); printf "  $(C_GRAY)├─ Removed target directory:$(RESET) $(C_CYAN)$(BUILD_DIR)/$(RESET)\n"; fi; \
	if [ -d "$(LOG_DIR)" ]; then rm -rf $(LOG_DIR)/*; printf "  $(C_GRAY)├─ Flushed log directory:$(RESET) $(C_CYAN)$(LOG_DIR)/$(RESET)\n"; fi; \
	rm -f data/nexus.db data/nexus.db-shm data/nexus.db-wal; \
	printf "  $(C_GRAY)├─ Flushed database artifacts from data/$(RESET)\n"; \
	TMP_COUNT=$$(find . -name "*.tmp" -type f | wc -l | tr -d ' '); \
	find . -name "*.tmp" -type f -delete; \
	printf "  $(C_GRAY)├─ Deleted $${TMP_COUNT} temporary files$(RESET)\n"; \
	go clean -cache -modcache -testcache; \
	printf "  $(C_GRAY)├─ Purged Go build and module caches$(RESET)\n"; \
	ELAPSED=$$(( ($$(date +%s%N) - $$START_TIME) / 1000000 )); \
	printf "  $(C_GRAY)└─ Status:$(RESET) [$(CHECK) $(C_GREEN)System Cleaned ($${ELAPSED}ms)$(RESET)]\n"

help: banner ## Display this interactive help interface
	@printf "$(C_CYAN)$(BOLD)Available Command Targets:$(RESET)\n\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; { \
			desc = $$2; \
			gsub("Execute primary build and validation suite", "Run all", desc); \
			gsub("Build engine binaries with embedded build metadata", "Build engine", desc); \
			gsub("Run static code analysis and quality checks", "Run lint", desc); \
			gsub("Run unit test suite with coverage reporting", "Run tests", desc); \
			gsub("Run performance benchmarks", "Run benchmarks", desc); \
			gsub("Analyze code complexity metrics using gocyclo", "Check complexity", desc); \
			gsub("Run engine dynamically \\(Usage: make run <args>\\)", "Run engine", desc); \
			gsub("Execute runtime diagnostics and environment checks", "Run diagnostics", desc); \
			gsub("Display module metadata and framework details", "Show info", desc); \
			gsub("Display clean semver string", "Show version", desc); \
			gsub("Purge binary artifacts, logs, build output, and module caches", "Clean project", desc); \
			gsub("Display this interactive help interface", "Show help", desc); \
			printf "  $(VINTAGE_YELLOW)%-16s$(RESET) $(C_GRAY)│$(RESET) $(VINTAGE_GRADIENT_ORANGE)%s$(RESET)\n", $$1, desc \
		}'
	@printf "\n"
