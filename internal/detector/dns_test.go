package detector

import (
	"context"
	"testing"
	"time"
)

func TestDNSDetector_Probe(t *testing.T) {
	// Use a public resolver for testing
	d := NewDNSDetector("8.8.8.8:53")
	
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
	defer cancel()

	// Test valid lookup
	res, err := d.Probe(ctx, "google.com")
	if err != nil {
		t.Fatalf("Probe failed: %v", err)
	}

	if len(res.Records) == 0 {
		t.Errorf("Expected records, got none")
	}

	// Test invalid lookup
	_, err = d.Probe(ctx, "nonexistent.example.com")
	if err == nil {
		t.Errorf("Expected error for nonexistent domain, got nil")
	}
}
