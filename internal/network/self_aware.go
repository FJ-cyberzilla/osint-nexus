package network

import (
	"context"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// NetworkStatus holds the result of a network self-awareness warmup/auto-check.
type NetworkStatus struct {
	Online       bool
	Latency      time.Duration
	ErrorMessage string
	CheckedAt    time.Time
}

// WarmupNetwork performs an automated connectivity auto-check (warmup) to verify internet availability.
// If offline or if network issues are present, it returns an explicit error with diagnostic context.
func WarmupNetwork(ctx context.Context, checkAddress string) (*NetworkStatus, error) {
	if checkAddress == "" {
		checkAddress = "8.8.8.1:53" // Default fallback check address (Google DNS or reliable IP)
	}

	start := time.Now()
	dialer := &net.Dialer{
		Timeout: 4 * time.Second,
	}

	conn, err := dialer.DialContext(ctx, "tcp", checkAddress)
	latency := time.Since(start)

	if err != nil {
		return &NetworkStatus{
			Online:       false,
			Latency:      latency,
			ErrorMessage: err.Error(),
			CheckedAt:    time.Now(),
		}, eris.Wrap(err, "network: self-aware warmup failed — network offline or isolated environment")
	}
	defer conn.Close()

	return &NetworkStatus{
		Online:       true,
		Latency:      latency,
		ErrorMessage: "",
		CheckedAt:    time.Now(),
	}, nil
}
