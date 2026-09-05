package engine

import (
	"context"
	"testing"
)

func TestShadowTracker(t *testing.T) {
	tracker := NewShadowTracker()
	ctx := context.Background()

	// Test: Track and GetState
	tracker.Track(ctx, "entity1", "active")

	state, exists := tracker.GetState(ctx, "entity1")
	if !exists {
		t.Error("Expected entity1 to exist")
	}
	if state != "active" {
		t.Errorf("Expected 'active', got '%s'", state)
	}

	// Test: Get non-existent
	_, exists = tracker.GetState(ctx, "unknown")
	if exists {
		t.Error("Expected 'unknown' to not exist")
	}

	// Test: Update state
	tracker.Track(ctx, "entity1", "inactive")
	state, _ = tracker.GetState(ctx, "entity1")
	if state != "inactive" {
		t.Errorf("Expected 'inactive', got '%s'", state)
	}
}
