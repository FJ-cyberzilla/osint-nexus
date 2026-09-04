package strategies

import (
	"context"

	"github.com/osint-nexus/internal/types"
)

// FingerprintStrategy defines the contract for fingerprinting strategies.
type FingerprintStrategy interface {
	Name() string
	Extract(ctx context.Context, data types.FingerprintData) (types.FingerprintResult, error)
}
