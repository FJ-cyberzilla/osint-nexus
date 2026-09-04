package types

import "context"

// Provider interface defines the contract for OSINT data collection.
type Provider interface {
	Name() string
	CheckUsername(ctx context.Context, username string) (*IdentityProfile, error)
}
