package detector

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// TLSResult holds the outcome of a TLS probe.
type TLSResult struct {
	CipherSuite string `json:"cipher_suite"`
	Version     uint16 `json:"version"`
	ServerName  string `json:"server_name"`
	JA3         string `json:"ja3"`
	JA4         string `json:"ja4"`
}

// TLSDetector probes TLS configurations.
type TLSDetector struct {
	timeout time.Duration
}

// NewTLSDetector initializes a new TLSDetector.
func NewTLSDetector(timeout time.Duration) *TLSDetector {
	return &TLSDetector{
		timeout: timeout,
	}
}

// Probe performs a TLS handshake to extract server configuration and a JA3-subset fingerprint.
func (d *TLSDetector) Probe(ctx context.Context, address string) (*TLSResult, error) {
	dialer := net.Dialer{
		Timeout: d.timeout,
	}

	host, _, err := net.SplitHostPort(address)
	if err != nil {
		return nil, eris.Wrapf(err, "detector: invalid address %q", address)
	}

	conn, err := dialer.DialContext(ctx, "tcp", address)
	if err != nil {
		return nil, eris.Wrap(err, "detector: tcp dial failed")
	}
	// We defer the closing of the connection.
	// Since tlsConn embeds conn, closing tlsConn closes conn.
	// However, if Handshake fails, we still need to close conn.
	// A simple approach is to use a flag or a closure to ensure it's closed.
	var closed bool
	defer func() {
		if !closed {
			conn.Close()
		}
	}()

	// Configure TLS client
	tlsConn := tls.Client(conn, &tls.Config{
		ServerName: host,
	})

	err = tlsConn.Handshake()
	if err != nil {
		return nil, eris.Wrap(err, "detector: tls handshake failed")
	}
	closed = true // Handshake took ownership of the connection

	defer tlsConn.Close()

	state := tlsConn.ConnectionState()

	// JA3-subset fingerprint: Version, CipherSuite
	ja3 := fmt.Sprintf("%d-%d", state.Version, state.CipherSuite)

	return &TLSResult{
		CipherSuite: tls.CipherSuiteName(state.CipherSuite),
		Version:     state.Version,
		ServerName:  state.ServerName,
		JA3:         ja3,
		JA4:         "not_supported_by_std_crypto_tls",
	}, nil
}
