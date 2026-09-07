package scoring

import (
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"testing"
)

func TestConfidenceCalculator_Calculate(t *testing.T) {
	cc := NewConfidenceCalculator()

	t.Run("Valid factors", func(t *testing.T) {
		f1, _ := types.NewFactor("f1", 0.8, types.FactorTypeMultiplier)
		f2, _ := types.NewFactor("f2", 0.1, types.FactorTypeBonus)
		factors := []types.Factor{*f1, *f2}

		result, err := cc.Calculate(factors)
		if err != nil {
			t.Fatalf("expected no error, got %v", err)
		}
		expectedScore := (1.0 * 0.8) + 0.1
		if result.Score != expectedScore {
			t.Fatalf("expected score %f, got %f", expectedScore, result.Score)
		}
	})

	t.Run("Empty factors", func(t *testing.T) {
		_, err := cc.Calculate([]types.Factor{})
		if err == nil {
			t.Fatal("expected error, got nil")
		}
	})
}
