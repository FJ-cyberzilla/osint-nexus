package helper

import (
	"context"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// DialContextHelper is a wrapper around net.Dialer to ensure consistent probing practices.
func DialContextHelper(ctx context.Context, network, address string, timeout time.Duration) (net.Conn, error) {
	dialer := net.Dialer{
		Timeout: timeout,
	}
	conn, err := dialer.DialContext(ctx, network, address)
	if err != nil {
		return nil, eris.Wrapf(err, "helper: dial failed for %s://%s", network, address)
	}
	return conn, nil
}
