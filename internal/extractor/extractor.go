package extractor

import (
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// NewDefaultOrchestrator initializes a fully configured Orchestrator
// with all necessary extractors for a standard scan.
func NewDefaultOrchestrator() (*Orchestrator, error) {
	cfg := types.NewDefaultConfig()

	emailExt, err := NewEmailExtractor()
	if err != nil {
		return nil, err
	}

	pgpExt, err := NewPGPExtractor()
	if err != nil {
		return nil, err
	}

	socialExt := NewSocialExtractor(cfg)
	metaExt := NewMetaExtractor()

	return NewOrchestrator(emailExt, pgpExt, socialExt, metaExt), nil
}
