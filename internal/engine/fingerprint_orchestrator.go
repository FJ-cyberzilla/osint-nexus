package engine

import (
	"context"
	"fmt"
	"sync"

	"github.com/osint-nexus/internal/engine/strategies"
	"github.com/osint-nexus/internal/types"
)

// FingerprintOrchestrator manages the execution of fingerprinting strategies.
type FingerprintOrchestrator struct {
	mu         sync.RWMutex
	strategies []strategies.FingerprintStrategy
}

// NewFingerprintOrchestrator creates a new orchestrator with the provided strategies.
func NewFingerprintOrchestrator(strats []strategies.FingerprintStrategy) *FingerprintOrchestrator {
	return &FingerprintOrchestrator{
		strategies: strats,
	}
}

// Register adds a new fingerprinting strategy to the orchestrator.
func (fo *FingerprintOrchestrator) Register(s strategies.FingerprintStrategy) {
	fo.mu.Lock()
	defer fo.mu.Unlock()
	fo.strategies = append(fo.strategies, s)
}

// Run executes all registered fingerprinting strategies concurrently.
func (fo *FingerprintOrchestrator) Run(ctx context.Context, data types.FingerprintData) ([]types.FingerprintResult, error) {
	fo.mu.RLock()
	strats := make([]strategies.FingerprintStrategy, len(fo.strategies))
	copy(strats, fo.strategies)
	fo.mu.RUnlock()

	results := make([]types.FingerprintResult, 0, len(strats))
	errChan := make(chan error, len(strats))
	resultChan := make(chan types.FingerprintResult, len(strats))
	var wg sync.WaitGroup

	for _, s := range strats {
		wg.Add(1)
		go func(strat strategies.FingerprintStrategy) {
			defer wg.Done()

			res, err := strat.Extract(ctx, data)
			if err != nil {
				errChan <- fmt.Errorf("engine: strategy %s failed: %w", strat.Name(), err)
				return
			}
			resultChan <- res
		}(s)
	}

	wg.Wait()
	close(resultChan)
	close(errChan)

	// Collect results
	for res := range resultChan {
		results = append(results, res)
	}
	
	if len(errChan) > 0 {
		return results, fmt.Errorf("engine: one or more strategies failed")
	}

	return results, nil
}
