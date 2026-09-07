package detector

import (
	"context"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// FallbackPayload implements types.FingerprintPayload for fallback fingerprinting.
type FallbackPayload struct {
	Status string `json:"status"`
}

// PayloadType returns the payload type identifier.
func (p FallbackPayload) PayloadType() string { return "fallback" }

// FallbackEngine orchestrates multiple probes and provides fallback logic.
type FallbackEngine struct {
	primaryProbes []BrowserProbe
	fallbackProbe BrowserProbe
}

// NewFallbackEngine initializes a new FallbackEngine.
func NewFallbackEngine(primary []BrowserProbe, fallback BrowserProbe) *FallbackEngine {
	return &FallbackEngine{
		primaryProbes: primary,
		fallbackProbe: fallback,
	}
}

// Probe tries primary probes and falls back to the fallbackProbe on failure.
func (e *FallbackEngine) Probe(ctx context.Context, targetURL string) (types.FingerprintData, error) {
	var lastErr error
	for _, p := range e.primaryProbes {
		data, err := p.Probe(ctx, targetURL)
		if err == nil {
			return data, nil
		}
		lastErr = eris.Wrap(err, "probe failed")
	}

	// All primary probes failed, use fallback
	data, err := e.fallbackProbe.Probe(ctx, targetURL)
	if err != nil {
		return types.FingerprintData{}, eris.Wrapf(err, "all probes and fallback failed: %v", lastErr)
	}
	return data, nil
}

// DefaultFallback returns a static empty payload for resilience.
type DefaultFallback struct{}

// NewDefaultFallback creates a new DefaultFallback.
func NewDefaultFallback() *DefaultFallback {
	return &DefaultFallback{}
}

// Probe implements BrowserProbe for DefaultFallback.
func (d *DefaultFallback) Probe(ctx context.Context, targetURL string) (types.FingerprintData, error) {
	return types.FingerprintData{
		Type:    "fallback",
		Payload: FallbackPayload{Status: "default"},
	}, nil
}
