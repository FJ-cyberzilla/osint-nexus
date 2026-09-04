package strategies

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestDnsFingerprintStrategy_Extract(t *testing.T) {
	strategy := &DnsFingerprintStrategy{}
	ctx := context.Background()

	t.Run("ValidData", func(t *testing.T) {
		data := types.FingerprintData{
			Type: "dns_patterns",
			Payload: DNSPayload{
				ResolverIP: "8.8.8.8",
				QueryTypes: []string{"A", "AAAA", "DNSSEC"},
			},
		}
		result, err := strategy.Extract(ctx, data)
		if err != nil {
			t.Fatalf("Extract failed: %v", err)
		}
		if result.Name != "dns_patterns" {
			t.Errorf("Expected dns_patterns, got %s", result.Name)
		}
		if result.Confidence != 0.6 {
			t.Errorf("Expected confidence 0.6, got %f", result.Confidence)
		}
		payload, ok := result.Data.Payload.(DNSOutputPayload)
		if !ok {
			t.Fatalf("Expected DNSOutputPayload, got %T", result.Data.Payload)
		}
		if payload.Resolver != "8.8.8.8" {
			t.Errorf("Expected resolver 8.8.8.8, got %v", payload.Resolver)
		}
		if payload.QueryTypeCount != 3 {
			t.Errorf("Expected query_type_count 3, got %v", payload.QueryTypeCount)
		}
		if payload.SupportsDNSSEC != true {
			t.Errorf("Expected supports_dnssec true, got %v", payload.SupportsDNSSEC)
		}
	})

	t.Run("MissingResolver", func(t *testing.T) {
		data := types.FingerprintData{
			Type: "dns_patterns",
			Payload: DNSPayload{
				QueryTypes: []string{"A"},
			},
		}
		result, _ := strategy.Extract(ctx, data)
		if result.Confidence != 0.1 {
			t.Errorf("Expected confidence 0.1, got %f", result.Confidence)
		}
		payload, ok := result.Data.Payload.(DNSOutputPayload)
		if !ok {
			t.Fatalf("Expected DNSOutputPayload, got %T", result.Data.Payload)
		}
		if payload.Resolver != "" {
			t.Errorf("Expected empty resolver, got %v", payload.Resolver)
		}
	})
}
