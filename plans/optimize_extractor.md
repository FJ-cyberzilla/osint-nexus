# Optimization Plan for `internal/extractor`

## Goal
Reduce memory allocation and execution time in the `internal/extractor` package to improve overall OSINT scan performance.

## Bottleneck Analysis
- The `BenchmarkPivotExtractor_Extract` test confirms that the extraction pipeline is the primary resource consumer.
- High memory usage is attributed to `regexp.FindAllString` on raw HTML strings and repeated object creation.

## Proposed Optimizations

### 1. Regex Pre-compilation (Already mostly done, but needs verification)
Ensure all regexes are compiled once at initialization and re-used.

### 2. Streamline Memory Allocation (`internal/extractor/orchestrator.go`)
- The current implementation of `extractStreaming` creates a new result struct and appends slices repeatedly.
- **Optimization**: Pre-allocate result slice capacities based on estimated result sizes or use a single buffer/map to collect findings before final conversion.

### 3. Buffer Reuse (`internal/extractor/email_extractor.go`)
- The `EmailExtractor` uses a `map[string]struct{}` which is good for uniqueness, but it is re-initialized for every `Extract` call.
- **Optimization**: Use a `sync.Pool` for reusable maps or buffers in extractors, if feasible, to minimize allocations.

## Verification
- Run `go test -bench=BenchmarkPivotExtractor_Extract -benchmem ./internal/extractor/...` before and after to verify improvements using `benchstat`.
