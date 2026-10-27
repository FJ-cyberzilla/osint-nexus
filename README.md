# OSINT-Nexus & Omni-Masquerade OS

* A high-performance reconnaissance engine & intelligence database generator

> **[FJ™ Cybertronic Systems](https://github.com/FJ-cyberzilla)**

[![Go CI](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/ci.yml/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/ci.yml)

## Overview

**OSINT-Nexus** and **Omni-Masquerade OS** are high-accuracy, low-level OSINT and network reconnaissance engines built natively in Go (`go1.23+`) by **FJ™ Cybertronic Systems**. 

The system handles deep packet inspection, raw socket manipulation, custom TLS fingerprinting (JA3/JA4), DNS record traversal, multi-source pivot extraction, and real-time intelligence database generation from minimal username seed clues.

## Omni-Masquerade: The Central Nerve & Algorithmic Engine

**Omni-Masquerade** serves as the central nerve and main algorithmic engine driving the entire application. It coordinates and orchestrates all sub-systems into a unified reconnaissance network:
- **`temp`**: Ephemeral session scratchpads, cache files, and temporary browser profile directories (`internal/engine/omni_masquerade/temp.go`).
- **`score`**: Weighted confidence scoring, false positive filtering, and metadata credibility evaluation (`internal/engine/omni_masquerade/score.go`).
- **`resolve`**: Handle canonicalization, username normalization, and pivot deduplication (`internal/engine/omni_masquerade/resolve.go`).
- **`vault`**: Thread-safe in-memory rotation vault for platform cookies and authentication tokens without dropping active sessions (`internal/engine/omni_masquerade/vault.go`).
- **`helper`**: Execution logging, progress reporting, and config validation (`internal/engine/omni_masquerade/helper.go`).
- **Central Nerve Status Panel**: Real-time visualization of Omni-Masquerade operational states, workers, and active reconnaissance tasks.
- **Dork Intelligence & Search Queries**: Automatic generation and execution of targeted search engine dorks for deep intelligence discovery.
- **Operation Finished Statistics & Final Findings**: Comprehensive summation of discovered intelligence, verified platform profiles, and final stats upon completion.
- **Network Strategy Alignment**: Dynamic TCP Window, TTL, and MSS adjustment alongside JA4 TLS extension shuffling.
- **Self-Awareness & Honeypot Detection**: Active heuristic payload analysis to detect canary tokens and honeypots, letting Omni-Masquerade terminate connections cleanly.
- **Legal & Compliance Enforcement**: Automated `robots.txt` parsing and risk scoring (`internal/detector/robots.go`).
- **STIX 2.1 Threat Intel Export**: Full conversion of identity profiles, IOCs, and relationship objects into STIX 2.1 bundles (`internal/exporter/stix.go`).

## Unified TUI Command Center & Modular Architecture

The TUI Command Center is launched via `make run` and provides a polished Bubble Tea interface featuring:
- **Modular UI Components (`internal/ui/`)**: Refactored into specialized modules (`panels.go`, `display.go`, `sys_status.go`) for maintainability.
- **App Status Telemetry vs. Target Intel**: Clear separation between local runtime socket telemetry/active sessions and target reconnaissance intelligence.
- **Robust Provider Lookups**: Accurate platform lookups across Instagram, Telegram, Threads, Rubika, and more with proper header validation and redirect handling (`internal/provider/base.go`).

## Primary Entry Point & Commands

- **`make help`**: Display all available Makefile commands, targets, and framework options.
- **`make install`**: Initialize environment, download dependencies, and build the binary via Makefile.
- **`make run`**: Launch the OSINT reconnaissance TUI Command Center as the unified entry point.
- **`make test`**: Run the comprehensive unit test suite.

## Architecture

- `cmd/nexus-cli/`: CLI application entrypoint.
- `internal/ui/`: Modular TUI dashboard components (`dashboard.go`, `dashboard_renderer.go`, `panels.go`, `display.go`, `sys_status.go`).
- `internal/engine/omni_masquerade/`: Omni-Masquerade OS central engine (`temp`, `score`, `resolve`, `vault`, `helper`).
- `internal/engine/browser_pool/`: Managed browser instance pool with Cloudflare evasion & low-network rules.
- `internal/detector/`: Low-level protocol probes (DNS, TLS, HTTP2, Robots Parser, Credential Leak).
- `internal/exporter/`: STIX 2.1 threat intelligence export engine.
- `internal/extractor/`: Modular parsing pipeline (Email, Social, Meta, PGP).

---
*Developed by FJ™ Cybertronic Systems.*
