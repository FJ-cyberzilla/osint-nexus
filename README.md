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
    - extractor/: Modular, streaming-based parsing pipeline (Email, Social, Meta, PGP).
    - `captcha/`: Solver clients & TLS fingerprinting.
    - `types/`: Core domain structs and interfaces.
    - `telemetry/`: Socket metrics & network telemetry.

## Build Restrictions

To ensure security and stability, **OSINT-Nexus strictly prohibits the installation of any additional tools** during the build or development lifecycle that are not already explicitly required. Please refer to [docs/BUILD_RESTRICTIONS.md](docs/BUILD_RESTRICTIONS.md) for the full policy.


## Usage

```bash
# Run the CLI
./cmd/nexus/nexus --help
```

## Development

- **Tech Stack**: Go 1.23+, `charmbracelet/lipgloss` (UI), `rotisserie/eris` (Structured Error Handling), `uber-go/mock` (Testing).
- **Standards**: Strictly typed, zero-panic, explicit error propagation, `context.Context` for all network calls.
- **Error Handling**: Use `github.com/rotisserie/eris` for all errors to ensure actionable, traceable context.
- **Testing**: Run all tests: `go test ./...`

### Error Handling Pattern
All operations that can fail must return `error` and wrap them using `eris` to maintain a traceable stack:
```go
if err != nil {
    return eris.Wrap(err, "contextual description")
}
```
Never ignore errors or use `fmt.Errorf` without `eris` wrapping.

### Initialization Pattern
Components requiring configuration should follow the explicit error-handling pattern:
```go
cfg, err := config.Get()
if err != nil {
    return nil, eris.Wrap(err, "failed to initialize")
}
```
`config.Get()` returns `(*Config, error)`. Never ignore the error.

## Command Center TUI

OSINT-Nexus features an industrial-grade, real-time command center dashboard. It provides comprehensive visibility into reconnaissance scans, including:
- **System Metrics Panels**: Device type, TLS Fingerprint (API or System Default), telemetry, heatmap, and Fingerbank API status/usage data.
- **Fingerbank Findings**: Advanced device identification, confidence scoring, and vulnerability alerting.
- **Intelligence Mapping**: Relations and shadow user visualization.
- **Real-Time Feedback**: Progress tracking with integrated spinner animations and live action reporting.
- **Categorized Alerting**: Granular **Yellow** system alerts for failures (API/Network/Fallback) and Light Blue advisory notifications.

See `docs/TUI_COMMAND_CENTER.md` for full implementation details.

## Fingerbank Integration
OSINT-Nexus leverages Fingerbank v2 for advanced device profiling. This integration supports multimodal payloads (JA3, client hints, TCP signatures) with automatic fallback to local detection if the API is disabled or unreliable (low confidence).

- **Documentation**: `docs/FINGERBANK_API.md`
- **Security**: API keys are securely managed via environment variables (`OSINT_FINGERBANK_API_KEY`).

---
*Developed by FJ™ Cybertronic Systems.*
