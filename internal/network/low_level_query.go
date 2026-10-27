package network

import (
	"context"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// LowLevelQueryEngine handles low-level network reconnaissance queries and probes with fallback.
type LowLevelQueryEngine struct {
	Timeout time.Duration
}

// NewLowLevelQueryEngine initializes a LowLevelQueryEngine with a given timeout.
func NewLowLevelQueryEngine(timeout time.Duration) *LowLevelQueryEngine {
	if timeout == 0 {
		timeout = 10 * time.Second
	}
	return &LowLevelQueryEngine{
		Timeout: timeout,
	}
}

// ProbeTCP performs a low-level TCP connection probe to verify host responsiveness.
func (e *LowLevelQueryEngine) ProbeTCP(ctx context.Context, address string) (bool, error) {
	dialer := &net.Dialer{
		Timeout: e.Timeout,
	}

	conn, err := dialer.DialContext(ctx, "tcp", address)
	if err != nil {
		// Fallback check or return wrapped error without panicking
		return false, eris.Wrapf(err, "network: low-level TCP probe failed for %s", address)
	}
	defer conn.Close()

	return true, nil
}

// ResolveLowLevel performs a low-level DNS query with system resolver fallback.
func (e *LowLevelQueryEngine) ResolveLowLevel(ctx context.Context, hostname string) ([]string, error) {
	resolver := &net.Resolver{}
	addrs, err := resolver.LookupHost(ctx, hostname)
	if err != nil {
		// Fallback to standard IP lookup or empty result
		ips, fallbackErr := net.LookupIP(hostname)
		if fallbackErr != nil {
			return nil, eris.Wrapf(err, "network: low-level DNS resolution failed (fallback also failed: %v)", fallbackErr)
		}
		var results []string
		for _, ip := range ips {
			results = append(results, ip.String())
		}
		return results, nil
	}

	return addrs, nil
}
