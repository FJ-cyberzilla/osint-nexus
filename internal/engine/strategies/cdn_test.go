package strategies

import (
	"context"
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

func TestCdnFingerprintStrategy_Extract(t *testing.T) {
	strategy := NewCdnFingerprintStrategy()
	ctx := context.Background()

	tests := []struct {
		name           string
		data           types.FingerprintData
		wantCdn        bool
		wantConfidence float64
	}{
		{
			name: "CDN detected (cf-ray)",
			data: types.FingerprintData{
				Type: "cdn_detection",
				Payload: CDNPayload{
					ServerHeaders: map[string]string{
						"cf-ray": "some-value",
					},
				},
			},
			wantCdn:        true,
			wantConfidence: 0.75,
		},
		{
			name: "CDN detected (x-cache)",
			data: types.FingerprintData{
				Type: "cdn_detection",
				Payload: CDNPayload{
					ServerHeaders: map[string]string{
						"x-cache": "HIT",
					},
				},
			},
			wantCdn:        true,
			wantConfidence: 0.75,
		},
		{
			name: "No CDN detected",
			data: types.FingerprintData{
				Type: "cdn_detection",
				Payload: CDNPayload{
					ServerHeaders: map[string]string{
						"server": "nginx",
					},
				},
			},
			wantCdn:        false,
			wantConfidence: 0.1,
		},
		{
			name:           "Empty data",
			data:           types.FingerprintData{},
			wantCdn:        false,
			wantConfidence: 0.1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := strategy.Extract(ctx, tt.data)
			if err != nil {
				t.Fatalf("Extract() error = %v", err)
			}

			payload, ok := got.Data.Payload.(CDNOutputPayload)
			if !ok {
				t.Fatalf("Extract() got invalid payload type %T, want CDNOutputPayload", got.Data.Payload)
			}

			if payload.CdnDetected != tt.wantCdn {
				t.Errorf("Extract() cdn_detected = %v, want %v", payload.CdnDetected, tt.wantCdn)
			}
			if got.Confidence != tt.wantConfidence {
				t.Errorf("Extract() confidence = %v, want %v", got.Confidence, tt.wantConfidence)
			}
		})
	}
}
