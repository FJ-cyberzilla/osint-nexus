package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

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
                return nil, fmt.Errorf("app: failed to get config: %w", err)
        }
        dbPath := cfg.Database.Path
        if err := os.MkdirAll(filepath.Dir(dbPath), 0755); err != nil {
                return nil, fmt.Errorf("app: failed to create db directory: %w", err)
        }
	engineDB, err := db.NewSQLiteEngine(dbPath)
	if err != nil {
		return nil, fmt.Errorf("app: failed to initialize db engine: %w", err)
	}

	if err := engineDB.EnsureSchema(); err != nil {
		engineDB.Close()
		return nil, fmt.Errorf("app: failed to ensure schema: %w", err)
	}

	resultRepo := db.NewResultRepository(engineDB)

	// Initialize FingerprintRepository
	repo, err := db.NewFingerprintRepository("data/fingerprints.json")
	if err != nil {
		engineDB.Close()
		return nil, fmt.Errorf("app: failed to initialize fingerprint repository: %w", err)
	}

	profileDetector := detector.NewProfileDetector()
	orchestrator, err := engine.NewOrchestrator(5, profileDetector)
	if err != nil {
		engineDB.Close()
		return nil, fmt.Errorf("app: failed to initialize orchestrator: %w", err)
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
func (a *NexusApp) Close() {
	if a.engineDB != nil {
		a.engineDB.Close()
	}
}

// RunScan executes the scan orchestrator for the given username.
func (a *NexusApp) RunScan(ctx context.Context, username string) (*engine.ScanSession, error) {
        return a.orchestrator.RunScan(ctx, username, a.providers, time.Duration(config.DefaultTimeoutSeconds)*time.Second), nil
}

// SaveResult persists scan results to the repository.
func (a *NexusApp) SaveResult(username, platform string) error {
	return a.resultRepo.Save(username, platform, true)
}
