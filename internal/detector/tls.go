package detector

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/detector/helper"
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
	host, _, err := net.SplitHostPort(address)
	if err != nil {
		return nil, eris.Wrapf(err, "detector: invalid address %q", address)
	}

	// Apply configured timeout to caller context if set
	if d.timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, d.timeout)
		defer cancel()
	}

	conn, err := helper.DialContextHelper(ctx, "tcp", address, d.timeout)
	if err != nil {
		return nil, eris.Wrap(err, "detector: tcp dial failed")
	}

	// tlsConn wraps conn; calling tlsConn.Close() closes the underlying conn automatically,
	// even if Handshake Context or Handshake fails.
	tlsConn := tls.Client(conn, &tls.Config{
		ServerName: host,
	})
	defer tlsConn.Close()

	if err := tlsConn.HandshakeContext(ctx); err != nil {
		return nil, eris.Wrap(err, "detector: tls handshake failed")
	}

	state := tlsConn.ConnectionState()

	return &TLSResult{
		CipherSuite: tls.CipherSuiteName(state.CipherSuite),
		Version:     state.Version,
		ServerName:  state.ServerName,
		JA3:         fmt.Sprintf("%d-%d", state.Version, state.CipherSuite),
		JA4:         "not_supported_by_std_crypto_tls",
	}, nil
}
