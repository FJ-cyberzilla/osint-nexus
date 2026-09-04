package strategies

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestExtensionFingerprintStrategy_Extract(t *testing.T) {
	strategy := NewExtensionFingerprintStrategy()
	ctx := context.Background()

	tests := []struct {
		name           string
		data           types.FingerprintData
		wantCount      int
		wantAdblocker  bool
		wantConfidence float64
	}{
		{
			name: "With Adblocker",
			data: types.FingerprintData{
				Type: "extension_detection",
				Payload: ExtensionPayload{
					DetectedExtensions: []string{"uBlock Origin", "Privacy Badger"},
				},
			},
			wantCount:      2,
			wantAdblocker:  true,
			wantConfidence: 0.8,
		},
		{
			name: "Without Adblocker",
			data: types.FingerprintData{
				Type: "extension_detection",
				Payload: ExtensionPayload{
					DetectedExtensions: []string{"Grammarly"},
				},
			},
			wantCount:      1,
			wantAdblocker:  false,
			wantConfidence: 0.8,
		},
		{
			name: "No extensions",
			data: types.FingerprintData{
				Type: "extension_detection",
				Payload: ExtensionPayload{
					DetectedExtensions: []string{},
				},
			},
			wantCount:      0,
			wantAdblocker:  false,
			wantConfidence: 0.2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := strategy.Extract(ctx, tt.data)
			if err != nil {
				t.Fatalf("Extract() error = %v", err)
			}
			
			payload, ok := got.Data.Payload.(ExtensionOutputPayload)
			if !ok {
				t.Fatalf("Extract() got invalid payload type %T, want ExtensionOutputPayload", got.Data.Payload)
			}
			
			if payload.ExtensionCount != tt.wantCount {
				t.Errorf("Extract() count = %v, want %v", payload.ExtensionCount, tt.wantCount)
			}
			if payload.HasAdblocker != tt.wantAdblocker {
				t.Errorf("Extract() adblocker = %v, want %v", payload.HasAdblocker, tt.wantAdblocker)
			}
			if got.Confidence != tt.wantConfidence {
				t.Errorf("Extract() confidence = %v, want %v", got.Confidence, tt.wantConfidence)
			}
		})
	}
}
