package detector

import (
	"context"
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/telemetry"
)

func TestCredentialLeakDetector_Analyze(t *testing.T) {
	metrics := telemetry.NewMetrics()
	detector, err := NewCredentialLeakDetector(metrics)
	if err != nil {
		t.Fatalf("failed to create detector: %v", err)
	}

	tests := []struct {
		name     string
		data     string
		wantLeak bool
	}{
		{
			name:     "leaked password",
			data:     "my password: secret123",
			wantLeak: true,
		},
		{
			name:     "no leak",
			data:     "just some normal text",
			wantLeak: false,
		},
		{
			name:     "key present",
			data:     "API_KEY=12345abcd",
			wantLeak: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			leaked, err := detector.Analyze(context.Background(), tt.data)
			if err != nil {
				t.Fatalf("Analyze failed: %v", err)
			}
			if leaked != tt.wantLeak {
				t.Errorf("got leaked %v, want %v", leaked, tt.wantLeak)
			}
		})
	}

	if metrics.Snapshot().CredentialLeaks != 2 {
		t.Errorf("expected 2 credential leaks in telemetry, got %d", metrics.Snapshot().CredentialLeaks)
	}
}
