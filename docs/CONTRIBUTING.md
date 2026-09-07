# Contributing to OSINT-Nexus

We welcome contributions! Please follow these guidelines:

## Development Workflow
- **Branching:** Use descriptive branch names (e.g., `feature/my-feature`, `fix/my-fix`).
- **Pull Requests:** Ensure all tests pass.
- **Error Handling:** Strictly use `github.com/rotisserie/eris` for wrapping errors to provide actionable context.
- **Tests:** Add industrial-level unit tests for new features using `go test`.

## Getting Started
1. Fork the repository.
2. Create a branch (`git checkout -b feature/my-feature`).
3. Make your changes.
4. Run tests: `go test ./...`
5. Push your branch and open a PR.
