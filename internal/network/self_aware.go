package network

import (
	"context"
	"net"
	"time"

	"github.com/rotisserie/eris"
)

// NetworkStatus holds the result of a network self-awareness warmup/auto-check.
type NetworkStatus struct {
	Online       bool
	Latency      time.Duration
	ErrorMessage string
	CheckedAt    time.Time
}

// WarmupNetwork performs an automated connectivity auto-check (warmup) to verify internet availability.
// If offline or if network issues are present, it returns an explicit error with diagnostic context.
func WarmupNetwork(ctx context.Context, checkAddress string) (*NetworkStatus, error) {
	if checkAddress == "" {
		checkAddress = "8.8.8.1:53" // Default fallback check address (Google DNS or reliable IP)
	}

	start := time.Now()
	dialer := &net.Dialer{
		Timeout: 4 * time.Second,
	}

	conn, err := dialer.DialContext(ctx, "tcp", checkAddress)
	latency := time.Since(start)

	if err != nil {
		return &NetworkStatus{
			Online:       false,
			Latency:      latency,
			ErrorMessage: err.Error(),
			CheckedAt:    time.Now(),
		}, eris.Wrap(err, "network: self-aware warmup failed — network offline or isolated environment")
	}
	defer conn.Close()

	return &NetworkStatus{
		Online:       true,
		Latency:      latency,
		ErrorMessage: "",
		CheckedAt:    time.Now(),
	}, nil
}

// DetectHoneypot analyzes response body byte slices for known honeypot markers or canary tokens.
func DetectHoneypot(body []byte) bool {
	if len(body) == 0 {
		return false
	}
	content := string(body)
	honeypotSignatures := []string{
		"canary_token",
		"honeypot-detected",
		"trap_door_active",
		"spider_trap",
		"bot_detection_wall",
	}

	for _, sig := range honeypotSignatures {
		if stringContains(content, sig) {
			return true
		}
	}
	return false
}

func stringContains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 || searchString(s, substr))
}

func searchString(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

