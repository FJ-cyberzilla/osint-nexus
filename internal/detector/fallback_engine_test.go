package detector

import (
	"context"
	"errors"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"testing"
)

// MockProbe allows simulating probe behavior.
type MockProbe struct {
	data types.FingerprintData
	err  error
}

func (m *MockProbe) Probe(ctx context.Context, targetURL string) (types.FingerprintData, error) {
	return m.data, m.err
}

func TestFallbackEngine(t *testing.T) {
	ctx := context.Background()
	targetURL := "https://example.com"

	t.Run("PrimarySuccess", func(t *testing.T) {
		primary := &MockProbe{data: types.FingerprintData{Type: "primary"}}
		fallback := &MockProbe{data: types.FingerprintData{Type: "fallback"}}
		engine := NewFallbackEngine([]BrowserProbe{primary}, fallback)

		data, err := engine.Probe(ctx, targetURL)
		if err != nil {
			t.Fatalf("expected success, got %v", err)
		}
		if data.Type != "primary" {
			t.Errorf("expected primary, got %s", data.Type)
		}
	})

	t.Run("PrimaryFailureFallbackSuccess", func(t *testing.T) {
		primary := &MockProbe{err: errors.New("fail")}
		fallback := &MockProbe{data: types.FingerprintData{Type: "fallback"}}
		engine := NewFallbackEngine([]BrowserProbe{primary}, fallback)

		data, err := engine.Probe(ctx, targetURL)
		if err != nil {
			t.Fatalf("expected success, got %v", err)
		}
		if data.Type != "fallback" {
			t.Errorf("expected fallback, got %s", data.Type)
		}
	})

	t.Run("AllFailure", func(t *testing.T) {
		primary := &MockProbe{err: errors.New("fail")}
		fallback := &MockProbe{err: errors.New("fallback fail")}
		engine := NewFallbackEngine([]BrowserProbe{primary}, fallback)

		_, err := engine.Probe(ctx, targetURL)
		if err == nil {
			t.Error("expected error, got nil")
		}
	})
}
