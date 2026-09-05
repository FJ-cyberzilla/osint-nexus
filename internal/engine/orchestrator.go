package engine

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/osint-nexus/internal/provider"
	"github.com/osint-nexus/internal/types"
)

// Detector interface for post-scan analysis.
type Detector interface {
	Analyze(ctx context.Context, profiles []*types.IdentityProfile) (float64, error)
}

// Orchestrator coordinates concurrent provider execution.
type Orchestrator struct {
	maxConcurrency int
	detector       Detector
}

// NewOrchestrator initializes an Orchestrator.
func NewOrchestrator(maxConcurrency int, detector Detector) (*Orchestrator, error) {
	if maxConcurrency <= 0 {
		return nil, fmt.Errorf("engine: maxConcurrency must be positive")
	}
	return &Orchestrator{
		maxConcurrency: maxConcurrency,
		detector:       detector,
	}, nil
}

// ScanState represents the current state of a scan.
type ScanState int

const (
	ScanStateInitiated ScanState = iota
	ScanStateRunning
	ScanStateCompleted
	ScanStateError
)

// ScanSession manages the lifecycle of a single scan.
type ScanSession struct {
	mu         sync.Mutex
	State      ScanState
	ResultChan <-chan *types.IdentityProfile
	ErrChan    <-chan error
	ProgressChan <-chan float64
}

// setState safely updates the scan state.
func (s *ScanSession) setState(state ScanState) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.State = state
}

// getState safely reads the scan state.
func (s *ScanSession) getState() ScanState {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.State
}

// RunScan executes a scan across multiple providers concurrently and returns a ScanSession.
func (o *Orchestrator) RunScan(ctx context.Context, username string, providers []types.Provider, timeout time.Duration) *ScanSession {
	if len(providers) == 0 {
		providers = provider.GetProviders()
	}

	resultChan := make(chan *types.IdentityProfile)
	errChan := make(chan error, len(providers))
	progressChan := make(chan float64)

	session := &ScanSession{
		State:        ScanStateInitiated,
		ResultChan:   resultChan,
		ErrChan:      errChan,
		ProgressChan: progressChan,
	}

	go func() {
		defer func() {
			close(resultChan)
			close(errChan)
			close(progressChan)
		}()
		session.setState(ScanStateRunning)
		var mu sync.Mutex
		results := make([]*types.IdentityProfile, 0, len(providers))

		// Semaphore to limit concurrency
		sem := make(chan struct{}, o.maxConcurrency)
		var wg sync.WaitGroup
		
		completed := 0
		var progressMu sync.Mutex

		for _, p := range providers {
			wg.Add(1)
			go func(p types.Provider) {
				defer wg.Done()

				sem <- struct{}{}
				defer func() { <-sem }()

				// Create a timeout-aware context
				scanCtx, cancel := context.WithTimeout(ctx, timeout)
				defer cancel()

				res, err := p.CheckUsername(scanCtx, username)
				
				// Update progress
				progressMu.Lock()
				completed++
				progressChan <- float64(completed) / float64(len(providers))
				progressMu.Unlock()

				if err != nil {
					session.setState(ScanStateError)
					errChan <- fmt.Errorf("engine: provider %s failed: %w", p.Name(), err)
					return
				}

				if res != nil {
					mu.Lock()
					results = append(results, res)
					mu.Unlock()
					resultChan <- res
				}
			}(p)
		}

		wg.Wait()

		if o.detector != nil {
			_, err := o.detector.Analyze(ctx, results)
			if err != nil {
				session.setState(ScanStateError)
				errChan <- fmt.Errorf("engine: post-scan analysis failed: %w", err)
			}
		}

		if session.getState() != ScanStateError {
			session.setState(ScanStateCompleted)
		}
	}()

	return session
}
