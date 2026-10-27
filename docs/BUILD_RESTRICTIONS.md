# OSINT-Nexus Build & Compilation Restrictions

## Go Constraints
- **Go Version**: Requires Go `1.23+`.
- **Zero Placeholders**: Production code must be fully implemented with zero stubs, truncation comments, or magic numbers.
- **Compilation Guarantee**: All packages must compile cleanly via `go build ./...` and pass tests via `go test ./...`.
