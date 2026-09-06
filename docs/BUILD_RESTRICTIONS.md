# Build Restrictions and Dependency Policy

## Policy Statement
To ensure security, determinism, and environment stability, **OSINT-Nexus strictly prohibits the installation of any additional tools, dependencies, or software packages** during the build or development lifecycle that are not already explicitly required by the project and managed via the defined `Makefile` targets.

## Enforcement
- **No Ad-Hoc Installations:** Developers and CI environments must NOT run commands such as `apt-get install`, `brew install`, `npm install`, or other package manager commands to install system-level tools or libraries within the context of the project build process.
- **Pre-Defined Targets Only:** All required tasks (build, test, lint, clean, etc.) must be executed exclusively via the provided `Makefile` targets.
- **Environment Stability:** Changes to the development environment must be coordinated with the project maintainers and updated in the project documentation/configuration, not patched locally by ad-hoc installations.

If a new dependency is required, it must be proposed, reviewed, and integrated into the official project configuration (e.g., `go.mod`, `Makefile`) before it can be used.
