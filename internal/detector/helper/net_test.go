package helper

import (
	"context"
	"net"
	"testing"
	"time"
)

func TestDialContextHelper_Success(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to start listener: %v", err)
	}
	defer listener.Close()

	addr := listener.Addr().String()

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	conn, err := DialContextHelper(ctx, "tcp", addr, 1*time.Second)
	if err != nil {
		t.Fatalf("expected nil error, got %v", err)
	}
	if conn == nil {
		t.Fatalf("expected valid connection, got nil")
	}
	defer conn.Close()
}

func TestDialContextHelper_Failure(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	// Use an unroutable IP address to force a timeout/failure
	_, err := DialContextHelper(ctx, "tcp", "10.255.255.1:80", 10*time.Millisecond)
	if err == nil {
		t.Fatalf("expected error dialing unroutable address, got nil")
	}
}
