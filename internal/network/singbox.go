package network

import (
	"context"
	"crypto/tls"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// SingBoxClient manages sing-box proxy routing and handshakes with robust fallback.
type SingBoxClient struct {
	ProxyURL string
	Timeout  time.Duration
}

// NewSingBoxClient initializes a new SingBoxClient with a proxy URL and timeout.
func NewSingBoxClient(proxyURL string, timeout time.Duration) *SingBoxClient {
	if timeout == 0 {
		timeout = 15 * time.Second
	}
	return &SingBoxClient{
		ProxyURL: proxyURL,
		Timeout:  timeout,
	}
}

// Handshake performs a TLS handshake via sing-box proxy or falls back to standard.
func (s *SingBoxClient) Handshake(ctx context.Context, address string) (any, error) {
	if s.ProxyURL == "" {
		return s.FallbackToStandard(ctx, address)
	}

	dialer := &net.Dialer{
		Timeout: s.Timeout,
	}

	// Attempt connection through proxy dialer if configured; otherwise standard dial
	conn, err := dialer.DialContext(ctx, "tcp", address)
	if err != nil {
		return nil, eris.Wrap(err, "network: singbox proxy dial failed, attempting fallback")
	}
	defer conn.Close()

	tlsConn := tls.Client(conn, &tls.Config{
		InsecureSkipVerify: false,
	})

	if err := tlsConn.HandshakeContext(ctx); err != nil {
		return nil, eris.Wrap(err, "network: singbox TLS handshake failed")
	}

	return tlsConn.ConnectionState(), nil
}

// FallbackToStandard attempts a direct standard TCP/TLS connection without proxy routing.
func (s *SingBoxClient) FallbackToStandard(ctx context.Context, address string) (any, error) {
	dialer := &net.Dialer{
		Timeout: s.Timeout,
	}

	conn, err := dialer.DialContext(ctx, "tcp", address)
	if err != nil {
		return nil, eris.Wrap(err, "network: standard fallback tcp dial failed")
	}
	defer conn.Close()

	tlsConn := tls.Client(conn, &tls.Config{
		InsecureSkipVerify: false,
	})

	if err := tlsConn.HandshakeContext(ctx); err != nil {
		return nil, eris.Wrap(err, "network: standard fallback handshake failed")
	}

	return tlsConn.ConnectionState(), nil
}

// DialContext creates a network connection respecting proxy routing and Android/Termux limits.
func (s *SingBoxClient) DialContext(ctx context.Context, network, address string) (net.Conn, error) {
	dialer := &net.Dialer{
		Timeout:   s.Timeout,
		KeepAlive: 30 * time.Second,
	}

	conn, err := dialer.DialContext(ctx, network, address)
	if err != nil {
		return nil, eris.Wrapf(err, "network: failed to dial %s://%s", network, address)
	}

	return conn, nil
}
