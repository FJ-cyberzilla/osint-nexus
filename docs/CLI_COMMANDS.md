# OSINT-Nexus & Omni-Masquerade OS CLI & TUI Command Reference

> **Developed by [FJ™ Cybertronic Systems](https://github.com/FJ-cyberzilla)**

`nexus-cli` is the high-performance command-line and interactive terminal UI (TUI) reconnaissance engine built natively in Go (`go1.23+`).

## Makefile Unified Entry Points

- **`make help`**: Display available Makefile targets.
- **`make install`**: Initialize environment and build binaries.
- **`make run`**: Launch the unified TUI Command Center dashboard.
- **`make test`**: Run test suite.

## Usage

```bash
nexus-cli [flags]
```

## Global Flags

- `--config string`: Path to the YAML configuration file (default is `./configs/config.yaml`).
- `-h, --help`: Display help for `nexus-cli`.

## Omni-Masquerade OS & Controllers

Omni-Masquerade OS provides comprehensive OSINT database generation starting from a username seed. It is governed by four modular control sub-components:
- **`temp` (`temp.go`)**: Ephemeral session scratchpads, cache files, and temporary browser profile directories.
- **`score` (`score.go`)**: Weighted confidence scoring, false positive filtering, and metadata credibility evaluation.
- **`resolve` (`resolve.go`)**: Username canonicalization, handle normalization, and pivot deduplication.
- **`helper` (`helper.go`)**: Execution logging, progress reporting, and configuration validation.
- **Central Nerve & Dork Engine**: Orchestrates real-time database generation, dork queries, and operation completion summaries.

## Advanced Evasion & Transport Layers

- **Behavioral Emulation (`behavior.go`)**: Stochastically distributed request jitter and human-like typing/cursor delays to defeat bot detection heuristics.
- **Canvas & WebGL Entropy Injection (`entropy.go`)**: Imperceptible micro-noise injection into HTMLCanvasElement rendering data and WebGL contexts to defeat device fingerprint tracking.
- **HTTP/3 & QUIC Masquerade (`http3.go`)**: QUIC/UDP transport routing and secure request dispatching under TLS 1.3.
- **TCP Socket Tuning (`tcp.go`)**: Raw socket options for per-profile IP TTL, window size, and keep-alive configuration.

## Interactive TUI Command Center (Modular UI)

When invoked via `make run`, `nexus-cli` launches the interactive **Bubble Tea** TUI Command Center with modular components (`internal/ui/panels.go`, `internal/ui/display.go`, `internal/ui/sys_status.go`):

1. **Target Prompt**: Enter the target username to begin the reconnaissance pipeline.
2. **Dashboard Views (Tabs)**:
   - **Overview**: Real-time device metadata, TLS fingerprint (JA3/JA3S), User-Agent, telemetry sockets, active sessions, and secondary pivot summaries.
   - **Results**: Live color-coded platform probes (✓ Found, ✗ Not Found / 404, ? Error) across Instagram, Telegram, Threads, Rubika, and more.
   - **Graph**: Relationship mapping nodes and edges connecting discovered identities.
   - **Analysis**: Stylometric analysis, heatmap intensity, and custom analytical charts.
   - **Network**: Fingerbank hardware profiles, vulnerability scores, and DNS leak detection.
   - **Alerts**: Priority-based anomaly detection alerts, system errors, and advisories.
3. **Panels & Completion**:
   - **Omni-Masquerade Central Nerve Panel**: Live orchestration status.
   - **Dork Results**: Search engine query intelligence.
   - **Final Findings Summary**: Prominent operation finished statistics and summary.
   - **App Status vs. Target Telemetry**: Clear visual separation of local app runtime status from target intelligence.
4. **Keyboard Controls**:
   - **Navigation**: `←` / `→` or `Tab` / `Shift+Tab` to switch tabs.
   - **Scrolling**: `↑` / `↓`, `j` / `k`, `PgUp` / `PgDown`, `Ctrl+U` / `Ctrl+D`, `Home` / `End`, `g` / `G`.
   - **Quit**: `q` or `Ctrl+C`.

---
*Developed by FJ™ Cybertronic Systems.*
