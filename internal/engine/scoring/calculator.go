package scoring

import (
	"fmt"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// ConfidenceCalculator computes the confidence score of an identification.
type ConfidenceCalculator struct{}

// NewConfidenceCalculator initializes a new ConfidenceCalculator.
func NewConfidenceCalculator() *ConfidenceCalculator {
	return &ConfidenceCalculator{}
}

// Calculate computes the confidence score based on the provided factors.
func (cc *ConfidenceCalculator) Calculate(factors []types.Factor) (*types.ConfidenceResult, error) {
	if len(factors) == 0 {
		return nil, fmt.Errorf("scoring: no factors provided")
	}

	score := 1.0
	details := make(map[string]float64)

	for _, factor := range factors {
		switch factor.FactorType {
		case types.FactorTypeMultiplier:
			score *= factor.Value
			details[factor.Name] = factor.Value
		case types.FactorTypeBonus:
			score += factor.Value
			details[factor.Name] = factor.Value
		default:
			return nil, fmt.Errorf("scoring: unknown factor type: %s", factor.FactorType)
		}
	}

	if score > 1.0 {
		score = 1.0
	}
	if score < 0.0 {
		score = 0.0
	}

	return &types.ConfidenceResult{
		Score:    score,
		Category: "N/A", // Categorization logic can be added later
		Details:  details,
	}, nil
}
