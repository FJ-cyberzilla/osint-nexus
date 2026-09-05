# OSINT-Nexus Industrial Makefile

APP_NAME=OSINT-Nexus
VERSION=1.0.0
CLI_TOOL=./cmd/nexus-cli/main.go

# Colors for Makefile output
GREEN=\033[0;32m
RED=\033[0;31m
YELLOW=\033[0;33m
PURPLE=\033[0;35m
CYAN=\033[0;36m
NC=\033[0m # No Color

.PHONY: all build lint test complexity run diagnosis about version help clean

all: build lint test ## Run build, lint, and test

build: ## Build the engine
	@echo -e "${PURPLE}[${APP_NAME}]${NC} Building engine..."
	@go build -ldflags "-X main.Version=$(VERSION)" -o bin/nexus ./cmd/nexus/
	@echo -e "${GREEN}✓ Build Successful${NC}"

lint: ## Run linters
	@echo -e "${PURPLE}[${APP_NAME}]${NC} Running linters..."
	@golangci-lint run ./... || echo -e "${RED}✗ Linting Failed${NC}"

test: ## Run tests
	@echo -e "${PURPLE}[${APP_NAME}]${NC} Running tests..."
	@go test -v ./... || echo -e "${RED}✗ Tests Failed${NC}"

complexity: ## Analyze complexity
	@echo -e "${PURPLE}[${APP_NAME}]${NC} Analyzing complexity..."
	@gocyclo -over 15 . || echo -e "${YELLOW}! High complexity detected${NC}"

run: ## Execute the engine
	@echo -e "${PURPLE}[${APP_NAME}]${NC} Executing..."
	@go run ./cmd/nexus/main.go

diagnosis: ## Run system diagnostics
	@echo -e "${PURPLE}[${APP_NAME}]${NC} Running system diagnostics..."
	@go run $(CLI_TOOL) status

about: ## About the engine
	@go run $(CLI_TOOL) about

version: ## Show version
	@echo "$(VERSION)"

clean: ## Remove build artifacts, logs, and caches
	@echo -e "${PURPLE}[${APP_NAME}]${NC} Cleaning project artifacts..."
	@rm -rf bin/
	@rm -rf logs/*
	@go clean -cache -modcache -testcache
	@find . -name "*.tmp" -type f -delete
	@echo -e "${GREEN}✓ Cleanup Complete${NC}"

help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${CYAN}%-20s${NC} %s\n", $$1, $$2}'
