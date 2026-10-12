package network

import (
	"context"
	"strings"
	"testing"
)

func TestTLSProxy_Handshake(t *testing.T) {
	p := &TLSProxy{}
	_, err := p.Handshake(context.Background(), "google.com:443")
	if err == nil {
		t.Errorf("expected error for unresolved tls handshake, got nil")
	}
}

func TestTLSProxy_FallbackToStandard(t *testing.T) {
	addr := setupMockServer(t)
	p := &TLSProxy{}
	_, err := p.FallbackToStandard(context.Background(), addr)

	// Expect error because it's not a real TLS server, so handshake will fail.
	// But it shouldn't be a TCP dial failure.
	if err == nil {
		t.Fatalf("expected error, got nil")
	}
	if strings.Contains(err.Error(), "tcp dial failed") {
		t.Errorf("unexpected tcp dial failure: %v", err)
	}
}
