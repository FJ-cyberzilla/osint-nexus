package telemetry

import (
	"context"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// DefaultNetworkTimeout is the default duration for network probes.
const DefaultNetworkTimeout = 5 * time.Second

// Probe defines the interface for health checks.
type Probe interface {
	Check(ctx context.Context) error
}

// NetworkProbe checks if a specific target is reachable.
type NetworkProbe struct {
	target  string
	timeout time.Duration
}

// NewNetworkProbe creates a new NetworkProbe with the given target and timeout.
func NewNetworkProbe(target string, timeout time.Duration) *NetworkProbe {
	return &NetworkProbe{
		target:  target,
		timeout: timeout,
	}
}

// Check verifies the target is reachable by attempting a TCP dial.
func (np *NetworkProbe) Check(ctx context.Context) error {
	dialer := net.Dialer{
		Timeout: np.timeout,
	}

	conn, err := dialer.DialContext(ctx, "tcp", np.target)
	if err != nil {
		return eris.Wrapf(err, "telemetry: network probe to %s", np.target)
	}
	defer conn.Close()

	return nil
}

// ReadinessProbe checks if a component is ready.
type ReadinessProbe struct {
	checkFunc func(ctx context.Context) error
}

// NewReadinessProbe creates a new ReadinessProbe with the given check function.
func NewReadinessProbe(checkFunc func(ctx context.Context) error) *ReadinessProbe {
	return &ReadinessProbe{
		checkFunc: checkFunc,
	}
}

// Check executes the readiness check function.
func (rp *ReadinessProbe) Check(ctx context.Context) error {
	if err := rp.checkFunc(ctx); err != nil {
		return eris.Wrap(err, "telemetry: readiness probe")
	}
	return nil
}
