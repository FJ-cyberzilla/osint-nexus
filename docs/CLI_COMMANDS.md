# OSINT-Nexus CLI Commands

The `nexus-cli` provides a set of powerful tools for network reconnaissance and OSINT data gathering.

## Global Flags

- `--config`: Path to the configuration file (default is `./configs/config.yaml`).

## Commands

### `status`
Prints a report on the current status of the engine, including build information and engine health.

### `probe`
Perform various network and protocol-specific probes on a target.

#### `dns`
Perform a DNS probe on a target hostname.

**Usage**:
```bash
./nexus-cli probe dns [hostname]
```

**Example**:
```bash
./nexus-cli probe dns google.com
```

#### tls
Perform a TLS probe on a target address (e.g., `hostname:port`).

**Usage**:
```bash
./nexus-cli probe tls [address]
```

**Example**:
```bash
./nexus-cli probe tls google.com:443
```

#### http
Perform an HTTP probe on a target URL (e.g., `https://example.com`).

**Usage**:
```bash
./nexus-cli probe http [url]
```

**Example**:
```bash
./nexus-cli probe http https://google.com
```

