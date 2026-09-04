package strategies

import (
	"context"
	"strings"

	"github.com/osint-nexus/internal/types"
)

// CDNPayload implements types.FingerprintPayload for CDN fingerprinting input.
type CDNPayload struct {
	ServerHeaders map[string]string `json:"server_headers"`
}

// PayloadType returns the payload type identifier.
func (p CDNPayload) PayloadType() string { return "cdn_input" }

// CDNOutputPayload implements types.FingerprintPayload for CDN fingerprinting output.
type CDNOutputPayload struct {
	CdnDetected bool   `json:"cdn_detected"`
	Provider    string `json:"provider"`
}

// PayloadType returns the payload type identifier.
func (p CDNOutputPayload) PayloadType() string { return "cdn_output" }

// CdnFingerprintStrategy identifies CDN presence based on HTTP headers.
type CdnFingerprintStrategy struct{}

// NewCdnFingerprintStrategy initializes a new CdnFingerprintStrategy.
func NewCdnFingerprintStrategy() *CdnFingerprintStrategy {
	return &CdnFingerprintStrategy{}
}

// Name returns the strategy identifier.
func (s *CdnFingerprintStrategy) Name() string {
	return "cdn_headers"
}

// Extract analyzes HTTP headers to detect CDN presence.
func (s *CdnFingerprintStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(CDNPayload)
	if !ok {
		return types.FingerprintResult{
			Name: s.Name(),
			Data: types.FingerprintData{
				Type:    "cdn_detection",
				Payload: CDNOutputPayload{CdnDetected: false, Provider: ""},
			},
			Confidence: 0.1,
		}, nil
	}

	// Identify common CDN headers
	cdnIdentified := false
	for k := range payload.ServerHeaders {
		lowerKey := strings.ToLower(k)
		if lowerKey == "cf-ray" || lowerKey == "x-amz-cf-id" || lowerKey == "x-cache" {
			cdnIdentified = true
			break
		}
	}

	confidence := 0.1
	if cdnIdentified {
		confidence = 0.75
	}

	serverHeader := ""
	for k, v := range payload.ServerHeaders {
		if strings.ToLower(k) == "server" {
			serverHeader = v
			break
		}
	}

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type:    "cdn_detection",
			Payload: CDNOutputPayload{CdnDetected: cdnIdentified, Provider: serverHeader},
		},
		Confidence: confidence,
	}, nil
}
