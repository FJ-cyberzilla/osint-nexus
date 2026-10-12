package network

import (
	"context"
	"testing"
)

func TestDoHClient_Resolve(t *testing.T) {
	c := &DoHClient{}
	_, err := c.Resolve(context.Background(), "google.com")
	if err == nil {
		t.Errorf("expected error for unresolved doh, got nil")
	}
}

func TestDoHClient_FallbackToStandard(t *testing.T) {
	c := &DoHClient{}
	ips, err := c.FallbackToStandard(context.Background(), "google.com")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ips) == 0 {
		t.Errorf("expected non-empty ips, got empty")
	}
}
