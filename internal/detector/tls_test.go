package detector

import (
	"context"
	"net"
	"testing"
	"time"
)

func TestTLSDetector_Probe(t *testing.T) {
	// Start a dummy TLS server
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer ln.Close()

	// This is tricky without a real TLS server, but we can test the connection logic
	// A real test would require a TLS listener. Given constraints,
	// let's test a known HTTPS endpoint if possible, or skip/mock if hard.
	// Let's try connecting to a known TLS site (google.com)
	
	d := NewTLSDetector(time.Second * 5)
	
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
	defer cancel()

	// Test against Google
	res, err := d.Probe(ctx, "google.com:443")
	if err != nil {
		t.Fatalf("Probe failed: %v", err)
	}

	if res.Version == 0 {
		t.Errorf("Expected valid TLS version, got 0")
	}
	
	if res.JA3 == "" || res.JA3 == "not_implemented" {
		t.Errorf("Expected valid JA3 fingerprint, got %s", res.JA3)
	}
}
