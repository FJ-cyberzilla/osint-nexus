package types

import (
	"fmt"
)

type FactorType string

const (
	FactorTypeMultiplier FactorType = "multiplier"
	FactorTypeBonus      FactorType = "bonus"
)

type Factor struct {
	Name       string     `json:"name"`
	Value      float64    `json:"value"`
	FactorType FactorType `json:"factor_type"`
}

func NewFactor(name string, value float64, factorType FactorType) (*Factor, error) {
	if name == "" {
		return nil, fmt.Errorf("types: factor name must be a non-empty string")
	}
	if factorType != FactorTypeMultiplier && factorType != FactorTypeBonus {
		return nil, fmt.Errorf("types: factor type must be 'multiplier' or 'bonus'")
	}
	if factorType == FactorTypeMultiplier && (value < 0.0 || value > 1.0) {
		return nil, fmt.Errorf("types: multiplier '%s' must be between 0.0 and 1.0, got %f", name, value)
	}
	if factorType == FactorTypeBonus && value < 0.0 {
		return nil, fmt.Errorf("types: bonus '%s' must be non-negative, got %f", name, value)
	}

	return &Factor{
		Name:       name,
		Value:      value,
		FactorType: factorType,
	}, nil
}

type ConfidenceResult struct {
	Score    float64            `json:"score"`
	Category string             `json:"category"`
	Details  map[string]float64 `json:"details"`
}
