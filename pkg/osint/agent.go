package osint

import (
	"context"
	"time"

	"github.com/rotisserie/eris"

	"github.com/FJ-cyberzilla/osint-nexus/internal/engine"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// Agent represents the primary structure for OSINT reconnaissance operations.
type Agent struct {
	Username string
}

// NewAgent initializes a new OSINT reconnaissance agent.
func NewAgent(username string) (*Agent, error) {
	if username == "" {
		return nil, eris.New("osint: username cannot be empty")
	}
	return &Agent{
		Username: username,
	}, nil
}

// RunScan executes the reconnaissance process for the initialized target.
func (a *Agent) RunScan(ctx context.Context, orch *engine.Orchestrator, providers []types.Provider, timeout time.Duration) (*engine.ScanSession, error) {
	if orch == nil {
		return nil, eris.New("osint: orchestrator cannot be nil")
	}

	session := orch.RunScan(ctx, a.Username, providers, timeout)
	return session, nil
}
