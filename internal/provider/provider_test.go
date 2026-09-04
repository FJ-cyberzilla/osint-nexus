package provider

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestPerformRequest(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("User-Agent") != "OSINT-Nexus/1.0" {
			t.Errorf("Expected User-Agent OSINT-Nexus/1.0, got %s", r.Header.Get("User-Agent"))
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	client := NewHTTPClient()
	resp, err := PerformRequest(context.Background(), client, server.URL)
	if err != nil {
		t.Fatalf("PerformRequest failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status OK, got %d", resp.StatusCode)
	}
}
