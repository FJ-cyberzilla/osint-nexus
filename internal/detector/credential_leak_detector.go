package detector

import (
	"context"
	"fmt"
	"regexp"

	"github.com/FJ-cyberzilla/osint-nexus/internal/telemetry"
)

// CredentialLeakDetector checks for leaked credentials associated with the target.
type CredentialLeakDetector struct {
	telemetry *telemetry.Metrics
	leakRegex *regexp.Regexp
}

// NewCredentialLeakDetector initializes a new CredentialLeakDetector.
func NewCredentialLeakDetector(metrics *telemetry.Metrics) (*CredentialLeakDetector, error) {
	// Regex to detect potential credential leaks in data
	leakPattern, err := regexp.Compile(`(?i)(password|secret|key|cred).*[:=]\s*[a-zA-Z0-9]+`)
	if err != nil {
		return nil, fmt.Errorf("detector: compile credential leak regex: %w", err)
	}

	return &CredentialLeakDetector{
		telemetry: metrics,
		leakRegex: leakPattern,
	}, nil
}

// Analyze scans the payload for potential credential leaks.
func (d *CredentialLeakDetector) Analyze(ctx context.Context, data string) (bool, error) {
	if d.leakRegex.MatchString(data) {
		if d.telemetry != nil {
			d.telemetry.RecordCredentialLeak()
		}
		return true, nil
	}
	return false, nil
}
