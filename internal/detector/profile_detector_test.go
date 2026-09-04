package detector

import (
	"context"
	"testing"

	"github.com/osint-nexus/internal/types"
)

func TestProfileDetector_Analyze(t *testing.T) {
	detector := NewProfileDetector()

	tests := []struct {
		name          string
		profiles      []*types.IdentityProfile
		expectedScore float64
	}{
		{
			name:          "Empty profiles",
			profiles:      []*types.IdentityProfile{},
			expectedScore: 0.0,
		},
		{
			name: "Single profile",
			profiles: []*types.IdentityProfile{
				{Username: "user1"},
			},
			expectedScore: 0.2,
		},
		{
			name: "Max profiles",
			profiles: []*types.IdentityProfile{
				{Username: "u1"}, {Username: "u2"}, {Username: "u3"}, {Username: "u4"}, {Username: "u5"},
			},
			expectedScore: 1.0,
		},
		{
			name: "Exceeds max profiles",
			profiles: []*types.IdentityProfile{
				{Username: "u1"}, {Username: "u2"}, {Username: "u3"}, {Username: "u4"}, {Username: "u5"}, {Username: "u6"},
			},
			expectedScore: 1.0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			score, err := detector.Analyze(context.Background(), tt.profiles)
			if err != nil {
				t.Fatalf("Analyze returned unexpected error: %v", err)
			}
			if score != tt.expectedScore {
				t.Errorf("Expected score %f, got %f", tt.expectedScore, score)
			}
		})
	}
}
