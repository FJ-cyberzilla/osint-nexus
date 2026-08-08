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

## 5. Fingerbank Device Profiling
OSINT Nexus integrates with Fingerbank to provide advanced device profiling during reconnaissance.

### How it works
During the scanning process, the system automatically collects available network patterns (DHCP, User-Agents, MAC address) and interrogates the Fingerbank API to infer device metadata, such as:
- Hardware Manufacturer and Model
- Operating System details
- Confidence score (0-100)
- Known CVE vulnerabilities

These results are automatically displayed in the UI dashboard within the "Device Profile" panel upon completion of the scan.

### Configuration
Ensure your Fingerbank API key is set in the environment variables (e.g., `FINGERBANK_API_KEY`) for full access to CVE vulnerability reports.

## 6. Secure Configuration
OSINT Nexus manages sensitive credentials, such as API keys, securely:

- **Credential Storage**: Sensitive keys are stored in a local `.env` file, which is automatically added to `.gitignore` to prevent accidental commitment to version control.
- **Secure Input**: When required, the CLI will display an interactive modal to input API keys securely. The input is masked during entry.
- **Fallback Modes**: If a required API key is missing (e.g., for Fingerbank device profiling), the application will automatically enter a fallback mode, disabling the feature while allowing other scanning activities to continue gracefully.

## 7. Development & Maintenance
The following commands are available for maintainers and contributors:
...

*   **Testing**: Run the full suite with `make test`.
*   **Code Quality**: Run linting with `make lint`.
*   **Code Formatting**: Run formatter with `make format`.
*   **Cleanup**: To remove caches, build artifacts, and logs:
    ```bash
    make clean
    ```

## 7. Testing and Optimization

To ensure system reliability, the test suite is designed for parallel execution with isolated database handling.

### 7.1 Running Tests
We use `pytest-xdist` to parallelize test execution across CPU cores, which is essential for performance.

```bash
# Run tests using all available CPU cores
uv run pytest -n auto
```

### 7.2 Code Coverage
We use `pytest-cov` to monitor code coverage.

```bash
# Run tests and generate coverage reports
uv run pytest -n auto --cov=osint_nexus --cov-report=xml
```

### 7.3 Continuous Integration (CI)
Our CI pipeline (GitHub Actions) automatically runs these tests on every pull request. The workflow is configured to handle:
- Parallel test execution.
- Isolated database management via Docker containers.
- Code coverage reporting to Codecov.

## 8. Troubleshooting Test Infrastructure

If tests are failing or acting inconsistently:
1.  **Docker Status**: Ensure Docker is running, as it is required for containerized database isolation (`docker info`).
2.  **Concurrency Issues**: If tests fail intermittently in parallel mode, verify that your local environment has sufficient resources (vCPUs/RAM).
3.  **Database Locking**: If database errors occur, run `make clean` to remove any stale artifacts or database lock files (`postgres_container.lock`) in the temporary directory.
4.  **Worker Isolation**: In parallel mode (`-n auto`), each worker process (`gw0`, `gw1`, etc.) creates its own temporary database. Ensure these processes have the necessary permissions to create databases on the PostgreSQL instance.

---
*For further assistance, report issues on the project's issue tracker.*
