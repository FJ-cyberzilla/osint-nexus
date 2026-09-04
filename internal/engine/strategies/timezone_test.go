package strategies

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestTimezoneFingerprintStrategy_Extract(t *testing.T) {
	strategy := NewTimezoneFingerprintStrategy()
	ctx := context.Background()

	tests := []struct {
		name           string
		data           types.FingerprintData
		wantTz         string
		wantConfidence float64
	}{
		{
			name: "Timezone provided",
			data: types.FingerprintData{
				Payload: TimezonePayload{
					Timezone:      "UTC",
					OffsetSeconds: 0,
				},
			},
			wantTz:         "UTC",
			wantConfidence: 0.5,
		},
		{
			name: "Timezone missing",
			data: types.FingerprintData{
				Payload: TimezonePayload{},
			},
			wantTz:         "",
			wantConfidence: 0.1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := strategy.Extract(ctx, tt.data)
			if err != nil {
				t.Fatalf("Extract() error = %v", err)
			}
			payload, ok := got.Data.Payload.(TimezoneOutputPayload)
			if !ok {
				t.Fatalf("got invalid payload type %T, want TimezoneOutputPayload", got.Data.Payload)
			}
			if payload.Timezone != tt.wantTz {
				t.Errorf("Extract() timezone = %v, want %v", payload.Timezone, tt.wantTz)
			}
			if got.Confidence != tt.wantConfidence {
				t.Errorf("Extract() confidence = %v, want %v", got.Confidence, tt.wantConfidence)
			}
		})
	}
}
