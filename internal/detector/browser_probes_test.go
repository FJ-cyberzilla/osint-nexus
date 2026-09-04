package detector

import (
	"context"
	"os/exec"
	"testing"
	"time"
)

func TestBrowserProbes(t *testing.T) {
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
		if _, ok := data.Payload["vendor"]; !ok {
			t.Error("expected vendor in payload")
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
		if _, ok := data.Payload["ice_candidates"]; !ok {
			t.Error("expected ice_candidates in payload")
		}
	})
}
