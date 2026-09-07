package extractor

import (
	"context"
	"fmt"

	"github.com/osint-nexus/internal/types"
)

// PivotExtractor coordinates regex and HTML parsing engines.
// DEPRECATED: Use Orchestrator instead.
type PivotExtractor struct {
	orchestrator *Orchestrator
}

// NewPivotExtractor initializes and returns a fully configured PivotExtractor.
func NewPivotExtractor() (*PivotExtractor, error) {
	cfg := types.NewDefaultConfig()
	
	emailExt, err := NewEmailExtractor()
	if err != nil {
		return nil, fmt.Errorf("pivot_extractor: %w", err)
	}

	// PGP extraction is implemented via PGPExtractor for modular consistency.
	pgpExt, err := NewPGPExtractor()
	if err != nil {
		return nil, fmt.Errorf("pivot_extractor: %w", err)
	}

	socialExt := NewSocialExtractor(cfg)
	metaExt := NewMetaExtractor()

	return &PivotExtractor{
		orchestrator: NewOrchestrator(emailExt, pgpExt, socialExt, metaExt),
	}, nil
}

// Extract parses the HTML content and returns harvested pivots.
func (p *PivotExtractor) Extract(ctx context.Context, rawHTML string, sourceURL string) (*types.ExtractedPivots, error) {
	// sourceURL is currently ignored by the new granular extractors.
	// If needed, it must be passed into specific extractors that require it.
	return p.orchestrator.Extract(ctx, rawHTML)
}
