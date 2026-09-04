package strategies

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestTCPStrategy_Extract(t *testing.T) {
	strategy := NewTCPStrategy()

	tests := []struct {
		name     string
		data     types.FingerprintData
		wantOS   string
		wantConf float64
	}{
		{
			name:     "Windows 10/11",
			data:     types.FingerprintData{Type: "tcp_stack", Payload: TCPPayload{TTL: 128, TCPOptions: []string{"wscale"}}},
			wantOS:   "Windows 10/11",
			wantConf: 0.85,
		},
		{
			name:     "Linux modern",
			data:     types.FingerprintData{Type: "tcp_stack", Payload: TCPPayload{TTL: 64, TCPOptions: []string{"timestamps", "sack"}}},
			wantOS:   "Linux (modern)",
			wantConf: 0.75,
		},
		{
			name:     "Network device",
			data:     types.FingerprintData{Type: "tcp_stack", Payload: TCPPayload{TTL: 255}},
			wantOS:   "Network device (Cisco/Juniper)",
			wantConf: 0.9,
		},
		{
			name:     "Unknown",
			data:     types.FingerprintData{Type: "tcp_stack", Payload: TCPPayload{TTL: 100}},
			wantOS:   "unknown",
			wantConf: 0.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := strategy.Extract(context.Background(), tt.data)
			if err != nil {
				t.Fatalf("Extract() error = %v", err)
			}

			payload, ok := got.Data.Payload.(TCPOutputPayload)
			if !ok {
				t.Fatalf("got invalid payload type %T, want TCPOutputPayload", got.Data.Payload)
			}
			if payload.InferredOS != tt.wantOS {
				t.Errorf("got inferred_os %v, want %v", payload.InferredOS, tt.wantOS)
			}
			if got.Confidence != tt.wantConf {
				t.Errorf("got confidence %v, want %v", got.Confidence, tt.wantConf)
			}
		})
	}
}
