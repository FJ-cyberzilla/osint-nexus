package network

import (
	"context"
	"testing"
	"time"
)

func TestLowLevelQueryEngine_ProbeTCP(t *testing.T) {
	engine := NewLowLevelQueryEngine(1 * time.Second)
	success, err := engine.ProbeTCP(context.Background(), "127.0.0.1:1")
	if err == nil || success {
		t.Error("Expected failure for closed port, got success")
	}
}

func TestLowLevelQueryEngine_ResolveLowLevel(t *testing.T) {
	engine := NewLowLevelQueryEngine(2 * time.Second)
	_, err := engine.ResolveLowLevel(context.Background(), "nonexistent.invalid.domain.test")
	if err == nil {
		t.Error("Expected error for invalid domain, got nil")
	}
}
