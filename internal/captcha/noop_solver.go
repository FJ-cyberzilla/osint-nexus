package captcha

import (
	"context"
	"fmt"
)

// NoOpSolver provides a non-functional solver implementation for testing and development.
type NoOpSolver struct{}

// NewNoOpSolver creates a new NoOpSolver instance.
func NewNoOpSolver() *NoOpSolver {
	return &NoOpSolver{}
}

// Solve returns an error indicating that this solver is not functional, as it is designed for no-operation scenarios.
func (s *NoOpSolver) Solve(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
	return "", fmt.Errorf("captcha: NoOpSolver: cannot solve challenges, this is a no-operation implementation")
}
