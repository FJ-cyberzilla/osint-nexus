package network

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestNetworkManager_ResolveDNS(t *testing.T) {
	nm := NewNetworkManager(nil)
	ctx := context.Background()

	// Should currently fail because doh is not implemented,
	// but should trigger the fallback mechanism (if standard DNS is available).
	_, err := nm.ResolveDNS(ctx, "google.com")

	// Based on implementation, it will attempt DoH (fails), then fallback to standard (should succeed).
	assert.NoError(t, err, "fallback to standard DNS should succeed")
}

func TestNetworkManager_SecureTLSHandshake(t *testing.T) {
	addr := setupMockServer(t)
	nm := NewNetworkManager(nil)
	ctx := context.Background()

	// Similarly, advanced TLS fails, fallback to standard should trigger.
	// We expect the fallback handshake to fail because the server is not a TLS server.
	_, err := nm.SecureTLSHandshake(ctx, addr)

	assert.Error(t, err, "fallback to standard TLS should return handshake error, not TCP error")
	assert.NotContains(t, err.Error(), "tcp dial failed")
}

func TestNetworkManager_OffloadData(t *testing.T) {
	nm := NewNetworkManager(nil)
	ctx := context.Background()

	err := nm.OffloadData(ctx, []byte("data"))
	assert.NoError(t, err, "offload data should succeed")
}

func TestNetworkManager_UpdateLinkedIP_NoConfig(t *testing.T) {
	nm := NewNetworkManager(nil)
	ctx := context.Background()

	err := nm.UpdateLinkedIP(ctx)
	assert.Error(t, err, "should error when no endpoints configured")
}
