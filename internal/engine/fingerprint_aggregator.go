package engine

import (
	"sync"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// FingerprintAggregator handles the aggregation of various fingerprinting strategies.
type FingerprintAggregator struct {
	mu      sync.RWMutex
	weights map[string]float64
}

// NewFingerprintAggregator initializes a new FingerprintAggregator with default weights.
func NewFingerprintAggregator() *FingerprintAggregator {
	return &FingerprintAggregator{
		weights: map[string]float64{
			"tls_ja3":        0.4,
			"http_headers":   0.3,
			"tcp_stack":      0.2,
			"http2_3_stack":  0.1,
			"dns_patterns":   0.1,
			"timezone_ntp":   0.05,
			"extension_load": 0.05,
			"cdn_headers":    0.05,
		},
	}
}

// Aggregate calculates the final weighted confidence based on collected results.
func (fa *FingerprintAggregator) Aggregate(results []types.FingerprintResult) (map[string]types.FingerprintData, float64, error) {
	fa.mu.RLock()
	defer fa.mu.RUnlock()

	aggregatedData := make(map[string]types.FingerprintData)
	var totalWeightedConfidence float64
	var totalWeight float64

	for _, result := range results {
		aggregatedData[result.Name] = result.Data

		weight, ok := fa.weights[result.Name]
		if !ok {
			weight = 0.1 // Default weight
		}

		totalWeightedConfidence += result.Confidence * weight
		totalWeight += weight
	}

	finalConfidence := 0.0
	if totalWeight > 0 {
		finalConfidence = totalWeightedConfidence / totalWeight
	}

	return aggregatedData, finalConfidence, nil
}
