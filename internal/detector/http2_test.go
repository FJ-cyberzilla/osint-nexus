package detector

import (
	"context"
	"crypto/tls"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"golang.org/x/net/http2"

	"github.com/FJ-cyberzilla/osint-nexus/internal/telemetry"
)

func TestHTTP2Detector_Probe(t *testing.T) {
	// Setup a mock server
	server := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	// Configure server for HTTP/2
	server.TLS = &tls.Config{
		NextProtos: []string{"h2", "http/1.1"},
	}
	err := http2.ConfigureServer(server.Config, &http2.Server{})
	if err != nil {
		t.Fatalf("unexpected error configuring server: %v", err)
	}
	server.StartTLS()
	defer server.Close()

	// NewHTTP2Detector with a reasonable timeout
	metrics := telemetry.NewMetrics()
	detector := NewHTTP2Detector(time.Second*2, metrics)
	// Override the client to trust the server's certificate
	detector.client.Transport.(*http2.Transport).TLSClientConfig = server.Client().Transport.(*http.Transport).TLSClientConfig

	// Perform the probe
	result, err := detector.Probe(context.Background(), server.URL)
	if err != nil {
		t.Fatalf("unexpected probe error: %v", err)
	}
	if result == nil {
		t.Fatalf("expected result, got nil")
	}
	if result.Target != server.URL {
		t.Errorf("expected target %s, got %s", server.URL, result.Target)
	}
	if result.Protocol != "HTTP/2" {
		t.Errorf("expected protocol HTTP/2, got %s", result.Protocol)
	}
	if !result.Supported {
		t.Errorf("expected supported true, got false")
	}

	// Verify metrics
	snapshot := metrics.Snapshot()
	if snapshot.RequestsTotal != 1 {
		t.Errorf("expected RequestsTotal 1, got %d", snapshot.RequestsTotal)
	}
	if snapshot.RequestsSuccess != 1 {
		t.Errorf("expected RequestsSuccess 1, got %d", snapshot.RequestsSuccess)
	}
	if snapshot.RequestsFailed != 0 {
		t.Errorf("expected RequestsFailed 0, got %d", snapshot.RequestsFailed)
	}
}
