# OSINT-Nexus Command Center TUI

The OSINT-Nexus Command Center is an industrial-grade, real-time TUI dashboard built with `github.com/charmbracelet/bubbletea` and styled using `github.com/charmbracelet/lipgloss`. It provides comprehensive asynchronous reconnaissance insights and stream updates.

## Core Features & Views

### 1. Unified Dashboard Tabs
- **Overview**: Target metadata, device type, timezone, JA3/JA3S TLS fingerprinting, User-Agent, telemetry socket metrics, active sessions, and secondary pivot summaries (emails, social media, dorks).
- **Results**: Real-time color-coded platform probes (`✓ Found`, `✗ Not Found / 404`, `? Error`).
- **Graph**: Relationship mapping nodes and directed edges linking discovered identities.
- **Analysis**: Stylometric analysis, heatmap intensity maps, and analytical chart metrics.
- **Network**: Fingerbank hardware profiles, vendor info, operating system details, vulnerability detection, and DNS leak test results.
- **Alerts**: Priority-based anomaly detection alerts, system advisories, and operational errors.

### 2. Operational Feedback & Telemetry
- **Active Status Reporting**: Dynamic progress bar, animated spinner (`spinner.Dot`), estimated time of arrival (ETA), and live worker status.
- **Fallback Resilience**: Automatic offline/demo simulation fallback mode ensuring rich populated results and telemetry even in isolated network environments.

### 3. Keyboard Navigation & Controls
- **Tab Switching**: `←` / `→` or `Tab` / `Shift+Tab`.
- **Content Scrolling**: `↑` / `↓`, `j` / `k`, `PgUp` / `PgDown`, `Ctrl+U` / `Ctrl+D`, `Home` / `End`, `g` / `G`.
- **Termination**: `q` or `Ctrl+C`.
