package types

import (
	"testing"
)

func TestNewFactor(t *testing.T) {
	t.Run("Valid Multiplier", func(t *testing.T) {
		f, err := NewFactor("test", 0.5, FactorTypeMultiplier)
		if err != nil {
			t.Errorf("expected no error, got %v", err)
		}
		if f.Name != "test" || f.Value != 0.5 || f.FactorType != FactorTypeMultiplier {
			t.Error("factor not initialized correctly")
		}
	})

	t.Run("Valid Bonus", func(t *testing.T) {
		f, err := NewFactor("test", 10.0, FactorTypeBonus)
		if err != nil {
			t.Errorf("expected no error, got %v", err)
		}
		if f.Value != 10.0 || f.FactorType != FactorTypeBonus {
			t.Error("factor not initialized correctly")
		}
	})

	t.Run("Invalid Name", func(t *testing.T) {
		_, err := NewFactor("", 0.5, FactorTypeMultiplier)
		if err == nil {
			t.Error("expected error for empty name, got nil")
		}
	})

	t.Run("Invalid Factor Type", func(t *testing.T) {
		_, err := NewFactor("test", 0.5, "invalid")
		if err == nil {
			t.Error("expected error for invalid factor type, got nil")
		}
	})

	t.Run("Invalid Multiplier Value", func(t *testing.T) {
		_, err := NewFactor("test", 1.5, FactorTypeMultiplier)
		if err == nil {
			t.Error("expected error for multiplier > 1.0, got nil")
		}
		_, err = NewFactor("test", -0.1, FactorTypeMultiplier)
		if err == nil {
			t.Error("expected error for multiplier < 0.0, got nil")
		}
	})

	t.Run("Invalid Bonus Value", func(t *testing.T) {
		_, err := NewFactor("test", -1.0, FactorTypeBonus)
		if err == nil {
			t.Error("expected error for negative bonus, got nil")
		}
	})
}
