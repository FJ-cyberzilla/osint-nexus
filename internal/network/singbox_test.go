package network

import (
	"context"
	"testing"
	"time"
)

func TestSingBoxClient_Fallback(t *testing.T) {
	client := NewSingBoxClient("", 2*time.Second)
	// Testing fallback handshake against an invalid address should fail gracefully without panic
		_, err := client.Handshake(context.Background(), "127.0.0.1:1")
	if err == nil {
		t.Error("Expected error for unreachable address, got nil")
	}
}

func TestSingBoxClient_DialContext(t *testing.T) {
	client := NewSingBoxClient("http://127.0.0.1:8080", 2*time.Second)
	_, err := client.DialContext(context.Background(), "tcp", "127.0.0.1:1")
	if err == nil {
		t.Error("Expected error for unreachable address, got nil")
	}
}
