# OSINT-Nexus Command Center TUI

> **Developed by [FJ™ Cybertronic Systems](https://github.com/FJ-cyberzilla)**

The OSINT-Nexus Command Center is an industrial-grade, real-time TUI dashboard built with `github.com/charmbracelet/bubbletea` and styled using `github.com/charmbracelet/lipgloss`. It provides comprehensive asynchronous reconnaissance insights and stream updates, launched uniformly via `make run`.

## Core Architecture & Modular UI (`internal/ui/`)

The TUI codebase is modularized into dedicated packages and components:
- **`panels.go`**: Specialized UI panels including the Omni-Masquerade Central Nerve Status Panel, Dork Results Panel, and Final Findings Summary Panel.
- **`display.go`**: Master view rendering coordination across dashboard tabs.
- **`sys_status.go`**: Dedicated rendering for local application status telemetry (socket metrics, active sessions, system health) clearly separated from target reconnaissance intelligence.

## Core Features & Views

### 1. Unified Dashboard Tabs
- **Overview**: Target metadata, device type, timezone, JA3/JA3S TLS fingerprinting, User-Agent, telemetry socket metrics, active sessions, and secondary pivot summaries (emails, social media, dorks).
- **Results**: Real-time color-coded platform probes (`✓ Found`, `✗ Not Found / 404`, `? Error`), powered by robust provider HTTP lookups across Instagram, Telegram, Threads, Rubika, and more.
- **Graph**: Relationship mapping nodes and directed edges linking discovered identities.
- **Analysis**: Stylometric analysis, heatmap intensity maps, and analytical chart metrics.
- **Network**: Fingerbank hardware profiles, vendor info, operating system details, vulnerability detection, and DNS leak test results.
- **Alerts**: Priority-based anomaly detection alerts, system advisories, and operational errors.

### 2. Operational Feedback, Dorks & Final Findings
- **Omni-Masquerade Central Nerve Panel**: Live status reporting on the orchestration engine, workers, and database generation.
- **Dork Results Panel**: Display of targeted search engine dorks and query intelligence results.
- **Operation Finished Statistics & Final Findings**: Prominent completion summary displaying total verified assets, elapsed time, and confidence ratings.
- **Fallback Resilience**: Automatic offline/demo simulation fallback mode ensuring rich populated results and telemetry even in isolated network environments.

### 3. Keyboard Navigation & Controls
- **Tab Switching**: `←` / `→` or `Tab` / `Shift+Tab`.
- **Content Scrolling**: `↑` / `↓`, `j` / `k`, `PgUp` / `PgDown`, `Ctrl+U` / `Ctrl+D`, `Home` / `End`, `g` / `G`.
- **Termination**: `q` or `Ctrl+C`.
