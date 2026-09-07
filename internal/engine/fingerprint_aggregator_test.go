package engine

import (
	"testing"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

type TestTLSPayload struct{ Hash string }

func (p TestTLSPayload) PayloadType() string { return "tls" }

type TestHTTPPayload struct{ Server string }

func (p TestHTTPPayload) PayloadType() string { return "http" }

func TestFingerprintAggregator_Aggregate(t *testing.T) {
	aggregator := NewFingerprintAggregator()

	results := []types.FingerprintResult{
		{
			Name: "tls_ja3",
			Data: types.FingerprintData{
				Type:    "tls",
				Payload: TestTLSPayload{Hash: "abc"},
			},
			Confidence: 0.9,
		},
		{
			Name: "http_headers",
			Data: types.FingerprintData{
				Type:    "http",
				Payload: TestHTTPPayload{Server: "nginx"},
			},
			Confidence: 0.8,
		},
	}

	data, confidence, err := aggregator.Aggregate(results)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}

	if len(data) != 2 {
		t.Errorf("expected 2 items, got %d", len(data))
	}

	if confidence <= 0 {
		t.Errorf("expected positive confidence, got %f", confidence)
	}
}
