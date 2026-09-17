package detector

import (
	"context"
	"crypto/tls"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
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
	assert.NoError(t, err)
	server.StartTLS()
	defer server.Close()

	// NewHTTP2Detector with a reasonable timeout
	metrics := telemetry.NewMetrics()
	detector := NewHTTP2Detector(time.Second*2, metrics)
	// Override the client to trust the server's certificate
	detector.client.Transport.(*http2.Transport).TLSClientConfig = server.Client().Transport.(*http.Transport).TLSClientConfig

	// Perform the probe
	result, err := detector.Probe(context.Background(), server.URL)
	assert.NoError(t, err)
	assert.NotNil(t, result)
	assert.Equal(t, server.URL, result.Target)
	assert.Equal(t, "HTTP/2", result.Protocol)
	assert.True(t, result.Supported)

	// Verify metrics
	snapshot := metrics.Snapshot()
	assert.Equal(t, uint64(1), snapshot.RequestsTotal)
	assert.Equal(t, uint64(1), snapshot.RequestsSuccess)
	assert.Equal(t, uint64(0), snapshot.RequestsFailed)
}
