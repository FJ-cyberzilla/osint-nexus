# OSINT Nexus

_A high-performance reconnaissance engine by_ **[FJ-cyberzilla]
(https://github.com/FJ-cyberzilla)**

**Version: 4.1.1**

[![Dependency Graph](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/update-graph/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/update-graph)[![CodeQL Advanced](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/codeql.yml/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/codeql.yml)[![Dependabot Updates](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/dependabot-updates)
[![pages-build-deployment](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/pages/pages-build-deployment)

> **[FJ™ Cybertronic Systems](https://github.com/FJ-cyberzilla)**


## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [License](#license)

## Overview

OSINT Nexus is a modular, facade-based system designed to automate username reconnaissance across diverse web platforms. It focuses on reliability, stealth (evasion), and data integrity, with advanced capabilities for browser pooling, captcha handling, telemetry collection, and data export.

## Key Features

*   **Modular Architecture**: Decoupled orchestration and subsystem design.
*   **Intelligent Recon**: Advanced passive fingerprinting (HTTP/TLS/TCP/DNS/NTP) for device inference, platform fingerprinting, and timing-entropy based detection.
*   **Resilient Design**: Health tracking, automatic circuit breaking, self-healing, and adaptive request handling (evasion agent).
*   **Browser & Captcha Management**: Built-in browser pooling, recycling, and multi-provider captcha solving, featuring a cross-platform engine (PyQt6/Playwright) with automatic environment detection.
*   **Telemetry & Data Integrity**: Comprehensive telemetry collection (DNS, hardware) and data export support (e.g., STIX).
*   **Persistence**: Async-ready SQLite database with support for caching and FTS5 full-text search.
*   **Fingerbank Integration**: Full API integration for advanced device profiling, including hardware, OS, and vulnerability (CVE) detection, exposed via a unified facade. Supports DHCP fingerprinting.
*   **Secure Credential Management**: Automatic `.env` management to keep API keys secure and untracked by Git, with an interactive TUI modal for secure configuration.
*   **Resilient Fallback Mode**: Fingerbank profiling gracefully degrades if API keys are missing.
*   **Aesthetic & Informative UI**: Rich CLI TUI featuring real-time intelligence dashboards (Telemetry, Relationships, Activity Heatmaps, Device Profiling) and comprehensive reporting.
*   **Android/Termux Optimized**: Configured for high-performance mobile execution.

## Architecture

See the detailed [Component Structure](docs/structure.mmd).

## Installation

OSINT Nexus requires Python 3.13+. It is highly recommended to use `uv` for environment management.

```bash
make install
```

## Usage

All operational commands are managed via `make`.

### Operational Commands

| Command | Description |
| :--- | :--- |
| `make run` | Initiate a scan for a target username. |
| `make health` | Check health status of all scanning providers. |
| `make db-info` | Inspect the local scan results database. |

### Development & Maintenance

| Command | Description |
| :--- | :--- |
| `make test` | Execute the comprehensive test suite with coverage. |
| `make lint` | Verify code quality using `ruff`. |
| `make format` | Automatically format the codebase. |
| `make clean` | Purge all build artifacts, caches, and logs. |

## Development

- **Tech Stack**: Python 3.13, FastAPI, Pydantic, SQLite (aiosqlite), Rich, Playwright.
- **Standards**: Strict typing (`mypy`), linting (`ruff`), and comprehensive unit testing (`pytest`).
- **Parallel Testing & Coverage**: The test suite is optimized for parallel execution using `pytest-xdist` (`pytest -n auto`) and includes automated code coverage analysis (`pytest-cov`).
- **CI/CD**: Fully automated testing, coverage reporting, and security scanning on every push/PR via GitHub Actions.

---
*Developed by FJ™ Cybertronic Systems.*
