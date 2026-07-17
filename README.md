# OSINT Nexus

An adaptive, high-performance OSINT agent for verifying username presence across platforms with advanced evasion, validation, and device inference capabilities.

## Version: 2.0.1

## Architecture Overview

OSINT Nexus has been refactored to a modular facade-based architecture, decoupling the main orchestration logic into distinct, testable subsystems.

### Core Components
- `OSINTAgent` (Facade): The primary entry point, orchestrating the scan lifecycle via injected subsystems.
- `ScanOrchestrator`: Manages concurrent provider scanning, health tracking, and persistence.
- `HealthTracker`: Implements platform health monitoring with failure decay.
- `ReportGenerator`: Handles telemetry collection and scan summary generation.
- `DeviceInferenceService`: Provides intelligent device context (MAC OUI, port heuristics).
- `DatabaseManager`: Ensures thread-safe/async-safe persistence of scan results.

## Key Improvements
- **Concurrency Fixes**: Resolved database persistence race conditions in `run_scan`.
- **Modular Design**: Extracted logic into independent subsystems, significantly improving maintainability and testability.
- **Dependency Injection**: Subsystems are explicitly injected, simplifying isolated component testing.
- **Enhanced Capability**: Added `DeviceInferenceService` for production-grade device context.
- **Termux Optimizations**: Automated TLS profile selection (restricting to `chrome120`) to ensure stability in Android/Termux environments.
- **Aesthetic Reporting**: Integrated `rich` for color-coded CLI tables and panel-based final intelligence summaries.
- **Platform Compatibility**: Expanded support for short-name platforms (e.g., 'X') and Iranian platforms (Eitaa, Soroush+, etc.).

## Usage
The agent is designed to be used in asynchronous contexts:
```python
agent = OSINTAgent(username="target_user")
async for intel in agent.run_scan("target_user"):
    # intel is an IntelligenceObject
    print(f"Found on {intel.platform}: {intel.found}")
report = agent.get_final_report()
```

## Testing
Comprehensive test suite available in `tests/`. Run using:
```bash
PYTHONPATH=. pytest tests/
```
