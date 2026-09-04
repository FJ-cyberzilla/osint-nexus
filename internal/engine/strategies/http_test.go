package strategies

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestHttpFingerprintStrategy_Extract(t *testing.T) {
	strategy := NewHttpFingerprintStrategy()

	data := types.FingerprintData{
		Type: "http_headers",
		Payload: HTTPPayload{
			Headers: map[string]string{
				"Sec-CH-UA-Platform": "Windows",
				"Sec-CH-UA-Mobile":   "?1",
				"Sec-CH-UA-Arch":     "x86",
				"Accept-Language":    "en-US,en;q=0.9",
				"User-Agent":         "Mozilla/5.0",
			},
		},
	}

	got, err := strategy.Extract(context.Background(), data)
	if err != nil {
		t.Fatalf("Extract() error = %v", err)
	}

	payload, ok := got.Data.Payload.(HTTPOutputPayload)
	if !ok {
		t.Fatalf("Extract() got invalid payload type %T, want HTTPOutputPayload", got.Data.Payload)
	}
	
	if payload.Platform != "Windows" {
		t.Errorf("Extract() platform = %v, want Windows", payload.Platform)
	}
	if payload.Mobile != true {
		t.Errorf("Extract() mobile = %v, want true", payload.Mobile)
	}
	if payload.Architecture != "x86" {
		t.Errorf("Extract() architecture = %v, want x86", payload.Architecture)
	}
	if payload.Language != "en-US,en;q=0.9" {
		t.Errorf("Extract() language = %v, want en-US,en;q=0.9", payload.Language)
	}
	
	if len(payload.FullHeaders) != 3 {
		t.Errorf("Extract() full_headers length = %d, want 3", len(payload.FullHeaders))
	}
}
