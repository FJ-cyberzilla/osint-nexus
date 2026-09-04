package engine

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/osint-nexus/internal/types"
)

const (
	testTimeout = 100 * time.Millisecond
)

type MockProvider struct {
	name   string
	result *types.IdentityProfile
	err    error
	delay  time.Duration
}

func (m *MockProvider) Name() string { return m.name }
func (m *MockProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	if m.delay > 0 {
		select {
		case <-time.After(m.delay):
		case <-ctx.Done():
			return nil, ctx.Err()
		}
	}
	return m.result, m.err
}

type MockDetector struct {
	err error
}

func (m *MockDetector) Analyze(ctx context.Context, profiles []*types.IdentityProfile) (float64, error) {
	return 1.0, m.err
}

func TestRunScan(t *testing.T) {
	type testCase struct {
		name           string
		providers      []types.Provider
		detector       Detector
		timeout        time.Duration
		expectResults  int
		expectErrors   int
	}

	tests := []testCase{
		{
			name: "success with multiple providers",
			providers: []types.Provider{
				&MockProvider{name: "p1", result: &types.IdentityProfile{}},
				&MockProvider{name: "p2", result: &types.IdentityProfile{}},
			},
			detector:      &MockDetector{},
			timeout:       testTimeout,
			expectResults: 2,
			expectErrors:  0,
		},
		{
			name: "mixed success and failure",
			providers: []types.Provider{
				&MockProvider{name: "p1", result: &types.IdentityProfile{}},
				&MockProvider{name: "p2", err: errors.New("failed")},
			},
			detector:      &MockDetector{},
			timeout:       testTimeout,
			expectResults: 1,
			expectErrors:  1,
		},
		{
			name: "provider timeout",
			providers: []types.Provider{
				&MockProvider{name: "p1", delay: 200 * time.Millisecond},
			},
			detector:      &MockDetector{},
			timeout:       50 * time.Millisecond,
			expectResults: 0,
			expectErrors:  1,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			ctx := context.Background()
			orchestrator, err := NewOrchestrator(2, tc.detector)
			if err != nil {
				t.Fatalf("failed to create orchestrator: %v", err)
			}

			session := orchestrator.RunScan(ctx, "testuser", tc.providers, tc.timeout)

			results := make([]*types.IdentityProfile, 0)
			for res := range session.ResultChan {
				results = append(results, res)
			}

			errorsCount := 0
			for range session.ErrChan {
				errorsCount++
			}

			if len(results) != tc.expectResults {
				t.Errorf("expected %d results, got %d", tc.expectResults, len(results))
			}
			if errorsCount != tc.expectErrors {
				t.Errorf("expected %d errors, got %d", tc.expectErrors, errorsCount)
			}
		})
	}
}
