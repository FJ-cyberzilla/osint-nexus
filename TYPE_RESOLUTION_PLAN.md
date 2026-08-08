# Plan for Resolving Incompatible Type Assignments

The primary strategy for resolving `[arg-type]`, `[return-value]`, and `[list-item]` errors is to move from implicit/structural typing (e.g., using `dict[str, str]` as a stand-in for a model) to **explicit, class-based modeling** and **Protocol-based interfaces**.

## Phase 1: Assessment & Prioritization
1. Analyze the representative errors extracted:
   - `osint_nexus/core/reconstructor.py`: Type mismatch (`dict[str, list[Never]]` vs `RelationshipGraph`).
   - `tests/core/test_reconstructor.py`: Data structure mismatch (`dict[str, str]` vs `Account` model).
   - `osint_nexus/core/compliance.py`: Strict type requirement (`Scrubbable`) vs loose input (`dict[str, str]`).

2. Prioritize errors in core logic (`osint_nexus/core/`) before addressing test-only errors, as these represent real structural fragility.

## Phase 2: Remediation Strategy

### 1. Model Hardening (Replacing Dictionaries with DataClasses/Pydantic)
- **Problem:** Functions expect a model (e.g., `Account`) but receive a dictionary (`dict[str, str]`).
- **Pattern:** Use `dataclasses` or Pydantic models to replace raw dictionaries.
- **Action:** Define proper models and update function signatures/instantiations to enforce this.

### 2. Interface Refinement (Using Protocols)
- **Problem:** `ComplianceEngine.sanitize` expects `dict[str, Scrubbable]`, but receives `dict[str, Collection[str]]`.
- **Pattern:** Define a `Protocol` for `Scrubbable` if it's not already one, ensuring the expected structure is explicitly satisfied. Use `typing.Protocol` to define required behaviors rather than relying on exact class matches (structural typing).

### 3. Strengthening Generics
- **Problem:** `dict[Any, Any]` or `list[Any]` usage.
- **Pattern:** Use specific generic type arguments.
- **Action:** Replace `Any` with specific types or bounded TypeVars where possible.

## Phase 3: Validation
- **Cycle:** Plan -> Act -> Validate.
- For each remediation:
  1. Create/Update a test case that specifically targets the type boundary.
  2. Implement the change.
  3. Verify with `mypy` and `pytest`.
- **Constraint:** Do not disable errors. If an error is deemed a false positive, it must be documented per project conventions (if applicable) or fixed by adding appropriate type hints, NOT by suppressing the error.
