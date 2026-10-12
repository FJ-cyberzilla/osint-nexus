package telemetry

import (
	"errors"
	"testing"
)

func TestNewAndroidSocketTracer(t *testing.T) {
	// Scenario: Map path does not exist
	tracer, err := NewAndroidSocketTracer("/non/existent/path")
	if err == nil {
		t.Fatalf("expected error, got nil")
	}
	if tracer != nil {
		t.Fatalf("expected nil tracer, got %v", tracer)
	}
	var notFoundErr *BPFMapNotFoundError
	if !errors.As(err, &notFoundErr) {
		t.Errorf("expected BPFMapNotFoundError, got %T: %v", err, err)
	}
}
