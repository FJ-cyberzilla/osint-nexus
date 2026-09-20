package types

import (
	"time"

	"github.com/google/uuid"
)

// TelemetryEvent represents a single telemetry event.
type TelemetryEvent struct {
	EventID   uuid.UUID
	SessionID uuid.UUID
	EventType string
	Payload   map[string]interface{}
	Timestamp time.Time
}
