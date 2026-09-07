package detector

import (
	"context"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// DNSResult holds the outcome of a DNS probe.
type DNSResult struct {
	Records  []string `json:"records"`
	Resolver string   `json:"resolver"`
	Latency  int64    `json:"latency_ms"`
}

// DNSDetector probes DNS configurations.
type DNSDetector struct {
	resolver *net.Resolver
}

// NewDNSDetector initializes a new DNSDetector with a specific resolver.
func NewDNSDetector(resolverAddr string) *DNSDetector {
	return &DNSDetector{
		resolver: &net.Resolver{
			PreferGo: true,
			Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
				d := net.Dialer{
					Timeout: time.Second * 5,
				}
				return d.DialContext(ctx, "udp", resolverAddr)
			},
		},
	}
}

// Probe performs a DNS lookup for the given hostname.
func (d *DNSDetector) Probe(ctx context.Context, hostname string) (*DNSResult, error) {
	start := time.Now()
	ips, err := d.resolver.LookupHost(ctx, hostname)
	if err != nil {
		return nil, eris.Wrap(err, "detector: dns lookup failed")
	}

	return &DNSResult{
		Records:  ips,
		Resolver: "configured",
		Latency:  time.Since(start).Milliseconds(),
	}, nil
}
