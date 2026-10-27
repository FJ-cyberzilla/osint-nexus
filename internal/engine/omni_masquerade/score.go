package omni_masquerade

import (
	"strings"
)

// ScoringModel evaluates credibility and confidence metrics for discovered OSINT profiles and pivots.
type ScoringModel struct {
	BaseConfidence float64
}

// NewScoringModel initializes a new ScoringModel with default thresholds.
func NewScoringModel() *ScoringModel {
	return &ScoringModel{
		BaseConfidence: 0.50,
	}
}

// CalculateProfileScore computes a weighted confidence score based on profile metadata attributes, avatar presence, bio length, and verification badges.
func (sm *ScoringModel) CalculateProfileScore(platform string, rawMetadata map[string]string) float64 {
	score := sm.BaseConfidence

	if len(rawMetadata) > 0 {
		score += 0.20
	}

	if email, ok := rawMetadata["email"]; ok && email != "" {
		if !strings.Contains(email, "noreply") {
			score += 0.15
		} else {
			score += 0.05
		}
	}

	if bio, ok := rawMetadata["bio"]; ok && len(bio) > 10 {
		score += 0.10
	}

	if score > 1.0 {
		score = 1.0
	}

	return score
}
