package osint

import (
	"context"
	"testing"
)

func TestNewAgent(t *testing.T) {
	tests := []struct {
		name     string
		username string
		wantErr  bool
	}{
		{"ValidUsername", "nexus_user", false},
		{"EmptyUsername", "", true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := NewAgent(tt.username)
			if (err != nil) != tt.wantErr {
				t.Errorf("NewAgent() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && got.Username != tt.username {
				t.Errorf("NewAgent() got = %v, want %v", got.Username, tt.username)
			}
		})
	}
}

func TestAgent_RunScan(t *testing.T) {
	a, _ := NewAgent("nexus_user")
	// Using nil for dependencies as we just want to verify the method signature and basic error handling
	_, err := a.RunScan(context.Background(), nil, nil, 0)
	if err == nil {
		t.Errorf("Agent.RunScan() expected error due to nil orchestrator, got nil")
	}
}
