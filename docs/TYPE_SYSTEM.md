# OSINT-Nexus Go Type System & Architecture Standards

## 1. Statically Typed Domain Models
All core domain data structures are defined with strict static types in Go, avoiding generic `map[string]any` or `interface{}` unless handling un-schematized JSON payloads.

- **Explicit Struct Tags**: Every struct field intended for persistence or transmission includes explicit `json:"field_name"` and `yaml:"field_name"` struct tags using `snake_case`.
- **Optional Fields**: Optional struct fields use pointers (`*string`, `*int`) to distinguish between explicit zero-values and absent (`nil`) values.

## 2. Core Domain Interfaces (`internal/types`)
- **`Provider`**: Interface defining provider contracts:
  ```go
  type Provider interface {
      Name() string
      CheckUsername(ctx context.Context, username string) (*IdentityProfile, error)
  }
  ```
- **`IdentityProfile`**: Primary structure encapsulating discovered accounts, emails, social media references, and confidence scoring.

## 3. Concurrency & Context Propagation
- All network operations, HTTP requests, and engine worker pools enforce `context.Context` parameters for deterministic timeouts and cascading cancellation.
- Zero-allocation byte slicing (`[]byte`) is utilized for raw packet and string processing on hot paths.
