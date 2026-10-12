package network

import (
	"context"
	"strings"
	"testing"
)

func TestDataDropService_Send(t *testing.T) {
	s := &DataDropService{}
	err := s.Send(context.Background(), []byte("test data"))
	if err == nil {
		t.Fatalf("expected error, got nil")
	}
	if !strings.Contains(err.Error(), "not implemented") {
		t.Errorf("expected 'not implemented' error, got %v", err)
	}
}
