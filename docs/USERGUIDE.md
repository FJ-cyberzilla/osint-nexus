# OSINT-Nexus & Omni-Masquerade OS User Guide
_Maintained by_ **[FJ-cyberzilla](https://github.com/FJ-cyberzilla)**  
> _Powered by_ **FJ™ Cybertronic Systems**
**Version: 1.0.0**

Welcome to the OSINT-Nexus & Omni-Masquerade OS user guide. This document provides detailed instructions on installing, configuring, and effectively using the industrial reconnaissance and intelligence database generation engine.

## 1. Introduction
OSINT-Nexus and Omni-Masquerade OS are high-accuracy, low-level OSINT and network reconnaissance engines built natively in Go (`go1.23+`). The system handles deep packet inspection, raw socket manipulation, custom TLS fingerprinting (JA3/JA4), DNS record traversal, multi-source pivot extraction, and real-time intelligence database generation from minimal username seed clues.

## 2. Prerequisites
- **Go**: Go `1.23+` installed on your system.
- **Build Tools**: `make`, standard C compiler (if required by network/socket bindings).
- **OS**: Optimized for Linux, macOS, and Android (Termux).

## 3. Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/FJ-cyberzilla/osint-nexus.git
   cd osint-nexus
   ```

2. **Build the Binary**:
   ```bash
   make build
   ```
   This compiles the `nexus-cli` binary into `./bin/nexus-cli`.

## 4. Omni-Masquerade OS & Control Modules
Omni-Masquerade OS transforms a small username clue into a comprehensive real-world OSINT database using four modular control sub-components:
- **`temp` (`internal/engine/omni_masquerade/temp.go`)**: Manages ephemeral session scratchpads, cache files, and temporary browser profile directories.
- **`score` (`internal/engine/omni_masquerade/score.go`)**: Computes weighted confidence scores, false positive filtering, and metadata credibility evaluation.
- **`resolve` (`internal/engine/omni_masquerade/resolve.go`)**: Canonicalizes handles, standardizes username formatting, and deduplicates pivot lists.
- **`helper` (`internal/engine/omni_masquerade/helper.go`)**: Manages execution logging, progress reporting, and configuration validation.

## 5. Advanced Evasion & Transport Layers
- **Behavioral Emulation (`behavior.go`)**: Stochastically distributed request jitter and human-like typing/cursor delays to defeat bot detection heuristics.
- **Canvas & WebGL Entropy Injection (`entropy.go`)**: Imperceptible micro-noise injection into HTMLCanvasElement rendering data and WebGL contexts to defeat device fingerprint tracking.
- **HTTP/3 & QUIC Masquerade (`http3.go`)**: QUIC/UDP transport routing and secure request dispatching under TLS 1.3.
- **TCP Socket Tuning (`tcp.go`)**: Raw socket options for per-profile IP TTL, window size, and keep-alive configuration.

## 6. Operational Workflow & Testing
- **TUI Command Center**: Launch via `./bin/nexus-cli` or `make run`.
- **Testing**: Run all unit tests across the codebase via `make test`.

---
*Developed by FJ™ Cybertronic Systems.*
