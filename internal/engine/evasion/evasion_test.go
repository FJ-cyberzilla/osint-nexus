package evasion

import (
	"testing"
)

func TestGetAllocatorOptions(t *testing.T) {
	t.Run("with single agent", func(t *testing.T) {
		opts := SpoofingOptions{
			UserAgents: []string{"test-agent-1"},
		}
		allocOpts := GetAllocatorOptions(opts)
		if len(allocOpts) == 0 {
			t.Fatal("expected options, got none")
		}
	})

	t.Run("with empty agent list", func(t *testing.T) {
		opts := SpoofingOptions{
			UserAgents: []string{},
		}
		allocOpts := GetAllocatorOptions(opts)
		if len(allocOpts) == 0 {
			t.Fatal("expected default options, got none")
		}
	})

	t.Run("with multiple agents", func(t *testing.T) {
		opts := SpoofingOptions{
			UserAgents: []string{"test-agent-1", "test-agent-2", "test-agent-3"},
		}
		allocOpts := GetAllocatorOptions(opts)
		if len(allocOpts) == 0 {
			t.Fatal("expected options, got none")
		}
	})
}
