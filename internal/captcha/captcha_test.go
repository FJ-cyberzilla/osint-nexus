package captcha

import (
	"context"
	"errors"
	"testing"
)

type TestSolver struct {
	solveFunc func(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error)
}

func (ts *TestSolver) Solve(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
	return ts.solveFunc(ctx, challengeType, challengeData)
}

func TestChainedSolver_Solve(t *testing.T) {
	ctx := context.Background()
	challengeType := TypeTurnstile
	challengeData := []byte("challenge")

	t.Run("First solver succeeds", func(t *testing.T) {
		s1 := &TestSolver{
			solveFunc: func(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
				return "solution1", nil
			},
		}
		s2 := &TestSolver{
			solveFunc: func(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
				return "solution2", nil
			},
		}
		cs := NewChainedSolver(s1, s2)
		solution, err := cs.Solve(ctx, challengeType, challengeData)
		if err != nil {
			t.Fatalf("expected no error, got %v", err)
		}
		if solution != "solution1" {
			t.Fatalf("expected solution1, got %s", solution)
		}
	})

	t.Run("First solver fails, second succeeds", func(t *testing.T) {
		s1 := &TestSolver{
			solveFunc: func(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
				return "", errors.New("failed")
			},
		}
		s2 := &TestSolver{
			solveFunc: func(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
				return "solution2", nil
			},
		}
		cs := NewChainedSolver(s1, s2)
		solution, err := cs.Solve(ctx, challengeType, challengeData)
		if err != nil {
			t.Fatalf("expected no error, got %v", err)
		}
		if solution != "solution2" {
			t.Fatalf("expected solution2, got %s", solution)
		}
	})

	t.Run("All solvers fail", func(t *testing.T) {
		s1 := &TestSolver{
			solveFunc: func(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
				return "", errors.New("failed1")
			},
		}
		s2 := &TestSolver{
			solveFunc: func(ctx context.Context, challengeType ChallengeType, challengeData []byte) (string, error) {
				return "", errors.New("failed2")
			},
		}
		cs := NewChainedSolver(s1, s2)
		_, err := cs.Solve(ctx, challengeType, challengeData)
		if err == nil {
			t.Fatal("expected error, got nil")
		}
	})
}

func TestNoOpSolver(t *testing.T) {
	s := NewNoOpSolver()
	_, err := s.Solve(context.Background(), TypeReCaptchaV2, []byte("data"))
	if err == nil {
		t.Fatal("expected error from NoOpSolver, got nil")
	}
}

func TestOcrSolver(t *testing.T) {
	ctx := context.Background()

	t.Run("Missing API key", func(t *testing.T) {
		s := NewOcrSolver("")
		_, err := s.Solve(ctx, TypeReCaptchaV2, []byte("data"))
		if err == nil {
			t.Fatal("expected error for missing API key, got nil")
		}
	})

	t.Run("Empty data", func(t *testing.T) {
		s := NewOcrSolver("api-key")
		_, err := s.Solve(ctx, TypeReCaptchaV2, nil)
		if err == nil {
			t.Fatal("expected error for empty data, got nil")
		}
	})

	t.Run("Valid request", func(t *testing.T) {
		s := NewOcrSolver("api-key")
		res, err := s.Solve(ctx, TypeReCaptchaV2, []byte("data"))
		if err != nil {
			t.Fatalf("expected no error, got %v", err)
		}
		if res != "SIMULATED_OCR_SOLUTION" {
			t.Fatalf("expected SIMULATED_OCR_SOLUTION, got %s", res)
		}
	})
}
