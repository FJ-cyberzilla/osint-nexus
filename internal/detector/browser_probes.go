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

// WebGLPayload is the structured output of a WebGL probe.
type WebGLPayload struct {
	Vendor   string `json:"vendor" yaml:"vendor"`
	Renderer string `json:"renderer" yaml:"renderer"`
}

func (p WebGLPayload) PayloadType() string { return "webgl" }

// WebGLProbe gathers WebGL renderer and vendor info from a headless browser.
type WebGLProbe struct {
	Timeout time.Duration
	run     func(ctx context.Context, url string) (WebGLPayloadResult, error)
}

type WebGLPayloadResult struct {
	Vendor   string `json:"vendor"`
	Renderer string `json:"renderer"`
}

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

	if p.run != nil {
		res, err := p.run(probeCtx, targetURL)
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

	tabCtx, cancel := chromedp.NewContext(probeCtx)
	defer cancel()

	if _, err := chromedp.Run(tabCtx, chromedp.Navigate("about:blank")); err != nil {
		return types.FingerprintData{}, eris.Wrap(err, "webgl probe failed to navigate")
	}

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

	res, err := chromedp.Run(tabCtx, chromedp.Evaluate[WebGLPayloadResult](script))
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
type WebRTCProbe struct {
	STUNServers   []STUNServer
	GatherTimeout time.Duration
	IncludeMDNS   bool
	run           func(ctx context.Context, url string) ([]string, error)
}

// WebRTCPayload is the structured output of a WebRTC probe.
type WebRTCPayload struct {
	Candidates  []*types.IceCandidate `json:"candidates" yaml:"candidates"`
	RawLines    []string              `json:"raw_lines" yaml:"raw_lines"`
	ParseErrors []string              `json:"parse_errors,omitempty" yaml:"parse_errors,omitempty"`
	MDNSSkipped int                   `json:"mdns_skipped,omitempty" yaml:"mdns_skipped,omitempty"`
}

func (p WebRTCPayload) PayloadType() string { return "webrtc" }

var defaultSTUNs = []STUNServer{
	{URL: "stun:stun.l.google.com:19302"},
	{URL: "stun:stun.cloudflare.com:3478"},
}

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
                finish();
            }
        };

        pc.onicegatheringstatechange = () => {
            if (pc.iceGatheringState === 'complete') finish();
        };

        pc.onicecandidateerror = () => {};

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

	gatherCtx, cancel := context.WithTimeout(ctx, timeout+2*time.Second)
	defer cancel()

	if p.run != nil {
		raw, err := p.run(gatherCtx, targetURL)
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

	tabCtx, cancel := chromedp.NewContext(gatherCtx)
	defer cancel()

	if _, err := chromedp.Run(tabCtx, chromedp.Navigate("about:blank")); err != nil {
		return types.FingerprintData{}, eris.Wrap(err, "webrtc probe failed to navigate")
	}

	raw, err := chromedp.Run(tabCtx, chromedp.Evaluate[[]string](script))
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

func renderIceServers(servers []STUNServer) string {
	parts := make([]string, 0, len(servers))
	for _, s := range servers {
		parts = append(parts, fmt.Sprintf(`{urls:%q}`, s.URL))
	}
	return strings.Join(parts, ",")
}
