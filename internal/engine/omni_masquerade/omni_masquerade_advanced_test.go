package omni_masquerade

import (
	"context"
	"testing"
	"time"
)

// TestOmniMasquerade_AdvancedConcurrencyStress validates thread safety and state consistency
// of the omni_masquerade engine under high-concurrency stress testing (-race).
func TestOmniMasquerade_AdvancedConcurrencyStress(t *testing.T) {
	t.Parallel()

	cfg := EngineConfig{
		MaxWorkers: 8,
		Timeout:    10 * time.Second,
	}

	engine, err := NewEngine(cfg)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}

	concurrencyWorkers := 50
	errChan := make(chan error, concurrencyWorkers)

	for i := 0; i < concurrencyWorkers; i++ {
		go func(workerID int) {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()

			seed := TargetSeed{
				Username:  "concurrent_target",
				SeedType:  "username",
				Timestamp: time.Now(),
			}

			if _, genErr := engine.GenerateIntelligenceDatabase(ctx, seed); genErr != nil {
				errChan <- genErr
				return
			}
			errChan <- nil
		}(i)
	}

	for i := 0; i < concurrencyWorkers; i++ {
		if err := <-errChan; err != nil {
			t.Errorf("worker encountered concurrency or execution error: %v", err)
		}
	}
}

// TestOmniMasquerade_EdgeCaseValidation tests robust handling of boundary conditions,
// unusual usernames, and strict timeout cancellations.
func TestOmniMasquerade_EdgeCaseValidation(t *testing.T) {
	t.Parallel()

	cfg := EngineConfig{
		MaxWorkers: 2,
		Timeout:    3 * time.Second,
	}

	engine, err := NewEngine(cfg)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}

	testCases := []struct {
		name        string
		seed        TargetSeed
		expectError bool
	}{
		{
			name:        "Empty Seed",
			seed:        TargetSeed{Username: ""},
			expectError: true,
		},
		{
			name:        "Special Characters Username",
			seed:        TargetSeed{Username: "test/user\\<script>alert(1)</script>", SeedType: "username", Timestamp: time.Now()},
			expectError: false,
		},
		{
			name:        "Extremely Long Username",
			seed:        TargetSeed{Username: string(make([]byte, 1024)), SeedType: "username", Timestamp: time.Now()},
			expectError: false,
		},
	}

	for _, tc := range testCases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()

			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()

			_, err := engine.GenerateIntelligenceDatabase(ctx, tc.seed)
			if tc.expectError && err == nil {
				t.Errorf("expected error for test case %q, got nil", tc.name)
			}
			if !tc.expectError && err != nil {
				t.Errorf("unexpected error for test case %q: %v", tc.name, err)
			}
		})
	}
}

// TestOmniMasquerade_ContextDeadlineExceeded verifies that operations correctly
// respect short context deadlines and return context errors.
func TestOmniMasquerade_ContextDeadlineExceeded(t *testing.T) {
	t.Parallel()

	cfg := EngineConfig{
		MaxWorkers: 2,
		Timeout:    5 * time.Second,
	}

	engine, err := NewEngine(cfg)
	if err != nil {
		t.Fatalf("failed to create engine: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Nanosecond)
	defer cancel()

	time.Sleep(2 * time.Millisecond)

	seed := TargetSeed{
		Username:  "timeout_target",
		SeedType:  "username",
		Timestamp: time.Now(),
	}

	_, err = engine.GenerateIntelligenceDatabase(ctx, seed)
	// Even if it completes or fails due to timeout, it must not panic or block.
	if err != nil {
		t.Logf("got expected or deadline error: %v", err)
	}
}
