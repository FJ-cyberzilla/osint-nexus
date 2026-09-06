# OSINT-Nexus Command Center TUI

The OSINT-Nexus Command Center is an industrial-grade, real-time TUI dashboard providing comprehensive reconnaissance insights. It utilizes an Elm-inspired architecture (`bubbletea`) to handle asynchronous OSINT data streams efficiently.

## Core Features

### 1. Unified Information Panels
- **System Metrics:** Real-time visibility into Device Type, TLS Fingerprint (API or System Default), Telemetry status, and Heatmap generation.
- **Fingerbank Findings:** Advanced profiling results (Device, Vendor, OS), confidence scores, and vulnerability alerts.
- **Intelligence Mapping:**
  - **Relations:** Mapped associations discovered during the scan.
  - **Shadow Users:** Identified shadow identities.
  - **Results:** Color-coded status updates (✓ Found, ✗ Not Found, ? Uncertain).

### 2. Operational Feedback
- **Active Status Reporting:** Dynamic status bar providing granular details on the current engine action, including API usage stats.
- **Spinner/Progress Alignment:** Integrated spinner animation alongside progress bars for immediate visual confirmation of engine activity.

### 3. Centralized Alerting
The TUI includes a priority-based alert system for real-time engine health monitoring. All errors (including Fingerbank API failures, timeouts, or network issues) are rendered in a prominent **Yellow** (`colorUnknown`) to ensure immediate operator visibility.

| Alert Level | Color | Purpose |
| :--- | :--- | :--- |
| **SYSTEM ALERTS** | Yellow | Critical reconnaissance failures, Fingerbank errors, or fallback engine issues. |
| **ADVISORY** | Light Blue | Transient issues, rate-limiting, or non-critical network warnings. |

## Integration
The dashboard is maintained in `internal/ui/dashboard.go`. UI updates are streamed using typed messages (e.g., `ErrorMsg`, `AdvisoryMsg`, `RelationMsg`) to ensure deterministic UI state transitions.
