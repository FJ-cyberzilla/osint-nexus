package osint

import (
	"context"
	"fmt"
	"time"

	"github.com/osint-nexus/internal/engine"
	"github.com/osint-nexus/internal/types"
)

// Agent represents the primary structure for OSINT reconnaissance operations.
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
func (a *Agent) RunScan(ctx context.Context, orch *engine.Orchestrator, providers []types.Provider, timeout time.Duration) (*engine.ScanSession, error) {
	if orch == nil {
		return nil, fmt.Errorf("osint: orchestrator cannot be nil")
	}

	session := orch.RunScan(ctx, a.Username, providers, timeout)
	return session, nil
}
