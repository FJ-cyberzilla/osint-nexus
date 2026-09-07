package extractor

import (
	"context"
	"fmt"
	"regexp"

	"github.com/osint-nexus/internal/types"
)

// PGPExtractor harvests PGP public keys from HTML content using regex.
type PGPExtractor struct {
	pgpRegex *regexp.Regexp
}

// NewPGPExtractor initializes and returns a fully configured PGPExtractor.
func NewPGPExtractor() (*PGPExtractor, error) {
	pgpPattern, err := regexp.Compile(`-----BEGIN PGP PUBLIC KEY BLOCK-----[\s\S]*?-----END PGP PUBLIC KEY BLOCK-----`)
	if err != nil {
		return nil, fmt.Errorf("pgp_extractor: compile pgp regex: %w", err)
	}

	return &PGPExtractor{
		pgpRegex: pgpPattern,
	}, nil
}

// Extract implements the Extractor interface for PGP keys.
func (p *PGPExtractor) Extract(ctx context.Context, rawHTML string) (*types.ExtractedPivots, error) {
	keys := p.pgpRegex.FindAllString(rawHTML, -1)

	return &types.ExtractedPivots{
		PGPKeys: keys,
	}, nil
}
