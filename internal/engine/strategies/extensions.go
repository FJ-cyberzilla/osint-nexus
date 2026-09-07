package strategies

import (
	"context"
	"strings"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// ExtensionPayload implements types.FingerprintPayload for extension fingerprinting input.
type ExtensionPayload struct {
	DetectedExtensions []string `json:"detected_extensions"`
}

// PayloadType returns the payload type identifier.
func (p ExtensionPayload) PayloadType() string { return "extension_input" }

// ExtensionOutputPayload implements types.FingerprintPayload for extension fingerprinting output.
type ExtensionOutputPayload struct {
	ExtensionCount int  `json:"extension_count"`
	HasAdblocker   bool `json:"has_adblocker"`
}

// PayloadType returns the payload type identifier.
func (p ExtensionOutputPayload) PayloadType() string { return "extension_output" }

// ExtensionFingerprintStrategy identifies browser extension load signatures.
type ExtensionFingerprintStrategy struct{}

// NewExtensionFingerprintStrategy initializes a new ExtensionFingerprintStrategy.
func NewExtensionFingerprintStrategy() *ExtensionFingerprintStrategy {
	return &ExtensionFingerprintStrategy{}
}

// Name returns the strategy identifier.
func (s *ExtensionFingerprintStrategy) Name() string {
	return "extension_load"
}

// Extract analyzes detected extensions.
func (s *ExtensionFingerprintStrategy) Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error) {
	payload, ok := data.Payload.(ExtensionPayload)
	if !ok {
		return types.FingerprintResult{
			Name: s.Name(),
			Data: types.FingerprintData{
				Type:    "extension_detection",
				Payload: ExtensionOutputPayload{ExtensionCount: 0, HasAdblocker: false},
			},
			Confidence: 0.2,
		}, nil
	}

	hasAdblocker := false
	for _, e := range payload.DetectedExtensions {
		lowerE := strings.ToLower(e)
		if strings.Contains(lowerE, "adblock") || strings.Contains(lowerE, "ublock") {
			hasAdblocker = true
			break
		}
	}

	confidence := 0.2
	if len(payload.DetectedExtensions) > 0 {
		confidence = 0.8
	}

	return types.FingerprintResult{
		Name: s.Name(),
		Data: types.FingerprintData{
			Type: "extension_detection",
			Payload: ExtensionOutputPayload{
				ExtensionCount: len(payload.DetectedExtensions),
				HasAdblocker:   hasAdblocker,
			},
		},
		Confidence: confidence,
	}, nil
}
