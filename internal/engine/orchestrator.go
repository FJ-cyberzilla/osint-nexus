package engine

import (
	"context"
	"sync"
	"sync/atomic"
	"time"

	"github.com/rotisserie/eris"

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
		return nil, eris.New("engine: maxConcurrency must be positive")
	}
	return &Orchestrator{
		maxConcurrency: maxConcurrency,
		detector:       detector,
	}, nil
}

// ScanState represents the current state of a scan.
type ScanState int32

const (
	ScanStateInitiated ScanState = iota
	ScanStateRunning
	ScanStateCompleted
	ScanStateError
)

// ScanSession manages the lifecycle of a single scan.
type ScanSession struct {
	State        atomic.Int32
	ResultChan   <-chan *types.IdentityProfile `json:"-" yaml:"-"`
	ErrChan      <-chan error                 `json:"-" yaml:"-"`
	ProgressChan <-chan float64               `json:"-" yaml:"-"`
}

// setState safely updates the scan state.
func (s *ScanSession) setState(state ScanState) {
	s.State.Store(int32(state))
}

// getState safely reads the scan state.
func (s *ScanSession) getState() ScanState {
	return ScanState(s.State.Load())
}

// RunScan executes a scan across multiple providers concurrently and returns a ScanSession.
func (o *Orchestrator) RunScan(ctx context.Context, username string, providers []types.Provider, timeout time.Duration) *ScanSession {
	if len(providers) == 0 {
		providers = provider.GetProviders()
	}

	resultChan := make(chan *types.IdentityProfile, len(providers))
	errChan := make(chan error, len(providers))
	progressChan := make(chan float64, len(providers))

	session := &ScanSession{
		ResultChan:   resultChan,
		ErrChan:      errChan,
		ProgressChan: progressChan,
	}
	session.setState(ScanStateInitiated)

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

		var completed atomic.Int64

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
				completed.Add(1)
				progressChan <- float64(completed.Load()) / float64(len(providers))

				if err != nil {
					session.setState(ScanStateError)
					errChan <- eris.Wrapf(err, "engine: provider %s failed", p.Name())
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
				errChan <- eris.Wrap(err, "engine: post-scan analysis failed")
			}
		}

		if session.getState() != ScanStateError {
			session.setState(ScanStateCompleted)
		}
	}()

	return session
}
