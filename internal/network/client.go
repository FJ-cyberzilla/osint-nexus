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

// Resolver defines the contract for DNS resolution.
type Resolver interface {
	Resolve(ctx context.Context, hostname string) ([]string, error)
	FallbackToStandard(ctx context.Context, hostname string) ([]string, error)
}

// Handshaker defines the contract for TLS handshakes.
type Handshaker interface {
	Handshake(ctx context.Context, address string) (any, error)
	FallbackToStandard(ctx context.Context, address string) (any, error)
}

// DataSender defines the contract for data offloading.
type DataSender interface {
	Send(ctx context.Context, data []byte) error
}
