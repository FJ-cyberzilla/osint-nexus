package strategies

import (
	"context"

	"github.com/FJ-cyberzilla/osint-nexus/internal/db"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// TLSPayload implements types.FingerprintPayload for TLS fingerprinting input.
type TLSPayload struct {
	JA3Hash string `json:"ja3_hash"`
}

// PayloadType returns the payload type identifier.
func (p TLSPayload) PayloadType() string { return "tls_input" }

// TLSOutputPayload implements types.FingerprintPayload for TLS fingerprinting output.
type TLSOutputPayload struct {
	JA3Hash        string `json:"ja3_hash"`
	InferredDevice string `json:"inferred_device"`
}

// PayloadType returns the payload type identifier.
func (p TLSOutputPayload) PayloadType() string { return "tls_output" }

// TLSStrategy implements the FingerprintStrategy for TLS (JA3).
type TLSStrategy struct {
	repo *db.FingerprintRepository
}

// NewTLSStrategy initializes a new TLSStrategy with a given FingerprintRepository.
func NewTLSStrategy(repo *db.FingerprintRepository) *TLSStrategy {
	return &TLSStrategy{
		repo: repo,
	}
}

// Name returns the strategy name.
func (s *TLSStrategy) Name() string {
	return "tls_ja3"
}

// Extract performs JA3 fingerprinting.
func (s *TLSStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(TLSPayload)
	if !ok {
		return types.FingerprintResult{
			Name: s.Name(),
			Data: types.FingerprintData{
				Type:    "tls_ja3",
				Payload: TLSOutputPayload{JA3Hash: "unknown", InferredDevice: "unknown"},
			},
			Confidence: 0.0,
		}, nil
	}

	deviceInfo := s.repo.GetSignature("ja3", payload.JA3Hash)
	if deviceInfo == "" {
		deviceInfo = "unknown"
	}

	confidence := 0.10
	if deviceInfo != "unknown" {
		confidence = 0.90
	}

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type:    "tls_ja3",
			Payload: TLSOutputPayload{JA3Hash: payload.JA3Hash, InferredDevice: deviceInfo},
		},
		Confidence: confidence,
	}, nil
}
