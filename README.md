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
