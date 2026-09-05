package captcha

import (
	"context"
	"fmt"
)

// OcrSolver implements a solver that simulates OCR-based challenge extraction.
type OcrSolver struct {
	apiKey string
}

// NewOcrSolver initializes a new OcrSolver with the required service credentials.
func NewOcrSolver(apiKey string) *OcrSolver {
	return &OcrSolver{
		apiKey: apiKey,
	}
}

// Solve simulates an API call to an OCR service.
func (s *OcrSolver) Solve(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
	if s.apiKey == "" {
		return "", fmt.Errorf("captcha: OcrSolver: missing API key")
	}

	// Simulate the OCR processing logic
	if len(challengeData) == 0 {
		return "", fmt.Errorf("captcha: OcrSolver: challenge data is empty")
	}

	return "SIMULATED_OCR_SOLUTION", nil
}
