package network

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestTLSProxy_Handshake(t *testing.T) {
	p := &TLSProxy{}
	_, err := p.Handshake(context.Background(), "google.com:443")
	assert.Error(t, err, "expected error for unresolved tls handshake")
}

func TestTLSProxy_FallbackToStandard(t *testing.T) {
	addr := setupMockServer(t)
	p := &TLSProxy{}
	_, err := p.FallbackToStandard(context.Background(), addr)

	// Expect error because it's not a real TLS server, so handshake will fail.
	// But it shouldn't be a TCP dial failure.
	assert.Error(t, err)
	assert.NotContains(t, err.Error(), "tcp dial failed")
}
