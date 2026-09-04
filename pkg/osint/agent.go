package osint

import (
	"context"
	"fmt"
)

// Agent defines the main interface for OSINT reconnaissance operations.
type Agent struct {
	Username string
}

// NewAgent initializes a new OSINT reconnaissance agent.
func NewAgent(username string) (*Agent, error) {
	if username == "" {
		return nil, fmt.Errorf("osint: username cannot be empty")
	}
	return &Agent{
		Username: username,
	}, nil
}

// RunScan executes the reconnaissance process for the initialized target.
func (a *Agent) RunScan(ctx context.Context) error {
	// TODO: Integrate orchestration logic here
	return fmt.Errorf("osint: RunScan not yet implemented")
}
