package detector

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestDNSLeakProbe_Check(t *testing.T) {
	// Create a mock server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	urls := []string{server.URL}
	probe := NewDNSLeakProbe()

	results, err := probe.Check(context.Background(), "http://test.com", urls)
	if err != nil {
		t.Fatalf("Check failed: %v", err)
	}

	if len(results) != 1 {
		t.Errorf("Expected 1 result, got %d", len(results))
	}
	
	if !results[0].IsLeaking {
		t.Errorf("Expected IsLeaking to be true, got false")
	}
}
