package engine

import (
	"context"
	"testing"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

func BenchmarkRunScan(b *testing.B) {
	orchestrator, _ := NewOrchestrator(2, nil)
	providers := []types.Provider{
		&MockProvider{name: "p1", result: &types.IdentityProfile{}},
		&MockProvider{name: "p2", result: &types.IdentityProfile{}},
	}
	ctx := context.Background()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		session := orchestrator.RunScan(ctx, "testuser", providers, 100*time.Millisecond)
		for range session.ResultChan {
		}
		for range session.ErrChan {
		}
	}
}
