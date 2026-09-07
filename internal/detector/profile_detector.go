package detector

import (
	"context"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// ProfileDetector analyzes found identity profiles to calculate a confidence score.
type ProfileDetector struct{}

// NewProfileDetector initializes a new ProfileDetector.
func NewProfileDetector() *ProfileDetector {
	return &ProfileDetector{}
}

// Analyze evaluates the identity profiles and returns a confidence score between 0.0 and 1.0.
func (d *ProfileDetector) Analyze(ctx context.Context, profiles []*types.IdentityProfile) (float64, error) {
	if len(profiles) == 0 {
		return 0.0, nil
	}

	// Simple heuristic: higher count of found profiles = higher confidence.
	// Assume 5 is maximum expected profiles for a typical OSINT scan.
	score := float64(len(profiles)) / 5.0
	if score > 1.0 {
		score = 1.0
	}

	return score, nil
}
