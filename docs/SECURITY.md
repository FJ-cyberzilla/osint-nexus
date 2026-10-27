# OSINT-Nexus Security Policy

## Reporting Vulnerabilities
If you discover a security vulnerability within `osint-nexus`, please report it via private disclosure rather than public issue trackers.

## Code Security Standards
- **Zero Secrets in Repository**: Never commit API keys, credentials, or `.env` files.
- **Error Handling**: No `panic()` calls in library packages (`pkg/`, `internal/`). All errors must be wrapped with contextual information using `github.com/rotisserie/eris`.
- **Context Propagation**: Enforce `context.Context` on all network and API calls to prevent resource leaks and guarantee deterministic timeouts.
