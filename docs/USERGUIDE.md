# OSINT Nexus User Guide
_Maintained by_ **[FJ-cyberzilla](https://github.com/FJ-cyberzilla)**  
> _Powered by_ **FJ™ Cybertronic Systems**
**Version: 4.1.1**

Welcome to the OSINT Nexus user guide. This document provides detailed instructions on installing, configuring, and effectively using the OSINT Nexus reconnaissance system.


## 1. Introduction
OSINT Nexus is a professional-grade OSINT tool built for adaptive, high-performance username reconnaissance. It is designed to be modular, stealthy, and highly resilient.

## 2. Prerequisites
- **Python**: 3.13 or newer.
- **Environment Management**: `uv` (strongly recommended).
- **OS**: Optimized for Unix-based systems (specifically Android/Termux, Linux, macOS).

## 3. Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd osint-nexus
    ```

2.  **Install Dependencies**:
    The project uses a `Makefile` to simplify workflows.
    ```bash
    make install
    ```
    This command will sync the environment using `uv`, ensuring all dependencies are installed and the virtual environment is ready.

## 4. Operational Workflow

The `make` interface is the recommended way to interact with OSINT Nexus.

### Scanning a Target
To initiate a reconnaissance scan for a specific username:
```bash
make run
```
*You will be prompted to enter the username.*

### Network & Provider Health
Before running large scans, check if the providers are reachable:
```bash
make health
```

### Inspecting Results
To query the local database for previously stored results:
```bash
make db-info
```

## 5. Development & Maintenance
The following commands are available for maintainers and contributors:

*   **Testing**: Run the full suite with `make test`.
*   **Code Quality**: Run linting with `make lint`.
*   **Code Formatting**: Run formatter with `make format`.
*   **Cleanup**: To remove caches, build artifacts, and logs:
    ```bash
    make clean
    ```

## 6. Configuration
Configuration is managed primarily through environment variables and Pydantic settings. For specific provider configurations or evasion parameters, please refer to:
- `osint_nexus/core/config.py`
- `osint_nexus/core/browser/config.py`

## 7. Troubleshooting
If you encounter issues, please:
1.  **Check Provider Health**: Run `make health`.
2.  **Verify Environment**: Ensure `make sync` has been run recently.
3.  **Logs**: Inspect logs in the `logs/` directory.
4.  **Database**: If results seem stale, use `make db-info` to inspect the local cache.

---
*For further assistance, report issues on the project's issue tracker.*
