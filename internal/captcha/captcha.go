package captcha

import (
	"context"
	"fmt"
)

// ChallengeType defines the supported CAPTCHA challenge types.
type ChallengeType string

const (
	TypeReCaptchaV2 ChallengeType = "recaptcha_v2"
	TypeReCaptchaV3 ChallengeType = "recaptcha_v3"
	TypeTurnstile   ChallengeType = "turnstile"
	TypeHCaptcha    ChallengeType = "hcaptcha"
)

// Solver defines the interface for CAPTCHA solving strategies.
type Solver interface {
	Solve(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error)
}

// SessionManager defines the interface for managing CAPTCHA-related sessions/cookies.
type SessionManager interface {
	GetValidSession(ctx context.Context, siteURL string) (map[string]string, error)
	StoreSession(ctx context.Context, siteURL string, session map[string]string) error
}

// ChainedSolver orchestrates multiple solvers, falling back from one to another if necessary.
type ChainedSolver struct {
	solvers []Solver
}

// NewChainedSolver initializes a new ChainedSolver with a prioritized list of solvers.
func NewChainedSolver(solvers ...Solver) *ChainedSolver {
	return &ChainedSolver{
		solvers: solvers,
	}
}

// Solve attempts to solve a CAPTCHA using the chained solvers.
func (cs *ChainedSolver) Solve(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
	var lastErr error
	for _, solver := range cs.solvers {
		solution, err := solver.Solve(ctx, challengeType, challengeData)
		if err == nil {
			return solution, nil
		}
		lastErr = fmt.Errorf("captcha: chained solver: %w", err)
	}
	return "", fmt.Errorf("captcha: all solvers failed: %w", lastErr)
}
