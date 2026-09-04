package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	_ "go.uber.org/automaxprocs"
	"github.com/osint-nexus/internal/db"
	"github.com/osint-nexus/internal/detector"
	"github.com/osint-nexus/internal/engine"
	"github.com/osint-nexus/internal/engine/strategies"
	"github.com/osint-nexus/internal/provider"
	"github.com/osint-nexus/internal/types"
)

func run() error {
	if len(os.Args) < 2 {
		return fmt.Errorf("usage: nexus <username>")
	}
	username := os.Args[1]

	ctx := context.Background()

	// Initialize DB
	engineDB, err := db.NewSQLiteEngine("nexus.db")
	if err != nil {
		return fmt.Errorf("failed to initialize db engine: %w", err)
	}
	defer engineDB.Close()

	if err := engineDB.EnsureSchema(); err != nil {
		return fmt.Errorf("failed to ensure schema: %w", err)
	}

	resultRepo := db.NewResultRepository(engineDB)

	// Initialize FingerprintRepository
	repo, err := db.NewFingerprintRepository("data/fingerprints.json")
	if err != nil {
		return fmt.Errorf("failed to initialize fingerprint repository: %w", err)
	}

	profileDetector := detector.NewProfileDetector()
	orchestrator, err := engine.NewOrchestrator(5, profileDetector)
	if err != nil {
		return fmt.Errorf("failed to initialize orchestrator: %w", err)
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

	fmt.Printf("Scanning for: %s\n", username)

	session := orchestrator.RunScan(ctx, username, providers, 5*time.Second)

	for {
		select {
		case res, ok := <-session.ResultChan:
			if !ok {
				session.ResultChan = nil
			} else {
				if res != nil {
					for _, acc := range res.Accounts {
						if acc.Username != nil && acc.Platform != nil {
							fmt.Printf("Found account: %s on %s\n", *acc.Username, *acc.Platform)
							if err := resultRepo.Save(*acc.Username, *acc.Platform, true); err != nil {
								fmt.Fprintf(os.Stderr, "Error saving result: %v\n", err)
							}
						}
					}
				}
			}
		case err, ok := <-session.ErrChan:
			if ok {
				fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			}
			session.ErrChan = nil
		}
		if session.ResultChan == nil && session.ErrChan == nil {
			break
		}
	}
	return nil
}

func main() {
	if err := run(); err != nil {
		log.Printf("Error: %v\n", err)
		os.Exit(1)
	}
}
