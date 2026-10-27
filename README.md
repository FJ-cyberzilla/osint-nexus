# OSINT-Nexus & Omni-Masquerade OS

* A high-performance reconnaissance engine & intelligence database generator

> **[FJ™ Cybertronic Systems](https://github.com/FJ-cyberzilla)**

[![Go CI](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/ci.yml/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/ci.yml)

## Overview

**OSINT-Nexus** and **Omni-Masquerade OS** are high-accuracy, low-level OSINT and network reconnaissance engines built natively in Go (`go1.23+`) by **FJ™ Cybertronic Systems**. 

The system handles deep packet inspection, raw socket manipulation, custom TLS fingerprinting (JA3/JA4), DNS record traversal, multi-source pivot extraction, and real-time intelligence database generation from minimal username seed clues.

## Omni-Masquerade Algorithm & Controllers

Omni-Masquerade OS uses a modular control architecture designed for maximum feasibility and control:
- **`temp`**: Ephemeral session scratchpads, cache files, and temporary browser profile directories (`internal/engine/omni_masquerade/temp.go`).
- **`score`**: Weighted confidence scoring, false positive filtering, and metadata credibility evaluation (`internal/engine/omni_masquerade/score.go`).
- **`resolve`**: Handle canonicalization, username normalization, and pivot deduplication (`internal/engine/omni_masquerade/resolve.go`).
- **`helper`**: Execution logging, progress reporting, and config validation (`internal/engine/omni_masquerade/helper.go`).

## Primary Entry Point & Commands

- **`make help`**: Display all available Makefile commands, targets, and framework options.
- **`make install`**: Initialize environment, download dependencies, and build the binary.
- **`make run`**: Launch the OSINT reconnaissance TUI Command Center.

## Architecture

- `cmd/nexus-cli/`: CLI application entrypoint.
- `internal/engine/omni_masquerade/`: Omni-Masquerade OS intelligence database generation engine (`temp`, `score`, `resolve`, `helper`).
- `internal/engine/browser_pool/`: Managed browser instance pool with Cloudflare evasion & low-network rules.
- `internal/detector/`: Low-level protocol probes (DNS, TLS, HTTP2, Credential Leak).
- `internal/extractor/`: Modular parsing pipeline (Email, Social, Meta, PGP).

---
*Developed by FJ™ Cybertronic Systems.*
