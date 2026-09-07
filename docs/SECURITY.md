# Security Policy

## Reporting a Vulnerability
Please report security vulnerabilities by opening a GitHub Issue with the "security" label. Do not disclose vulnerabilities in public comments.

## Disclosure
We appreciate responsible disclosure and will address reported issues promptly.

## Security Hardening & Best Practices
The project enforces strict security standards, including:

- **Cryptographic Integrity:** Use of `crypto/rand` for all random number generation, replacing weak `math/rand` to prevent predictability attacks (G404/CWE-338).
- **Context Management:** Strict adherence to context lifecycle management. All browser-based and network probes utilize combined cancellation functions to prevent resource leaks and context shadowing (G118/CWE-400).
- **Resource Integrity:** Mandatory error handling for all resource cleanup operations (`defer Close()`), including explicit error checks and return paths for database and network body closures to prevent silent failures (G104/CWE-703).
- **Access Control:** Application directories created with restricted permissions (`0750`) to ensure system integrity and prevent unauthorized access (G301/CWE-276).
