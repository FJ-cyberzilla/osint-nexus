package network

import (
	"context"
)

// Intermediator defines the contract for low-level network operations
// with built-in fallback capabilities.
type Intermediator interface {
	ResolveDNS(ctx context.Context, hostname string) ([]string, error)
	SecureTLSHandshake(ctx context.Context, address string) (any, error)
	OffloadData(ctx context.Context, data []byte) error
}
