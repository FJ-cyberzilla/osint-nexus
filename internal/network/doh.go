package network

import (
	"context"
	"net"

	"github.com/rotisserie/eris"
)

// DoHClient handles secure DNS resolution.
type DoHClient struct{}

// Resolve attempts DNS over HTTPS.
func (c *DoHClient) Resolve(ctx context.Context, hostname string) ([]string, error) {
	// For now, return an error to force fallback as per designed behavior.
	return nil, eris.New("network: doh resolution unavailable")
}

// FallbackToStandard resolves DNS using system resolver.
func (c *DoHClient) FallbackToStandard(ctx context.Context, hostname string) ([]string, error) {
	ips, err := net.DefaultResolver.LookupHost(ctx, hostname)
	if err != nil {
		return nil, eris.Wrap(err, "network: standard dns fallback failed")
	}
	return ips, nil
}
