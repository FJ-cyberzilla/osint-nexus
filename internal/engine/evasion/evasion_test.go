package evasion

import (
	"testing"
)

func TestGetAllocatorOptions(t *testing.T) {
	opts := SpoofingOptions{
		UserAgents: []string{"test-agent"},
	}

	allocOpts := GetAllocatorOptions(opts)
	if len(allocOpts) == 0 {
		t.Fatal("expected options")
	}
}
