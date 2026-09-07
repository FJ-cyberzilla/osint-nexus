package main

import (
	"context"
	"os"
	"path/filepath"
	"time"

	"github.com/rotisserie/eris"

	"github.com/osint-nexus/internal/config"
	"github.com/osint-nexus/internal/db"
	"github.com/osint-nexus/internal/detector"
	"github.com/osint-nexus/internal/engine"
	"github.com/osint-nexus/internal/engine/strategies"
	"github.com/osint-nexus/internal/provider"
	"github.com/osint-nexus/internal/types"
)

// NexusApp encapsulates the dependencies and lifecycle of the Nexus application.
type NexusApp struct {
	engineDB       *db.SQLiteEngine
	resultRepo     *db.ResultRepository
	orchestrator   *engine.Orchestrator
	fpOrchestrator *engine.FingerprintOrchestrator
	providers      []types.Provider
}

// NewNexusApp initializes a fully configured NexusApp.
func NewNexusApp() (*NexusApp, error) {
	// Initialize DB
	cfg, err := config.Get()
	if err != nil {
		return nil, eris.Wrap(err, "app: failed to get config")
	}
	dbPath := cfg.Database.Path
	// Fix G301: Set directory permissions to 0750
	if err := os.MkdirAll(filepath.Dir(dbPath), 0750); err != nil {
		return nil, eris.Wrapf(err, "app: failed to create db directory at %s", filepath.Dir(dbPath))
	}
	engineDB, err := db.NewSQLiteEngine(dbPath)
	if err != nil {
		return nil, eris.Wrap(err, "app: failed to initialize db engine")
	}

	// Fix G104: Explicitly handle Close errors
	if err := engineDB.EnsureSchema(); err != nil {
		if closeErr := engineDB.Close(); closeErr != nil {
			return nil, eris.Wrapf(err, "app: failed to ensure schema (and failed to close db: %v)", closeErr)
		}
		return nil, eris.Wrap(err, "app: failed to ensure schema")
	}

	resultRepo := db.NewResultRepository(engineDB)

	// Initialize FingerprintRepository
	repo, err := db.NewFingerprintRepository("data/fingerprints.json")
	if err != nil {
		if closeErr := engineDB.Close(); closeErr != nil {
			return nil, eris.Wrapf(err, "app: failed to initialize fingerprint repository (and failed to close db: %v)", closeErr)
		}
		return nil, eris.Wrap(err, "app: failed to initialize fingerprint repository")
	}

	profileDetector := detector.NewProfileDetector()
	orchestrator, err := engine.NewOrchestrator(5, profileDetector)
	if err != nil {
		if closeErr := engineDB.Close(); closeErr != nil {
			return nil, eris.Wrapf(err, "app: failed to initialize orchestrator (and failed to close db: %v)", closeErr)
		}
		return nil, eris.Wrap(err, "app: failed to initialize orchestrator")
	}

	// Initialize FingerprintOrchestrator
	fpOrchestrator := engine.NewFingerprintOrchestrator(nil)
	fpOrchestrator.Register(strategies.NewCdnFingerprintStrategy())
	fpOrchestrator.Register(strategies.NewDnsFingerprintStrategy())
	fpOrchestrator.Register(strategies.NewExtensionFingerprintStrategy())
	fpOrchestrator.Register(strategies.NewHttpFingerprintStrategy())
	fpOrchestrator.Register(strategies.NewHttp2FingerprintStrategy())
	fpOrchestrator.Register(strategies.NewTCPStrategy())
	fpOrchestrator.Register(strategies.NewTimezoneFingerprintStrategy())
	fpOrchestrator.Register(strategies.NewTLSStrategy(repo))

	providers := []types.Provider{
		provider.NewRegistryProvider(),
		provider.NewTwitterProvider(),
		provider.NewInstagramProvider(),
	}

	return &NexusApp{
		engineDB:       engineDB,
		resultRepo:     resultRepo,
		orchestrator:   orchestrator,
		fpOrchestrator: fpOrchestrator,
		providers:      providers,
	}, nil
}

// Close gracefully closes application resources.
// Fix G104: Return error on Close
func (a *NexusApp) Close() error {
	if a.engineDB != nil {
		return a.engineDB.Close()
	}
	return nil
}

// RunScan executes the scan orchestrator for the given username.
func (a *NexusApp) RunScan(ctx context.Context, username string) (*engine.ScanSession, error) {
	return a.orchestrator.RunScan(ctx, username, a.providers, time.Duration(config.DefaultTimeoutSeconds)*time.Second), nil
}

// SaveResult persists scan results to the repository.
func (a *NexusApp) SaveResult(username, platform string) error {
	if err := a.resultRepo.Save(username, platform, true); err != nil {
		return eris.Wrap(err, "app: failed to save result")
	}
	return nil
}
