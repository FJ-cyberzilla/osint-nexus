# OSINT Nexus - Go Edition

_A high-performance reconnaissance engine by_ **[FJ-cyberzilla](https://github.com/FJ-cyberzilla)**

> **[FJ™ Cybertronic Systems](https://github.com/FJ-cyberzilla)**

## Overview

OSINT Nexus is a high-accuracy, low-level OSINT and network reconnaissance engine built natively in Go (`go1.23+`). It handles deep packet inspection, raw socket manipulation, custom TLS fingerprinting (JA3/JA4), DNS record traversal, and multi-source pivot extraction.

The system is designed for maximum performance, deterministic data integrity, and strict type safety.

## Architecture

The project follows a strict Go directory structure:

- `cmd/nexus/`: CLI application entrypoint.
- `pkg/osint/`: Publicly exportable client APIs.
- `internal/`: Core components:
    - `engine/`: Provider orchestrator & worker pools.
    - `detector/`: Low-level protocol probes (DNS, TLS, HTTP2).
    - `extractor/`: Regex & HTML parsing pipeline.
    - `captcha/`: Solver clients & TLS fingerprinting.
    - `types/`: Core domain structs and interfaces.
    - `telemetry/`: Socket metrics & network telemetry.

## Installation & Setup

OSINT Nexus requires Go 1.23+.

```bash
# Clone the repository
git clone https://github.com/FJ-cyberzilla/osint-nexus.git
cd osint-nexus

# Build the project
go build ./...
```

## Usage

```bash
# Run the CLI
./cmd/nexus/nexus --help
```

## Development

- **Tech Stack**: Go 1.23+, `charmbracelet/lipgloss` (UI), `rotisserie/eris` (Errors), `uber-go/mock` (Testing).
- **Standards**: Strictly typed, zero-panic, explicit error propagation, `context.Context` for all network calls.
- **Testing**: Run all tests: `go test ./...`

---
*Developed by FJ™ Cybertronic Systems.*
