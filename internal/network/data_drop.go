package network

import (
	"context"
)

// DataDropService handles data ingestion.
type DataDropService struct{}

// Send sends data to the drop service.
func (d *DataDropService) Send(ctx context.Context, data []byte) error {
	// For now, return nil to simulate success.
	return nil
}
