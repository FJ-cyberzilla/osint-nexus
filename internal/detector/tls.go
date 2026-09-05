package detector

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"time"
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
		return nil, fmt.Errorf("detector: invalid address %q: %w", address, err)
	}

	conn, err := dialer.DialContext(ctx, "tcp", address)
	if err != nil {
		return nil, fmt.Errorf("detector: tcp dial failed: %w", err)
	}
	defer conn.Close()

	// Configure TLS client
	tlsConn := tls.Client(conn, &tls.Config{
		ServerName: host,
	})

	err = tlsConn.Handshake()
	if err != nil {
		return nil, fmt.Errorf("detector: tls handshake failed: %w", err)
	}
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
