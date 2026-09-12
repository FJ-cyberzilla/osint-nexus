package network

import (
	"context"
	"crypto/tls"
	"net"

	"github.com/rotisserie/eris"
)

// TLSProxy handles advanced TLS handshakes.
type TLSProxy struct{}

// Handshake attempts an advanced TLS handshake.
func (t *TLSProxy) Handshake(ctx context.Context, address string) (any, error) {
	// For now, return an error to force fallback as per designed behavior.
	return nil, eris.New("network: advanced tls handshake unavailable")
}

// FallbackToStandard attempts a standard TLS handshake.
func (t *TLSProxy) FallbackToStandard(ctx context.Context, address string) (any, error) {
	conn, err := (&net.Dialer{}).DialContext(ctx, "tcp", address)
	if err != nil {
		return nil, eris.Wrap(err, "network: standard tls fallback tcp dial failed")
	}
	defer conn.Close()

	tlsConn := tls.Client(conn, &tls.Config{
		InsecureSkipVerify: true, // Example
	})

	if err := tlsConn.Handshake(); err != nil {
		return nil, eris.Wrap(err, "network: standard tls fallback handshake failed")
	}

	return tlsConn.ConnectionState(), nil
}
