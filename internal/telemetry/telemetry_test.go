package telemetry

import (
	"context"
	"errors"
	"net"
	"testing"
	"time"
)

func TestMetrics(t *testing.T) {
	t.Run("Metrics record correctly", func(t *testing.T) {
		m := NewMetrics()
		m.RecordRequest()
		m.RecordSuccess()
		m.RecordRequest()
		m.RecordFailure()
		m.RecordBytes(1024)

		snapshot := m.Snapshot()

		if snapshot.RequestsTotal != 2 {
			t.Errorf("expected 2 total requests, got %d", snapshot.RequestsTotal)
		}
		if snapshot.RequestsSuccess != 1 {
			t.Errorf("expected 1 successful request, got %d", snapshot.RequestsSuccess)
		}
		if snapshot.RequestsFailed != 1 {
			t.Errorf("expected 1 failed request, got %d", snapshot.RequestsFailed)
		}
		if snapshot.BytesTransferred != 1024 {
			t.Errorf("expected 1024 bytes, got %d", snapshot.BytesTransferred)
		}
	})
}

func TestNetworkProbe(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to listen: %v", err)
	}
	defer ln.Close()

	target := ln.Addr().String()

	tests := []struct {
		name        string
		target      string
		timeout     time.Duration
		expectError bool
	}{
		{
			name:        "Successful probe",
			target:      target,
			timeout:     DefaultNetworkTimeout,
			expectError: false,
		},
		{
			name:        "Failed probe - connection refused",
			target:      "127.0.0.1:1",
			timeout:     100 * time.Millisecond,
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			probe := NewNetworkProbe(tt.target, tt.timeout)
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()

			err := probe.Check(ctx)
			if (err != nil) != tt.expectError {
				t.Errorf("expected error: %v, got: %v", tt.expectError, err)
			}
		})
	}
}

func TestReadinessProbe(t *testing.T) {
	tests := []struct {
		name        string
		checkFunc   func(ctx context.Context) error
		expectError bool
	}{
		{
			name: "Successful readiness",
			checkFunc: func(ctx context.Context) error {
				return nil
			},
			expectError: false,
		},
		{
			name: "Failed readiness",
			checkFunc: func(ctx context.Context) error {
				return errors.New("component not ready")
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			probe := NewReadinessProbe(tt.checkFunc)
			err := probe.Check(context.Background())
			if (err != nil) != tt.expectError {
				t.Errorf("expected error: %v, got: %v", tt.expectError, err)
			}
		})
	}
}
