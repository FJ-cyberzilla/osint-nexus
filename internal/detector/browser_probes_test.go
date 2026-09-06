package detector

import (
	"context"
	"os"
	"os/exec"
	"testing"
	"time"
)

func TestBrowserProbes(t *testing.T) {
	// Skip in Termux or CI environments to prevent crashes
	if os.Getenv("TERMUX_VERSION") != "" || os.Getenv("CI") != "" {
		t.Skip("skipping browser tests in restricted environment (Termux/CI)")
	}

	// Skip if no browser is available in the environment
	_, err := exec.LookPath("google-chrome")
	chromeErr := err
	_, err = exec.LookPath("chromium")
	chromiumErr := err
	if chromeErr != nil && chromiumErr != nil {
		t.Skip("skipping browser tests: no browser found in PATH")
	}

	ctx := context.Background()
	targetURL := "https://example.com"

	t.Run("WebGLProbe", func(t *testing.T) {
		probe := NewWebGLProbe(5 * time.Second)
		data, err := probe.Probe(ctx, targetURL)
		if err != nil {
			t.Fatalf("WebGLProbe failed: %v", err)
		}
		if data.Type != "webgl" {
			t.Errorf("expected type webgl, got %s", data.Type)
		}
		payload, ok := data.Payload.(WebGLPayload)
		if !ok {
			t.Fatal("expected WebGLPayload")
		}
		if payload.Vendor == "" {
			t.Error("expected non-empty vendor in payload")
		}
	})

	t.Run("WebRTCProbe", func(t *testing.T) {
		probe := NewWebRTCProbe(5 * time.Second)
		data, err := probe.Probe(ctx, targetURL)
		if err != nil {
			t.Fatalf("WebRTCProbe failed: %v", err)
		}
		if data.Type != "webrtc" {
			t.Errorf("expected type webrtc, got %s", data.Type)
		}
		payload, ok := data.Payload.(WebRTCPayload)
		if !ok {
			t.Fatal("expected WebRTCPayload")
		}
		if payload.IceCandidates == "" {
			t.Error("expected non-empty ice_candidates in payload")
		}
	})
}
