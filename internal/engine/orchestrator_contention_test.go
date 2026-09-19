package engine

import (
	"context"
	"testing"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// BenchmarkRunScanContention creates a high-concurrency scenario
// to stress-test lock contention in Orchestrator.
func BenchmarkRunScanContention(b *testing.B) {
	numProviders := 100
	maxConcurrency := 20
	orchestrator, _ := NewOrchestrator(maxConcurrency, nil)
	providers := make([]types.Provider, numProviders)
	for i := 0; i < numProviders; i++ {
		providers[i] = &MockProvider{name: "p", result: &types.IdentityProfile{}}
	}
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		session := orchestrator.RunScan(ctx, "testuser", providers, 500*time.Millisecond)
		for range session.ResultChan {
		}
		for range session.ErrChan {
		}
	}
}
