
### OSINT-Nexus 

* Powered by FJ™ Cyberzilla Systems®
*FJ-cyberzilla* dev and  owner of the following  Platform.

## Architectural Blueprint & System Specification

## 1. Executive Summary & Core Purpose

`osint-nexus` is an enterprise-grade, highly modular Open Source Intelligence (OSINT) gathering, browser automation, and digital fingerprinting framework designed in Python. It provides automated target reconnaissance, dynamic content extraction, anti-bot/anti-scraping evasion, network & protocol-level fingerprint detection, multi-provider API integrations, and structured intelligence exports (e.g., STIX 2.1).

### Key Architectural Pillars
1. **Multi-Head Execution Engine**: Headless browser automation engine powered by Playwright and PyQt backends with automatic dynamic engine fallback and pooling.
2. **Detection & Evasion Subsystem**: Real-time fingerprint analysis (TLS, HTTP/2, TCP, DNS, Canvas/Audio, Timing/Entropy) coupled with adaptive mimicry and active CAPTCHA solving (Anti-Captcha, 2Captcha, Chained solvers).
3. **Orchestrated Recon Pipeline**: Asynchronous worker pool system running permutation, target discovery, dorking, data extraction, and confidence scoring.
4. **Data Persistence & Health Monitoring**: Multi-tier repository pattern using SQLite engines, cache layers, schema migration handlers, and diagnostic telemetry probes.
5. **Multi-Interface Access**: Terminal UI (Rich/Textual), CLI commands, and a RESTful API layer (FastAPI).

---

## 2. High-Level Architecture Diagram

The diagram below illustrates the macro-level view of `osint-nexus`, showing user interface entry points, core orchestration modules, data acquisition engines, evasion layers, storage abstractions, and export formats.

```mermaid
flowchart TB
    subgraph UI_Layer ["User Interface Layer"]
        CLI["CLI Commands\n(osint_nexus.cli.commands)"]
        TUI["Rich Terminal UI\n(osint_nexus.cli.ui & components)"]
        API["FastAPI Server\n(osint_nexus.api.main)"]
    end

    subgraph Core_Orchestrator ["Core Orchestration & Business Logic"]
        ORCH["Orchestrator Core\n(orchestrator/core.py)"]
        WORKERS["Worker Pool\n(orchestrator/workers.py)"]
        AGG["Data Aggregator\n(aggregator.py)"]
        SCORE["Confidence Calculator\n(score_calculator.py & confidence.py)"]
        PERM["Permutator & Dorking\n(permutator.py / dork.py)"]
    end

    subgraph Data_Acquisition ["Data Acquisition & Execution Layer"]
        BROWSER_POOL["Browser Pool & Factory\n(core/browser/pool.py & factory.py)"]
        PLAYWRIGHT["Playwright Engine\n(engine_playwright.py)"]
        PYQT["PyQt Engine\n(engine_pyqt.py)"]
        PROVIDERS["Provider Registry\n(providers/registry.py)"]
        GENERIC_P["Generic Provider"]
        GH_P["GitHub Provider"]
        APARAT_P["Aparat Provider"]
    end

    subgraph Evasion_Detection ["Evasion, Intelligence & Anti-Detection"]
        EVASION["Evasion Agent & Mimicry\n(evasion.py / mimicry.py)"]
        CAPTCHA["CAPTCHA Solvers (Chained)\n(anti_captcha.py / two_captcha.py)"]
        DETECTORS["Fingerprint Detectors\n(TLS, DNS, HTTP/2, Canvas, Timing)"]
        FINGERBANK["Fingerbank Client & Service\n(fingerbank/service.py)"]
    end

    subgraph Storage_Layer ["Database & Repository Layer"]
        DB_ENGINE["SQLite Engine & Health\n(core/db/sqlite_engine.py)"]
        SCHEMA["Schema Manager\n(schema_manager.py)"]
        REPOS["Repositories\n(Search, Result, Cache, Fingerprint)"]
    end

    subgraph Export_Layer ["Exporters & Output"]
        REPORT["Report Generator\n(report.py)"]
        STIX["STIX 2.1 Exporter\n(exporters/stix.py)"]
    end

    %% User Interactions
    CLI --> ORCH
    TUI --> ORCH
    API --> ORCH

    %% Orchestrator connections
    ORCH --> WORKERS
    ORCH --> PERM
    WORKERS --> BROWSER_POOL
    WORKERS --> PROVIDERS
    WORKERS --> AGG

    %% Browser Engines
    BROWSER_POOL --> PLAYWRIGHT
    BROWSER_POOL --> PYQT

    %% Providers
    PROVIDERS --> GENERIC_P
    PROVIDERS --> GH_P
    PROVIDERS --> APARAT_P

    %% Evasion & Detection Integration
    PLAYWRIGHT --> EVASION
    PLAYWRIGHT --> CAPTCHA
    PLAYWRIGHT --> DETECTORS
    DETECTORS --> FINGERBANK

    %% Storage connections
    AGG --> SCORE
    SCORE --> REPOS
    REPOS --> DB_ENGINE
    DB_ENGINE --> SCHEMA

    %% Exporters
    AGG --> REPORT
    AGG --> STIX
```

---

## 3. Layer Breakdown & Core Modules

### 3.1 Interface Layer (`osint_nexus/cli`, `osint_nexus/api`)
- **CLI Commands (`osint_nexus/cli/commands/`)**:
  - `scan.py`: Initiates multi-threaded scan jobs against target usernames, domains, or IP addresses.
  - `health.py`: Executes system readiness checks, browser health validations, and API key authentications.
  - `db_info.py`: Inspects internal storage usage, schema migration state, and cached query metrics.
- **UI Components (`osint_nexus/cli/components/`)**:
  - Provides modular UI elements (progress bars, status panels, tabular results, credential input prompts) styled via `theme.py`.
- **API Server (`osint_nexus/api/`)**:
  - Exposes RESTful endpoints (`main.py`) using Dependency Injection (`deps.py`) to allow remote management and programmatic integration.

### 3.2 Core Orchestration Subsystem (`osint_nexus/core/`)

```mermaid
graph TD
    A[Target Input] --> B[Permutator / Dorking Engine]
    B --> C[Orchestrator Core]
    C --> D[Task Queue / Worker Pool]
    D --> E1[Provider Runner]
    D --> E2[Browser Engine Tasks]
    E1 --> F[Raw Intelligence Data]
    E2 --> F[Raw Intelligence Data]
    F --> G[Data Aggregator]
    G --> H[Extractor & Reconstructor]
    H --> I[Confidence Scoring Engine]
    I --> J[Result Repository / Output]
```

- **Orchestrator (`orchestrator/core.py`, `workers.py`)**: Manages the execution lifecycle. Spawns asynchronous task workers, schedules platform-specific checks, and manages resource concurrency limits.
- **Aggregator (`aggregator.py`)**: Merges partial intelligence artifacts collected from standard web requests, headful/headless browsers, and third-party APIs.
- **Confidence & Scoring Engine (`confidence.py`, `score_calculator.py`)**: Evaluates the probability of target matches, discounting false positives via cross-referencing and contextual heuristics.
- **Permutation Engine (`permutator.py`, `platform_permutator.py`)**: Generates variations of target usernames, handles, domains, and dork queries based on platform-specific rules.

### 3.3 Browser Automation & Protocol Evasion (`osint_nexus/core/browser/`, `evasion.py`)

The framework abstracts browser runtime engines, selecting between Playwright and PyQt depending on platform capabilities, system dependencies, or anti-bot defenses.

```mermaid
classDiagram
    class BrowserEngine {
        <<interface>>
        +launch()
        +navigate(url: str)
        +extract_page_data()
        +close()
    }
    class PlaywrightEngine {
        -context: PlaywrightContext
        +stealth_mode: bool
        +navigate(url: str)
        +solve_captcha()
    }
    class PyQtEngine {
        -qpage: QWebEnginePage
        +navigate(url: str)
    }
    class BrowserPool {
        -available_engines: Queue~BrowserEngine~
        +acquire_engine() BrowserEngine
        +release_engine(engine: BrowserEngine)
    }
    class EngineFactory {
        +create_engine(type: EngineType) BrowserEngine
    }

    BrowserEngine <|.. PlaywrightEngine
    BrowserEngine <|.. PyQtEngine
    BrowserPool --> EngineFactory
    EngineFactory ..> BrowserEngine
```

- **Browser Detector & Evasion (`evasion.py`, `mimicry.py`)**: Modifies HTTP request headers, TLS client handshakes, navigator properties, canvas fingerprints, and WebGL context to bypass fingerprinting mechanisms.
- **Detectors (`osint_nexus/core/detectors/`)**: Analyzes defensive controls on target servers:
  - `cdn.py`: Detects Cloudflare, Akamai, Imperva, AWS CloudFront.
  - `tls.py` & `http2.py`: Analyzes JA3/JA4 fingerprints and HTTP/2 settings frames.
  - `timing_entropy.py`: Analyzes wall-clock timing variations for side-channel defense detection.
- **CAPTCHA Solvers (`osint_nexus/core/captcha/`)**:
  - `chained.py`: Enables automated fallback sequences (e.g., attempt local OCR -> `anti_captcha.py` -> `two_captcha.py`).

### 3.4 Storage & Intelligence Persistence (`osint_nexus/core/db/`)

Persistence relies on SQLite via an optimized repository abstraction layer.

```mermaid
erDiagram
    SEARCH_JOB ||--|{ SCAN_RESULT : generates
    SCAN_RESULT ||--o{ FINGERPRINT_DATA : captures
    CACHE_ENTRY ||--o{ SCAN_RESULT : optimizes

    SEARCH_JOB {
        string id PK
        string target_identifier
        datetime created_at
        string status
    }
    SCAN_RESULT {
        string id PK
        string job_id FK
        string provider_name
        float confidence_score
        json raw_payload
    }
    FINGERPRINT_DATA {
        string id PK
        string result_id FK
        string ja3_hash
        string tls_version
        string dns_leak_status
    }
    CACHE_ENTRY {
        string cache_key PK
        json value
        datetime expires_at
    }
```

- **Schema Manager (`schema_manager.py`)**: Handles zero-downtime database upgrades and table versioning.
- **Health Manager (`health_manager.py`)**: Tracks database file lock contention, read/write latency, and transaction integrity.
- **Repositories**: Specialized classes for caching (`cache_repository.py`), fingerprint tracking (`fingerprint_repository.py`), target queries (`search_repository.py`), and result persistence (`result_repository.py`).

---

## 4. End-to-End Scan Execution Flow

The sequence diagram below models the execution flow when a scan request is executed through the framework.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / CLI Client
    participant CLI as CLI / API Layer
    participant Orch as Orchestrator
    participant Perm as Permutator Engine
    participant Pool as Browser Pool
    participant Engine as Playwright / PyQt Engine
    participant Detect as Fingerprint Detector
    participant Solv as Chained CAPTCHA Solver
    participant Agg as Data Aggregator
    participant DB as SQLite Repository
    participant Export as STIX / Report Exporter

    User->>CLI: Execute Scan (Target: "john_doe")
    CLI->>Orch: Initialize Scan Job
    Orch->>Perm: Generate Username Permutations & Dork Variants
    Perm-->>Orch: Return Target Variants

    par Parallel Provider Execution
        Orch->>Pool: Acquire Browser Instance
        Pool-->>Orch: Return Engine Instance
        Orch->>Engine: Navigate to Target URL
        Engine->>Detect: Analyze Page Security & CDN

        alt Defense Block Detected (CAPTCHA)
            Detect-->>Engine: Challenge Triggered
            Engine->>Solv: Request Solve Challenge
            Solv-->>Engine: Return Solved Token
            Engine->>Engine: Inject Token & Resume Navigation
        end

        Engine-->>Orch: Return Extracted Page Payload & Metadata
        Pool->>Pool: Release Engine Instance
    and REST API Provider Scrapes
        Orch->>Orch: Execute direct async requests (GitHub, Aparat, etc.)
    end

    Orch->>Agg: Process & Normalize Raw Payloads
    Agg->>Agg: Calculate Confidence Score & Correlate Artifacts
    Agg->>DB: Persist Target Profile & Scan Results
    DB-->>Agg: Confirm DB Write

    alt Export Requested
        Orch->>Export: Convert Results to STIX 2.1 / JSON
        Export-->>User: Output Formatted Report File
    end

    Orch-->>CLI: Job Completed Notification
    CLI-->>User: Render Final Results on TUI Dashboard
```

---

## 5. Complete Repository File & Directory Map

| Path | Purpose / Description |
| :--- | :--- |
| **`CODEOWNERS`** | Defines project ownership and pull-request review rules. |
| **`DISCLAIMER` / `NOTICE`** | Legal usage notices regarding security auditing and OSINT ethics. |
| **`Makefile`** | Build automation tasks (linting, tests, environment setup). |
| **`pyproject.toml` / `uv.lock`** | Dependency declarations and lockfiles for environment reproducibility. |
| **`data/`** | Static data assets (MAC OUI databases, site definitions, user-agent pools). |
| **`docs/`** | Architectural documentation, mermaid specs, and developer guidelines. |
| **`osint_nexus/api/`** | FastAPI endpoints (`main.py`) and dependency injection providers (`deps.py`). |
| **`osint_nexus/cli/`** | Terminal User Interface dashboard, Rich components, and executable commands. |
| **`osint_nexus/core/browser/`** | Playwright and PyQt browser automation engines, pooling, and factory logic. |
| **`osint_nexus/core/captcha/`** | Modular CAPTCHA solvers (2Captcha, Anti-Captcha) and solver registries. |
| **`osint_nexus/core/db/`** | SQLite abstraction layers, migrations, and repository patterns. |
| **`osint_nexus/core/detectors/`** | Protocol-level fingerprint detectors (TLS, HTTP/2, DNS leaks, Canvas, Timing). |
| **`osint_nexus/core/exporters/`** | Exporters converting output into standardized formats (STIX 2.1). |
| **`osint_nexus/core/fingerbank/`** | Device, operating system, and hardware inference engines. |
| **`osint_nexus/core/orchestrator/`** | Asynchronous worker pool dispatcher and job state managers. |
| **`osint_nexus/core/telemetry/`** | Internal diagnostics, system telemetry probes, and bridge utilities. |
| **`osint_nexus/providers/`** | Provider implementations for target platforms (GitHub, Aparat, Generic web). |
| **`osint_nexus/utils/`** | Rate limiters, security sandboxes, network monitors, and string parsers. |
| **`scripts/`** | Diagnostic scripts for type-checker verification (`repro_*`). |
| **`tests/`** | Full unit, functional, integration, and mock test suites. |

---

## 6. Setup & Developer Quickstart

### Prerequisites
- Python 3.10+
- `uv` or `pip` package manager
- Node.js / Playwright browser binaries (for full headful/headless engine capabilities)

### Installation & Initialization
```bash
# Clone the repository
git clone [https://github.com/org/osint-nexus.git](https://github.com/org/osint-nexus.git)
cd osint-nexus

# Setup environment with uv
uv sync

# Install Playwright browser dependencies
npx playwright install webkit chromium firefox

# Run health diagnostics
python -m osint_nexus.cli.main health
```

### Running Scans via CLI
```bash
# Run reconnaissance on a target handle
python -m osint_nexus.cli.main scan --target "john_doe" --export stix

# Run API Server
uvicorn osint_nexus.api.main:app --reload --port 8000
