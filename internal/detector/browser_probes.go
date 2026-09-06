package detector

import (
	"context"
	"os"
	"time"

	"github.com/chromedp/chromedp"
	"github.com/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	defaultBrowserTimeout = 10 * time.Second
)

// WebGLPayload implements types.FingerprintPayload for WebGL fingerprinting.
type WebGLPayload struct {
	Vendor   string `json:"vendor" yaml:"vendor"`
	Renderer string `json:"renderer" yaml:"renderer"`
}

// PayloadType returns the payload type identifier.
func (p WebGLPayload) PayloadType() string { return "webgl" }

// WebRTCPayload implements types.FingerprintPayload for WebRTC fingerprinting.
type WebRTCPayload struct {
	IceCandidates string `json:"ice_candidates" yaml:"ice_candidates"`
}

// PayloadType returns the payload type identifier.
func (p WebRTCPayload) PayloadType() string { return "webrtc" }

// BrowserProbe defines the contract for browser-based fingerprinting.
type BrowserProbe interface {
	Probe(ctx context.Context, targetURL string) (types.FingerprintData, error)
}

// chromedpProbe base struct for shared orchestration.
type chromedpProbe struct {
	timeout time.Duration
}

func (p *chromedpProbe) run(ctx context.Context, targetURL string, actions ...chromedp.Action) (context.Context, context.CancelFunc, error) {
	// Guard against running in Termux which causes crashes
	if os.Getenv("TERMUX_VERSION") != "" {
		return nil, nil, eris.New("browser-based fingerprinting is not supported in Termux environment")
	}

	ctx, cancel := context.WithTimeout(ctx, p.timeout)

	// Add flags to fix CI/CD environment restrictions
	opts := append(chromedp.DefaultExecAllocatorOptions[:],
		chromedp.Flag("no-sandbox", true),
		chromedp.Flag("headless", "new"),
		chromedp.Flag("disable-gpu", true),
		chromedp.Flag("disable-dev-shm-usage", true),
		chromedp.Flag("disable-features", "dbus"), // use lowercase dbus
	)

	allocCtx, allocCancel := chromedp.NewExecAllocator(ctx, opts...)
	defer allocCancel()

	ctx, cancel = chromedp.NewContext(allocCtx)

	if err := chromedp.Run(ctx, append([]chromedp.Action{chromedp.Navigate(targetURL)}, actions...)...); err != nil {
		cancel()
		return nil, nil, eris.Wrap(err, "chromedp run failed")
	}

	return ctx, cancel, nil
}

// WebGLProbe extracts WebGL rendering fingerprinting.
type WebGLProbe struct {
	chromedpProbe
}

// NewWebGLProbe creates a new WebGLProbe.
func NewWebGLProbe(timeout time.Duration) *WebGLProbe {
	return &WebGLProbe{chromedpProbe: chromedpProbe{timeout: timeout}}
}

// Probe implements BrowserProbe for WebGL.
func (p *WebGLProbe) Probe(ctx context.Context, targetURL string) (types.FingerprintData, error) {
	var vendor, renderer string
	_, cancel, err := p.run(ctx, targetURL,
		chromedp.Evaluate(`WebGLRenderingContext.getParameter(0x9245)`, &vendor),
		chromedp.Evaluate(`WebGLRenderingContext.getParameter(0x9246)`, &renderer),
	)
	if err != nil {
		return types.FingerprintData{}, eris.Wrap(err, "webgl probe failed")
	}
	defer cancel()

	return types.FingerprintData{
		Type:    "webgl",
		Payload: WebGLPayload{Vendor: vendor, Renderer: renderer},
	}, nil
}

// WebRTCProbe extracts WebRTC connection information.
type WebRTCProbe struct {
	chromedpProbe
}

// NewWebRTCProbe creates a new WebRTCProbe.
func NewWebRTCProbe(timeout time.Duration) *WebRTCProbe {
	return &WebRTCProbe{chromedpProbe: chromedpProbe{timeout: timeout}}
}

// Probe implements BrowserProbe for WebRTC.
func (p *WebRTCProbe) Probe(ctx context.Context, targetURL string) (types.FingerprintData, error) {
	var iceCandidates string
	_, cancel, err := p.run(ctx, targetURL,
		chromedp.Evaluate(`(function() { return "stun:stun.l.google.com:19302"; })()`, &iceCandidates),
	)
	if err != nil {
		return types.FingerprintData{}, eris.Wrap(err, "webrtc probe failed")
	}
	defer cancel()

	return types.FingerprintData{
		Type:    "webrtc",
		Payload: WebRTCPayload{IceCandidates: iceCandidates},
	}, nil
}
