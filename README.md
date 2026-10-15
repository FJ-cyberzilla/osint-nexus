# Osint Nexus

[![Go CI](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/FJ-cyberzilla/osint-nexus)
![Go Version](https://img.shields.io/badge/go-1.23%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*FJ™ Cybertronic Systems*

**An industrial-grade, low-level OSINT and network reconnaissance engine built natively in Go.**

---

⛳ What Does OSINT Nexus Do?

OSINT Nexus is an all-in-one automated reconnaissance, threat intelligence, and digital footprinting platform. Instead of relying on fragmented scripts, it unifies deep protocol inspection, social media profiling, network telemetry, and relational data analysis into a single deterministic engine.

Specifically, OSINT Nexus provides:

* **Multi-Platform Digital Footprinting & Social Recon:** Queries and extracts identity data across over 15 distinct provider networks (including GitHub, Reddit, Twitter/X, Instagram, Telegram, TikTok, Twitch, Pinterest, Medium, SoundCloud, LinkedIn, Facebook, Aparat, and device profiling via Fingerbank).
* **Deep Content & Credential Extraction:** Employs streaming-based parsers (`internal/extractor`) to harvest emails, PGP public keys, social handles, image metadata (EXIF/Meta), and stylometric writing patterns from target assets.
* **Advanced Network & Protocol Probing:** Performs raw socket manipulation, custom TLS fingerprinting (JA3/JA4), HTTP/HTTP2/TCP probes, WebRTC parser analysis, DNS record traversal, and real-time DNS and credential leak detection (`internal/detector`).
* **Stealth, Evasion & Browser Automation:** Features automated search engine dorking, captcha solving capabilities (OCR solvers), evasion strategies, and a managed browser pool (`internal/engine/browser_pool`) for dynamic client-side rendering.
* **Relational Identity Pivoting & Graph Mapping:** Constructs interconnected entity graphs (`internal/graph`) to link disparate usernames, emails, IP addresses, and digital artifacts, allowing operators to visualize complex adversary pivots and export intelligence packages in STIX 2.1 format.
* **Low-Level System Telemetry & Kernel Tracing:** Integrates advanced monitoring modules including eBPF network monitors and Android socket tracers to inspect low-level socket activity and system metrics (`internal/telemetry`).
* **Industrial Command Center TUI:** Provides a real-time, high-performance terminal user interface built with `charmbracelet/lipgloss` for managing live investigations and streaming output.

---

# ⛩️ Architecture & Directory Separation

The project enforces a strict, modular Go layout separating public APIs, internal engines, low-level detectors, parsing pipelines, and terminal interfaces:

```text
.
├── cmd/
│   └── nexus-cli/        # CLI application entrypoint
├── internal/
│   ├── captcha/          # Captcha solvers and OCR clients
│   ├── cli/              # Root commands and CLI argument routers
│   ├── config/           # YAML configuration parser and validators
│   ├── db/               # PostgreSQL/Redis connection layers, repositories, and schemas
│   ├── detector/         # Low-level protocol probes (DNS, TLS, HTTP2, Anomaly, Leak)
│   ├── engine/           # Provider orchestrator, browser pool, dorking, evasion, and queues
│   ├── exporter/         # Threat intelligence export bindings (STIX 2.1)
│   ├── extractor/        # Streaming-based parsing pipeline (Email, Social, PGP, Meta, Stylometry)
│   ├── graph/            # Relational identity and pivoting graph builders
│   ├── network/          # Raw socket client, DoH, data drops, and proxy tunnels
│   ├── provider/         # External platform target connectors (GitHub, Reddit, Twitter, etc.)
│   ├── telemetry/        # eBPF monitors, Android socket tracers, and metrics
│   ├── types/            # Core domain models, confidence scoring, and error interfaces
│   └── ui/               # Industrial-grade Command Center TUI (`charmbracelet/lipgloss`)
├── pkg/
│   ├── osint/            # Publicly exportable client APIs and agent wrappers
│   └── sanitizer/        # Strict input sanitization and normalizers
└── docs/                 # Comprehensive documentation manuals

🛠️ Build & Installation Guide
OSINT Nexus features a unified Makefile to handle environment initialization, compilation, testing, and quality gates. To inspect all available tasks and options at any time, run make help.
Quick Setup

# Clone the repository
git clone [https://github.com/FJ-cyberzilla/osint-nexus.git](https://github.com/FJ-cyberzilla/osint-nexus.git)
cd osint-nexus

# Initialize environment and build the application binary
make install
Complete Makefile Operations Reference

CommandDescription
make installPrepare environment and build the application
make buildBuild engine binary with embedded build metadata (bin/nexus-cli)
make lintRun static code analysis and quality checks
make testRun unit test suite with coverage reporting
make coverageGenerate HTML coverage report
make benchRun performance benchmarks
make complexityAnalyze cyclomatic complexity using gocyclo
make fmtFormat all Go source files
make vetRun go vet static analysis
make checkRun all quality gates
make runRun engine (Usage: make run ARGS="-d --verbose")
make aboutDisplay module metadata
make versionDisplay clean semver string
make statsShow project statistics
make cleanPurge build artifacts, logs, temp files
make clean-allPurge artifacts AND Go caches
make helpDisplay this help interface

#⚡ Usage & Command Center
The primary interface for executing probes and managing investigations is the compiled binary bin/nexus-cli.
Basic CLI Commands
# Display general help and command usage
./bin/nexus-cli --help

# Execute a targeted DNS reconnaissance probe
./bin/nexus-cli probe dns target.com

# Run the engine interactively via the Makefile wrapper
make run ARGS="probe dns target.com --verbose"


Command Center TUI
OSINT Nexus includes an immersive, real-time industrial terminal dashboard powered by charmbracelet/lipgloss

# Launch the Command Center Dashboard
./bin/nexus-cli dashboard
or  using  make  run

Refer to docs/TUI_COMMAND_CENTER.md for full layout specifications and keyboard shortcuts.

# 🧪  Development & Quality Standards
Tech Stack: Go 1.23+, charmbracelet/lipgloss (Terminal UI), rotisserie/eris (Structured Error Handling), uber-go/mock (Testing framework).
Error Handling Pattern: All operations capable of failing must return an error wrapped via eris to guarantee complete stack trace visibility:
if err != nil {
    return eris.Wrap(err, "failed to execute reconnaissance probe")
}



*Developed by FJ™ Cybertronic Systems.*
-- FJ-cyberzilla®, Spring MCXXVI --
