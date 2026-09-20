package engine

import (
	"context"
	"sync"
	"testing"

	"github.com/google/uuid"
)

func TestSessionTracker_UpdateSession(t *testing.T) {
	tracker := NewSessionTracker(nil, nil)
	ctx := context.Background()
	sessionID := uuid.New()
	profileID := uuid.New()
	deviceType := "test-device"

	err := tracker.UpdateSession(ctx, sessionID, profileID, deviceType)
	if err != nil {
		t.Fatalf("failed to update session: %v", err)
	}

	state, exists := tracker.GetSession(sessionID)
	if !exists {
		t.Fatal("session not found")
	}
	if state.ProfileID != profileID {
		t.Errorf("expected profileID %s, got %s", profileID, state.ProfileID)
	}
}

func TestSessionTracker_ConcurrentUpdates(t *testing.T) {
	tracker := NewSessionTracker(nil, nil)
	ctx := context.Background()
	sessionID := uuid.New()
	profileID := uuid.New()
	deviceType := "test-device"
	
	const numGoroutines = 100
	var wg sync.WaitGroup
	wg.Add(numGoroutines)

	for i := 0; i < numGoroutines; i++ {
		go func() {
			defer wg.Done()
			_ = tracker.UpdateSession(ctx, sessionID, profileID, deviceType)
		}()
	}
	wg.Wait()

	_, exists := tracker.GetSession(sessionID)
	if !exists {
		t.Fatal("session not found after concurrent updates")
	}
}
