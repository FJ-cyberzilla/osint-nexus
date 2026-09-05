package strategies

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestHttp2FingerprintStrategy_Extract(t *testing.T) {
	strategy := NewHttp2FingerprintStrategy()

	maxStreams := 200

	tests := []struct {
		name           string
		data           types.FingerprintData
		wantProtocol   string
		wantConfidence float64
	}{
		{
			name: "H2 protocol",
			data: types.FingerprintData{
				Type: "http2_3_detection",
				Payload: HTTP2Payload{
					ALPN: "h2",
					SettingsFrame: HTTP2Settings{
						MaxConcurrentStreams: &maxStreams,
					},
				},
			},
			wantProtocol:   "h2",
			wantConfidence: 0.7,
		},
		{
			name: "Unknown protocol",
			data: types.FingerprintData{
				Type: "http2_3_detection",
				Payload: HTTP2Payload{
					ALPN: "http/1.1",
				},
			},
			wantProtocol:   "http/1.1",
			wantConfidence: 0.2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := strategy.Extract(context.Background(), tt.data)
			if err != nil {
				t.Fatalf("Extract() error = %v", err)
			}
			payload, ok := got.Data.Payload.(HTTP2OutputPayload)
			if !ok {
				t.Fatalf("got invalid payload type %T, want HTTP2OutputPayload", got.Data.Payload)
			}
			if payload.Protocol != tt.wantProtocol {
				t.Errorf("Extract() protocol = %v, want %v", payload.Protocol, tt.wantProtocol)
			}
			if got.Confidence != tt.wantConfidence {
				t.Errorf("Extract() confidence = %v, want %v", got.Confidence, tt.wantConfidence)
			}
		})
	}
}
