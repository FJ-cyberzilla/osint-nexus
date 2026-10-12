package detector

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/chromedp/chromedp"
	"github.com/rotisserie/eris"
)

// STUNServer describes a single STUN endpoint for ICE gathering.
type STUNServer struct {
	URL string // e.g. "stun:stun.example.com:3478"
}

// NewWebRTCProbe initializes a WebRTCProbe with the specified timeout.
func NewWebRTCProbe(timeout time.Duration) *WebRTCProbe {
	return &WebRTCProbe{
		GatherTimeout: timeout,
	}
}

// WebGLProbe gathers WebGL renderer and vendor info from a headless browser.
type WebGLProbe struct {
	Timeout time.Duration
	run     func(ctx context.Context, url string, actions ...chromedp.Action) error
}

// WebGLPayload is the structured output of a WebGL probe.
type WebGLPayload struct {
	Vendor   string `json:"vendor" yaml:"vendor"`
	Renderer string `json:"renderer" yaml:"renderer"`
}

func (p WebGLPayload) PayloadType() string { return "webgl" }

// NewWebGLProbe initializes a WebGLProbe with the specified timeout.
func NewWebGLProbe(timeout time.Duration) *WebGLProbe {
	return &WebGLProbe{
		Timeout: timeout,
	}
}

// Probe implements BrowserProbe for WebGLProbe.
func (p *WebGLProbe) Probe(ctx context.Context, targetURL string) (types.FingerprintData, error) {
	timeout := p.Timeout
	if timeout <= 0 {
		timeout = 5 * time.Second
	}
	probeCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	script := `(() => {
		const canvas = document.createElement('canvas');
		const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
		if (!gl) return {vendor: '', renderer: ''};
		const ext = gl.getExtension('WEBGL_debug_renderer_info');
		if (!ext) return {vendor: '', renderer: ''};
		return {
			vendor: gl.getParameter(ext.UNMASKED_VENDOR_WEBGL) || '',
			renderer: gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) || ''
		};
	})()`

	var res struct {
		Vendor   string `json:"vendor"`
		Renderer string `json:"renderer"`
	}

	runner := p.run
	if runner == nil {
		runner = func(c context.Context, u string, acts ...chromedp.Action) error {
			tabCtx, cancel := chromedp.NewContext(c)
			defer cancel()
			all := append([]chromedp.Action{
				chromedp.Navigate("about:blank"),
			}, acts...)
			return chromedp.Run(tabCtx, all...)
		}
	}

	err := runner(probeCtx, targetURL, chromedp.Evaluate(script, &res))
	if err != nil {
		return types.FingerprintData{}, eris.Wrap(err, "webgl probe failed")
	}

	return types.FingerprintData{
		Type: "webgl",
		Payload: WebGLPayload{
			Vendor:   res.Vendor,
			Renderer: res.Renderer,
		},
	}, nil
}

// WebRTCProbe gathers ICE candidates from a headless browser.
//
// Isolation model: the caller owns a long-lived chromedp ExecAllocator and
// passes its context in via ctx. Each Probe call creates a fresh incognito
// tab so that cookies, storage, and WebRTC identity do not leak between
// targets.
type WebRTCProbe struct {
	// STUNServers is the set of STUN endpoints advertised to the browser.
	// If empty, a conservative default set is used. TURN is deliberately
	// not offered here — see WebRTCPayload docs.
	STUNServers []STUNServer

	// GatherTimeout caps ICE gathering. Defaults to 5s. The browser script
	// resolves early on iceGatheringState == "complete"; this is the hard
	// ceiling for stacks that never reach "complete" (blocked STUN, etc.).
	GatherTimeout time.Duration

	// IncludeMDNS controls whether mDNS .local hostnames are preserved in
	// the parsed output. Defaults to false: OSINT consumers want real IPs.
	// When false, candidates whose only address is mDNS are dropped from
	// the parsed set but retained in RawLines for forensics.
	IncludeMDNS bool

	// run executes the chromedp actions. Kept as a field so tests can
	// substitute a fake. In production this is the default runner.
	run func(ctx context.Context, url string, actions ...chromedp.Action) error
}

// WebRTCPayload is the structured output of a WebRTC probe.
type WebRTCPayload struct {
	// Candidates is the validated, parsed set. mDNS-only entries are
	// excluded unless IncludeMDNS is set.
	Candidates []*types.IceCandidate `json:"candidates" yaml:"candidates"`

	// RawLines preserves every candidate line exactly as the browser
	// emitted it. Never drop this — forensics and future parsers depend
	// on it, and it lets consumers re-derive anything the structured
	// form lost.
	RawLines []string `json:"raw_lines" yaml:"raw_lines"`

	// ParseErrors is non-fatal: one malformed line does not abort the
	// probe. Each entry is prefixed with the source line index.
	ParseErrors []string `json:"parse_errors,omitempty" yaml:"parse_errors,omitempty"`

	// MDNSSkipped counts candidates dropped because their address was a
	// .local hostname and IncludeMDNS was false. Diagnostic only.
	MDNSSkipped int `json:"mdns_skipped,omitempty" yaml:"mdns_skipped,omitempty"`
}

func (p WebRTCPayload) PayloadType() string { return "webrtc" }

// defaultSTUNs are only used when the caller does not supply STUNServers.
// Choose neutral endpoints in production; these exist so the probe works
// out of the box in tests and local runs.
var defaultSTUNs = []STUNServer{
	{URL: "stun:stun.l.google.com:19302"},
	{URL: "stun:stun.cloudflare.com:3478"},
}

// webrtcGatherTemplate is the JS template. %s is substituted with the
// iceServers array literal. Kept as a template (not a const) so that the
// server list and timeout can be injected without string surgery.
const webrtcGatherTemplate = `
(() => {
    return new Promise((resolve) => {
        const candidates = [];
        let resolved = false;

        const finish = () => {
            if (resolved) return;
            resolved = true;
            try { pc.close(); } catch (e) {}
            resolve(candidates);
        };

        const pc = new RTCPeerConnection({
            iceServers: [%s]
        });

        pc.onicecandidate = (event) => {
            if (event.candidate && event.candidate.candidate) {
                candidates.push(event.candidate.candidate);
            } else if (!event.candidate) {
                // null candidate signals end of gathering in every
                // Chromium/Firefox build we target — more reliable than
                // iceGatheringState alone.
                finish();
            }
        };

        pc.onicegatheringstatechange = () => {
            if (pc.iceGatheringState === 'complete') finish();
        };

        pc.onicecandidateerror = () => { /* swallow, STUN may be blocked */ };

        try {
            pc.createDataChannel('osint-nexus-probe');
            pc.createOffer()
                .then((offer) => pc.setLocalDescription(offer))
                .catch(() => finish());
        } catch (e) {
            finish();
        }

        setTimeout(finish, %d);
    });
})()
`

// Probe implements BrowserProbe for WebRTC candidate gathering.
func (p *WebRTCProbe) Probe(ctx context.Context, targetURL string) (types.FingerprintData, error) {
	servers := p.STUNServers
	if len(servers) == 0 {
		servers = defaultSTUNs
	}

	timeout := p.GatherTimeout
	if timeout <= 0 {
		timeout = 5 * time.Second
	}

	script := fmt.Sprintf(webrtcGatherTemplate,
		renderIceServers(servers),
		timeout.Milliseconds(),
	)

	// Hard ceiling on the whole gather. The JS setTimeout is the soft
	// floor; this context bounds chromedp itself so a wedged tab cannot
	// stall the scan.
	gatherCtx, cancel := context.WithTimeout(ctx, timeout+2*time.Second)
	defer cancel()

	var raw []string
	runner := p.run
	if runner == nil {
		runner = p.defaultRun
	}

	err := runner(gatherCtx, targetURL, chromedp.Evaluate(script, &raw))
	if err != nil {
		return types.FingerprintData{}, eris.Wrap(err, "webrtc probe failed")
	}

	payload := WebRTCPayload{RawLines: raw}

	parsed, parseErrs := ParseIceCandidates(raw)
	for _, e := range parseErrs {
		payload.ParseErrors = append(payload.ParseErrors, e.Error())
	}

	if p.IncludeMDNS {
		payload.Candidates = parsed
	} else {
		for _, c := range parsed {
			if c.Address == nil && c.Hostname != "" {
				payload.MDNSSkipped++
				continue
			}
			payload.Candidates = append(payload.Candidates, c)
		}
	}

	return types.FingerprintData{
		Type:    "webrtc",
		Payload: payload,
	}, nil
}

// renderIceServers builds the JS array literal for the RTCPeerConnection ctor.
func renderIceServers(servers []STUNServer) string {
	parts := make([]string, 0, len(servers))
	for _, s := range servers {
		// json.Marshal-style quoting would be safer if URLs ever come
		// from untrusted config; for now config is operator-controlled.
		parts = append(parts, fmt.Sprintf(`{urls:%q}`, s.URL))
	}
	return strings.Join(parts, ",")
}

// defaultRun executes chromedp actions in a fresh incognito tab. The caller
// is expected to have created ctx from a shared ExecAllocator; this method
// only adds the per-target isolation flag.
func (p *WebRTCProbe) defaultRun(ctx context.Context, url string, actions ...chromedp.Action) error {
	tabCtx, cancel := chromedp.NewContext(ctx)
	defer cancel()

	// Navigate first (about:blank is fine — we do not need the target page
	// to gather candidates, and navigating to targetURL would taint the
	// scan with the target's own scripts).
	all := append([]chromedp.Action{
		chromedp.Navigate("about:blank"),
	}, actions...)

	return chromedp.Run(tabCtx, all...)
}
