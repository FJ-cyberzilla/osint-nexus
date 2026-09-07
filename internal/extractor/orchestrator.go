package extractor

import (
	"context"
	"fmt"

	"github.com/osint-nexus/internal/types"
)

// Orchestrator coordinates multiple extractors to harvest pivots.
type Orchestrator struct {
	extractors []types.Extractor
}

// NewOrchestrator creates a new orchestrator with the provided extractors.
func NewOrchestrator(extractors ...types.Extractor) *Orchestrator {
	return &Orchestrator{extractors: extractors}
}

// Extract runs all registered extractors and aggregates the results.
func (o *Orchestrator) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	result := &types.ExtractedPivots{
		Emails:        []string{},
		PGPKeys:       []string{}, // Note: PGP extraction needs a dedicated extractor if needed
		ExternalLinks: []string{},
		SocialHandles: []types.SocialHandle{},
	}

	for _, e := range o.extractors {
		pivots, err := e.Extract(ctx, rawHTML)
		if err != nil {
			return nil, fmt.Errorf("extractor_orchestrator: %w", err)
		}

		if pivots.Emails != nil {
			result.Emails = append(result.Emails, pivots.Emails...)
		}
		if pivots.PGPKeys != nil {
			result.PGPKeys = append(result.PGPKeys, pivots.PGPKeys...)
		}
		if pivots.ExternalLinks != nil {
			result.ExternalLinks = append(result.ExternalLinks, pivots.ExternalLinks...)
		}
		if pivots.SocialHandles != nil {
			result.SocialHandles = append(result.SocialHandles, pivots.SocialHandles...)
		}
		if pivots.Bio != nil && *pivots.Bio != "" {
			result.Bio = pivots.Bio
		}
	}

	return result, nil
}
