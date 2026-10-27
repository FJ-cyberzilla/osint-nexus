package network

import (
	"context"
	"testing"
	"time"
)

func TestWarmupNetwork_Offline(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	// Using an unreachable local port to test offline error reporting
	status, err := WarmupNetwork(ctx, "127.0.0.1:1")
	if err == nil {
		t.Error("Expected error for unreachable network check, got nil")
	}
	if status.Online {
		t.Error("Expected Online to be false")
	}
}
