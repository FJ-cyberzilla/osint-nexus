package sanitizer

import (
	"testing"
)

func TestSanitizeUsername(t *testing.T) {
	tests := []struct {
		input    string
		expected string
		isValid  bool
	}{
		{"user123", "user123", true},
		{"user_123", "user_123", true},
		{" user123 ", "user123", true},
		{"user!@#", "", false},
		{"", "", false},
	}

	for _, tt := range tests {
		result, ok := SanitizeUsername(tt.input)
		if ok != tt.isValid || result != tt.expected {
			t.Errorf("SanitizeUsername(%q) = (%q, %v); want (%q, %v)", tt.input, result, ok, tt.expected, tt.isValid)
		}
	}
}
