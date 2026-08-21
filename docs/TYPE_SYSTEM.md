# Type Safety Guidelines

## Fingerprint Architecture

The system utilizes a structured registry pattern for fingerprinting strategies.

- **`FingerprintStrategy` Protocol**: All strategies MUST implement the `FingerprintStrategy[T_Data, T_Result]` protocol, where `T_Data` and `T_Result` are bound to `JSONValue` and `JSONObject` respectively.
- **Heterogeneous Registration**: The `FingerprintStrategyRegistry` stores strategies as `FingerprintStrategy[Any, Any]` to support different input/output types while ensuring safe type handling at the boundary.
- **Implementation Standards**:
    - Strategies MUST define `name: str`.
    - Strategies MUST implement `extract(self, data: JSONValue) -> JSONObject`.
    - All implementations MUST be decorated with `@beartype` to enforce runtime type checking.

## Protocol Bridging

When third-party libraries (e.g., `curl_cffi`, `httpx`) do not directly implement required internal interfaces (e.g., `SessionProtocol`):

- **Use Wrappers**: Implement a wrapper class (e.g., `SessionWrapper`) that delegates calls to the underlying implementation while adhering to the internal `Protocol` definition.
- **Standardize Interface**: Ensure the wrapper exposes all required methods in the `Protocol` (e.g., both `close` and `aclose` for asynchronous sessions).

## Explicit Modeling

- **Prefer DataClasses/Pydantic**: Replace unstructured `dict` types with formal models for complex data structures to improve type safety and maintainability.
