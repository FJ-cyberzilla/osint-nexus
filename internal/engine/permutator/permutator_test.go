package permutator

import (
	"testing"
)

func TestSimplePermutator(t *testing.T) {
	p := NewSimplePermutator([]string{"-dev", "-stage"})
	
	results, err := p.Permute("example")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(results) != 2 {
		t.Errorf("expected 2 results, got %d", len(results))
	}
	
	if results[0] != "example-dev" || results[1] != "example-stage" {
		t.Errorf("unexpected results: %v", results)
	}
}
