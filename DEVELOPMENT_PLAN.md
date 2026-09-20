# OSINT-Nexus Unified Development Plan

This document is the single source of truth for the project's roadmap, progress, and actionable task backlog.

## Core Objectives
OSINT-Nexus is a high-accuracy, low-level OSINT and network reconnaissance engine. Our primary focus is deterministic data integrity across network protocol boundaries.

## Roadmap & Progress

### Completed Phases
- Phase 1: Project Design & Layout
- Phase 2: Database Layer & Persistence
- Phase 3: Core Business Logic (Anomaly & Stylometry)
- Phase 4: Session Tracking & Pipeline Integration

### Completed Phase 5: Validation, Benchmarking & Audit
- [x] End-to-end integration tests (Cleanup/Review)
- [x] Performance benchmarking (hot-path: `internal/engine/orchestrator.go` cleaned, benchmark added to `internal/detector/dns_leak_test.go`)
- [x] Thermo-nuclear code quality audit.
- [x] Create high-performance `queue.go` for orchestrator.
- [x] Audit memory allocations in `internal/detector`.
- [x] Investigate lock contention in `internal/engine/orchestrator.go` and `browser_pool`.
- [x] Audit context propagation and error wrapping in `internal/detector` (Refactored `credential_leak_detector.go` to use `eris`).
### Completed Phase 6: ABI Compliance for eBPF Components
- [x] Audit eBPF telemetry implementation.
- [x] Refactor `android_socket_tracer.go` to use explicitly defined structs for BPF map key/value mapping to ensure ABI stability.
- [x] Update documentation (`README.md`, `docs/PROJECT_MANAGEMENT.md`).

### Completed Phase 7: Final Testing & Verification
- [x] Add unit tests for BPF map iteration with mocked/simulated map data.

### Completed Phase 8/9: CLI Migration & Entry Point Consolidation
- [x] Integrate `osint.Agent` and `engine.Orchestrator` into CLI.
- [x] Enforce `nexus-cli` binary as sole entry point via Makefile (`make run`, `make diagnosis`, `make about`).
- [x] Cleanup Makefile to use compiled binary exclusively.

### Future Architectural Initiatives
- [ ] Complete tool integration.

## Actionable Task Backlog

### Immediate / Critical
- [ ] Audit memory allocations in `internal/detector`.
- [ ] Investigate lock contention in `internal/engine/orchestrator.go`.
- [ ] Audit context propagation and error wrapping in `internal/detector`.

### Future / Maintenance
- [ ] Expand test coverage for `internal/detector`.
- [ ] Refactor CLI commands in `internal/cli/`.
- [ ] Optimize `ResultRepository.Query` dynamic SQL construction.
- [ ] Review `internal/extractor` and `internal/detector` for technical debt.
