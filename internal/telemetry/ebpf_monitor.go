package telemetry

import (
	"context"
	"fmt"
)

// SocketTrafficEntry represents a record extracted from Android BPF maps.
type SocketTrafficEntry struct {
	UID       uint32
	GID       uint32
	BytesRx   uint64
	BytesTx   uint64
	RemoteIP  string
	RemotePort uint16
}

// EBPFMonitor defines the contract for reading and interpreting BPF maps.
type EBPFMonitor interface {
	// PollRecords reads the current state of tracked socket traffic.
	PollRecords(ctx context.Context) ([]SocketTrafficEntry, error)
}

// BPFMapNotFoundError is returned when the required BPF map path is inaccessible.
type BPFMapNotFoundError struct {
	Path string
}

func (e *BPFMapNotFoundError) Error() string {
	return fmt.Sprintf("telemetry: BPF map not found at %s", e.Path)
}
