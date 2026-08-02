# OSINT Nexus

[![CodeQL Advanced](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/codeql.yml/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/codeql.yml)[![Dependabot Updates](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/dependabot-updates)[![Dependency Graph](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/update-graph/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/dependabot/update-graph)[![pages-build-deployment](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/FJ-cyberzilla/osint-nexus/actions/workflows/pages/pages-build-deployment)

An adaptive, high-performance OSINT agent for verifying username presence across platforms with advanced evasion, validation, and device inference capabilities.

## Version: 2.1.0

## Architecture Overview

OSINT Nexus has been refactored to a modular, facade-based architecture, decoupling the main orchestration logic into distinct, testable subsystems.

### Core Components

*   **`OSINTAgent` (Facade)**: The primary entry point, orchestrating the scan lifecycle via injected subsystems.
*   **`ScanOrchestrator`**: Manages concurrent provider scanning, health tracking, and persistence.
*   **`HealthTracker`**: Implements platform health monitoring with failure decay, circuit breaking, and auto-healing.
*   **`ReportGenerator`**: Handles telemetry collection and scan summary generation.
*   **`DeviceInferenceService`**: Provides intelligent device context (MAC OUI, port heuristics).
*   **`DatabaseManager`**: Ensures thread-safe/async-safe persistence of scan results.

## Key Improvements

*   **Health Monitoring & Circuit Breaking**: Robust failure tracking with configurable thresholds and auto-healing.
*   **Debugging**: Added developer-friendly `DEBUG_PROVIDERS` flag for graceful error handling.
*   **CLI Enhancements**: Added a dedicated `health` command for monitoring provider status.
*   **Concurrency**: Resolved database persistence race conditions in `run_scan`.
*   **Modular Design**: Logic extracted into independent, testable subsystems.
*   **Enhanced Capability**: Added `DeviceInferenceService` for production-grade device context.
*   **Termux Optimizations**: Automated TLS profile selection (`chrome120`) for Android/Termux stability.
*   **Aesthetic Reporting**: Integrated `rich` for color-coded CLI tables and final summaries.

## Usage

### Programmatic API

```python
from osint_nexus.core.agent import OSINTAgent

agent = OSINTAgent(username="target_user")
async for intel in agent.run_scan("target_user"):
    print(f"Found on {intel.platform}: {intel.found}")
report = agent.get_final_report()
```

### CLI Operations

**Scan a target username:**
```bash
python -m osint_nexus.cli scan --username target_user
```

**Check provider health:**
```bash
python -m osint_nexus.cli health
```

## Testing

Comprehensive test suite available in `tests/`.

```bash
PYTHONPATH=. pytest tests/
```
