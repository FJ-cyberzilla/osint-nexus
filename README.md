# OSINT Nexus
_A high-performance reconnaissance engine by_ **[FJ-cyberzilla](https://github.com/FJ-cyberzilla)**
**Version: 3.1.7**

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

OSINT Nexus is a modular, facade-based system designed to automate username reconnaissance across diverse web platforms. It focuses on reliability, stealth (evasion), and data integrity.

## Key Features

*   **Modular Architecture**: Decoupled orchestration and subsystem design.
*   **Intelligent Recon**: Advanced device inference, platform fingerprinting, and timing-entropy based detection.
*   **Resilient Design**: Health tracking, automatic circuit breaking, and self-healing for robust scanning.
*   **Stealth & Evasion**: Browser fingerprinting, captcha solving, and adaptive request handling (e.g., `curl_cffi`).
*   **Persistence**: Async-ready SQLite database with support for caching and FTS5 full-text search.
*   **Aesthetic UI**: Color-coded, rich CLI interfaces for real-time monitoring and reporting.
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

- **Tech Stack**: Python 3.13, FastAPI, Pydantic, SQLite (aiosqlite), Rich, Playwright (optional).
- **Standards**: Strict typing (`mypy`), linting (`ruff`), and comprehensive unit testing (`pytest`).

---
*Developed by FJ™ Cybertronic Systems.*
