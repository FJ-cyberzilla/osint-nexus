package engine

import (
	"context"
	"sync"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/db"
	"github.com/FJ-cyberzilla/osint-nexus/internal/ui"
	"github.com/google/uuid"
)

// SessionState tracks active device sessions.
type SessionState struct {
	SessionID  uuid.UUID
	ProfileID  uuid.UUID
	DeviceType string
	LastSeen   time.Time
}

// SessionTracker manages concurrent device state.
type SessionTracker struct {
	mu       sync.RWMutex
	sessions map[uuid.UUID]*SessionState
	repo     *db.ProfilingRepository
	ui       UIMessenger
}

// NewSessionTracker initializes a new tracker.
func NewSessionTracker(repo *db.ProfilingRepository, ui UIMessenger) *SessionTracker {
	return &SessionTracker{
		sessions: make(map[uuid.UUID]*SessionState),
		repo:     repo,
		ui:       ui,
	}
}

// UpdateSession updates or creates a session.
func (t *SessionTracker) UpdateSession(ctx context.Context, sessionID uuid.UUID, profileID uuid.UUID, deviceType string) error {
	t.mu.Lock()
	state, exists := t.sessions[sessionID]
	if !exists {
		state = &SessionState{
			SessionID:  sessionID,
			ProfileID:  profileID,
			DeviceType: deviceType,
		}
		t.sessions[sessionID] = state
	}
	state.LastSeen = time.Now()
	t.mu.Unlock()

	if t.ui != nil {
		t.ui.Send(ui.SessionMsg{
			SessionID:  state.SessionID.String(),
			ProfileID:  state.ProfileID.String(),
			DeviceType: state.DeviceType,
			LastSeen:   state.LastSeen,
		})
	}

	// Asynchronously persist could be implemented here or via a ticker.
	return nil
}

// GetSession retrieves a session state safely.
func (t *SessionTracker) GetSession(sessionID uuid.UUID) (*SessionState, bool) {
	t.mu.RLock()
	defer t.mu.RUnlock()
	state, exists := t.sessions[sessionID]
	return state, exists
}
