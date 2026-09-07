package strategies

import (
	"context"
	"fmt"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// TCPPayload implements types.FingerprintPayload for TCP fingerprinting.
type TCPPayload struct {
	TTL        int      `json:"ttl"`
	TCPOptions []string `json:"tcp_options"`
}

// PayloadType returns the payload type identifier.
func (p TCPPayload) PayloadType() string { return "tcp_stack" }

// TCPOutputPayload implements types.FingerprintPayload for TCP fingerprinting output.
type TCPOutputPayload struct {
	InferredOS string `json:"inferred_os"`
}

// PayloadType returns the payload type identifier.
func (p TCPOutputPayload) PayloadType() string { return "tcp_stack_output" }

// TCPStrategy implements the FingerprintStrategy for TCP/IP stack fingerprinting (TTL/Window/Options).
type TCPStrategy struct{}

// NewTCPStrategy initializes a new TCPStrategy.
func NewTCPStrategy() *TCPStrategy {
	return &TCPStrategy{}
}

// Name returns the strategy name.
func (s *TCPStrategy) Name() string {
	return "tcp_stack"
}

// Extract performs TCP fingerprinting based on TTL and Options.
func (s *TCPStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(TCPPayload)
	if !ok {
		return types.FingerprintResult{}, fmt.Errorf("tcp_strategy: invalid payload type: %T", data.Payload)
	}

	inferredOS, confidence := s.detectOS(payload.TTL, payload.TCPOptions)

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type:    "tcp_stack",
			Payload: TCPOutputPayload{InferredOS: inferredOS},
		},
		Confidence: confidence,
	}, nil
}

func (s *TCPStrategy) detectOS(ttl int, options []string) (string, float64) {
	switch ttl {
	case 128:
		return s.detectWindows(options)
	case 64:
		return s.detectLinuxMacOS(options)
	case 255:
		return "Network device (Cisco/Juniper)", 0.9
	default:
		return "unknown", 0.0
	}
}

func (s *TCPStrategy) detectWindows(options []string) (string, float64) {
	for _, opt := range options {
		if opt == "wscale" {
			return "Windows 10/11", 0.85
		}
	}
	return "Windows (older)", 0.7
}

func (s *TCPStrategy) detectLinuxMacOS(options []string) (string, float64) {
	hasTimestamps := false
	hasSack := false
	for _, opt := range options {
		if opt == "timestamps" {
			hasTimestamps = true
		}
		if opt == "sack" {
			hasSack = true
		}
	}

	if hasTimestamps && hasSack {
		return "Linux (modern)", 0.75
	} else if hasTimestamps {
		return "macOS/iOS", 0.7
	}
	return "Linux (older)", 0.5
}
