package engine

import (
	"context"
	"sync"
)

// ShadowTracker monitors ephemeral entity states.
type ShadowTracker struct {
	mu      sync.RWMutex
	shadows map[string]string // entityID -> ephemeralState
}

// NewShadowTracker initializes a new ShadowTracker.
func NewShadowTracker() *ShadowTracker {
	return &ShadowTracker{
		shadows: make(map[string]string),
	}
}

// Track updates or sets ephemeral state for an entity.
func (st *ShadowTracker) Track(ctx context.Context, entityID string, state string) {
	st.mu.Lock()
	defer st.mu.Unlock()
	st.shadows[entityID] = state
}

// GetState retrieves ephemeral state for an entity.
func (st *ShadowTracker) GetState(ctx context.Context, entityID string) (string, bool) {
	st.mu.RLock()
	defer st.mu.RUnlock()
	state, exists := st.shadows[entityID]
	return state, exists
}
