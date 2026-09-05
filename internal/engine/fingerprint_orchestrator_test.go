package engine

import (
	"context"
	"errors"
	"testing"

	"github.com/osint-nexus/internal/engine/strategies"
	"github.com/osint-nexus/internal/types"
)

type MockPayload struct{ Val int }

func (p MockPayload) PayloadType() string { return "mock" }

// MockStrategy implements FingerprintStrategy for testing.
type MockStrategy struct {
	name string
	fail bool
}

func (m *MockStrategy) Name() string {
	return m.name
}

func (m *MockStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	if m.fail {
		return types.FingerprintResult{}, errors.New("simulated error")
	}
	return types.FingerprintResult{
		Name:       m.name,
		Data:       types.FingerprintData{Type: m.name, Payload: MockPayload{Val: 1}},
		Confidence: 0.5,
	}, nil
}

func TestFingerprintOrchestrator_Register(t *testing.T) {
	orchestrator := NewFingerprintOrchestrator(nil)
	orchestrator.Register(&MockStrategy{name: "strat1", fail: false})

	results, err := orchestrator.Run(context.Background(), types.FingerprintData{Payload: MockPayload{Val: 1}})

	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if len(results) != 1 {
		t.Fatalf("Expected 1 result, got %d", len(results))
	}
}

func TestFingerprintOrchestrator_Run_WithError(t *testing.T) {
	strats := []strategies.FingerprintStrategy{
		&MockStrategy{name: "strat1", fail: false},
		&MockStrategy{name: "strat2", fail: true},
	}

	orchestrator := NewFingerprintOrchestrator(strats)
	_, err := orchestrator.Run(context.Background(), types.FingerprintData{Payload: MockPayload{Val: 1}})

	if err == nil {
		t.Fatal("Expected error, got nil")
	}
}
