# OSINT Nexus - Go Edition

_A high-performance reconnaissance engine by_ **[FJ-cyberzilla](https://github.com/FJ-cyberzilla)**

> **[FJ™ Cybertronic Systems](https://github.com/FJ-cyberzilla)**

## Overview

OSINT Nexus is a high-accuracy, low-level OSINT and network reconnaissance engine built natively in Go (`go1.23+`). It handles deep packet inspection, raw socket manipulation, custom TLS fingerprinting (JA3/JA4), DNS record traversal, and multi-source pivot extraction.

The system is designed for maximum performance, deterministic data integrity, and strict type safety.

## Architecture

The project follows a strict Go directory structure:

- `cmd/nexus-cli/`: CLI application entrypoint.
- `pkg/osint/`: Publicly exportable client APIs.
- `internal/`: Core components:
    - `engine/`: Provider orchestrator (high-concurrency, lock-free aggregation).
    - `detector/`: Low-level protocol probes (DNS, TLS, HTTP2).
    - `extractor/`: Modular, streaming-based parsing pipeline (Email, Social, Meta, PGP).
    - `captcha/`: Solver clients & TLS fingerprinting.
    - `types/`: Core domain structs and interfaces.
    - `telemetry/`: Socket metrics & network telemetry.

## Build & Installation

OSINT-Nexus uses a unified `Makefile` for all build, test, and environment management tasks.

```bash
# Initialize environment and build the binary
make install

# Build binary
make build

# Run all unit tests
make test

# Run performance benchmarks
make bench
```

> **Note:** Strictly prohibits the installation of any additional tools during the build or development lifecycle. See [docs/BUILD_RESTRICTIONS.md](docs/BUILD_RESTRICTIONS.md).

## Usage

The primary interface for the engine is the `bin/nexus-cli` tool.

```bash
# Display help
./bin/nexus-cli --help

# Run a DNS probe
./bin/nexus-cli probe dns google.com
```

See `docs/CLI_COMMANDS.md` for full command documentation.

## Development

- **Tech Stack**: Go 1.23+, `charmbracelet/lipgloss` (UI), `rotisserie/eris` (Structured Error Handling), `uber-go/mock` (Testing).
- **Performance**: High-concurrency operations utilize lock-free result aggregation in `internal/engine`. The `internal/extractor` utilizes a streaming tokenizer for memory-efficient parsing.

### Error Handling Pattern
All operations that can fail must return `error` and wrap them using `eris` to maintain a traceable stack:
```go
if err != nil {
    return eris.Wrap(err, "contextual description")
}
```

## Command Center TUI

OSINT-Nexus features an industrial-grade, real-time command center dashboard.

See `docs/TUI_COMMAND_CENTER.md` for full implementation details.

---
*Developed by FJ™ Cybertronic Systems.*
