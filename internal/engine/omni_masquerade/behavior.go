package omni_masquerade

import (
	"context"
	"math/rand"
	"time"

	"github.com/rotisserie/eris"
)

// BehaviorEmulator simulates human-like behavioral telemetry, non-linear request pacing, and cursor/typing delays.
type BehaviorEmulator struct {
	rng *rand.Rand
}

// NewBehaviorEmulator initializes a new BehaviorEmulator with a local pseudo-random source.
func NewBehaviorEmulator() *BehaviorEmulator {
	return &BehaviorEmulator{
		rng: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// JitterDelay introduces a non-linear, stochastically distributed delay between requests to avoid rate limiting and bot detection.
func (be *BehaviorEmulator) JitterDelay(ctx context.Context, baseDelay time.Duration) error {
	// Add Gaussian/Uniform jitter of +/- 40% around base delay
	jitterFactor := 0.6 + (be.rng.Float64() * 0.8)
	jitteredDuration := time.Duration(float64(baseDelay) * jitterFactor)

	select {
	case <-ctx.Done():
		return eris.Wrap(ctx.Err(), "behavior_emulator: jitter delay cancelled")
	case <-time.After(jitteredDuration):
		return nil
	}
}

// EmulateTypingDelay calculates realistic inter-key typing delays for form input automation.
func (be *BehaviorEmulator) EmulateTypingDelay(ctx context.Context) error {
	// Typing speed variance between 60ms and 180ms per keystroke
	ms := 60 + be.rng.Intn(120)
	delay := time.Duration(ms) * time.Millisecond

	select {
	case <-ctx.Done():
		return eris.Wrap(ctx.Err(), "behavior_emulator: typing delay cancelled")
	case <-time.After(delay):
		return nil
	}
}
