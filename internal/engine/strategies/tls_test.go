package strategies

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/db"
	"github.com/osint-nexus/internal/types"
)

func TestTLSStrategy_Extract(t *testing.T) {
	// Create a temporary repo for testing
	repo, err := db.NewFingerprintRepository("nonexistent")
	if err != nil {
		t.Fatalf("failed to create repo: %v", err)
	}

	strategy := NewTLSStrategy(repo)

	tests := []struct {
		name       string
		data       types.FingerprintData
		wantDevice string
		wantConf   float64
	}{
		{
			name: "Known JA3",
			data: types.FingerprintData{
				Type:    "tls_ja3",
				Payload: TLSPayload{JA3Hash: "72a589da586844d7f0818ce684948eea"},
			},
			wantDevice: "Chrome 120 on Windows 10",
			wantConf:   0.90,
		},
		{
			name: "Unknown JA3",
			data: types.FingerprintData{
				Type:    "tls_ja3",
				Payload: TLSPayload{JA3Hash: "unknown"},
			},
			wantDevice: "unknown",
			wantConf:   0.10,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := strategy.Extract(context.Background(), tt.data)
			if err != nil {
				t.Fatalf("Extract() error = %v", err)
			}

			payload, ok := got.Data.Payload.(TLSOutputPayload)
			if !ok {
				t.Fatalf("got invalid payload type %T, want TLSOutputPayload", got.Data.Payload)
			}
			if payload.InferredDevice != tt.wantDevice {
				t.Errorf("got inferred_device %v, want %v", payload.InferredDevice, tt.wantDevice)
			}
			if got.Confidence != tt.wantConf {
				t.Errorf("got confidence %v, want %v", got.Confidence, tt.wantConf)
			}
		})
	}
}
