package dorking

import (
	"testing"
)

func TestSimpleDorker(t *testing.T) {
	d := NewSimpleDorker("base")

	query, err := d.Generate("example.com", "login")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	expected := "login site:example.com"
	if query != expected {
		t.Errorf("expected %s, got %s", expected, query)
	}
}
