package strategies

import (
	"context"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// DNSPayload implements types.FingerprintPayload for DNS fingerprinting input.
type DNSPayload struct {
	ResolverIP string   `json:"resolver_ip"`
	QueryTypes []string `json:"query_types"`
}

// PayloadType returns the payload type identifier.
func (p DNSPayload) PayloadType() string { return "dns_input" }

// DNSOutputPayload implements types.FingerprintPayload for DNS fingerprinting output.
type DNSOutputPayload struct {
	Resolver       string `json:"resolver"`
	QueryTypeCount int    `json:"query_type_count"`
	SupportsDNSSEC bool   `json:"supports_dnssec"`
}

// PayloadType returns the payload type identifier.
func (p DNSOutputPayload) PayloadType() string { return "dns_output" }

// DnsFingerprintStrategy implements FingerprintStrategy for DNS patterns.
type DnsFingerprintStrategy struct{}

// NewDnsFingerprintStrategy initializes a new DnsFingerprintStrategy.
func NewDnsFingerprintStrategy() *DnsFingerprintStrategy {
	return &DnsFingerprintStrategy{}
}

// Name returns the strategy name.
func (s *DnsFingerprintStrategy) Name() string {
	return "dns_patterns"
}

// Extract performs heuristic analysis on DNS data.
func (s *DnsFingerprintStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(DNSPayload)
	if !ok {
		return types.FingerprintResult{
			Name: s.Name(),
			Data: types.FingerprintData{
				Type:    "dns_patterns",
				Payload: DNSOutputPayload{},
			},
			Confidence: 0.1,
		}, nil
	}

	queryTypes := make(map[string]struct{})
	supportsDNSSEC := false
	for _, s := range payload.QueryTypes {
		queryTypes[s] = struct{}{}
		if s == "DNSSEC" {
			supportsDNSSEC = true
		}
	}

	confidence := 0.1
	if payload.ResolverIP != "" {
		confidence = 0.6
	}

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type: "dns_patterns",
			Payload: DNSOutputPayload{
				Resolver:       payload.ResolverIP,
				QueryTypeCount: len(queryTypes),
				SupportsDNSSEC: supportsDNSSEC,
			},
		},
		Confidence: confidence,
	}, nil
}
