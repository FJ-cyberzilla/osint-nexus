package network

import (
	"context"

	"github.com/rotisserie/eris"
)

// DataDropService handles data ingestion.
type DataDropService struct{}

// Send sends data to the drop service.
func (d *DataDropService) Send(ctx context.Context, data []byte) error {
	return eris.New("network: data drop service not implemented")
}
