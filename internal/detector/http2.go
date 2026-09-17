package detector

import (
	"context"
	"net/http"
	"time"

	"github.com/rotisserie/eris"
	"golang.org/x/net/http2"

	"github.com/FJ-cyberzilla/osint-nexus/internal/telemetry"
	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// HTTP2Detector performs HTTP/2 protocol probes on a target URL.
type HTTP2Detector struct {
	client  *http.Client
	metrics *telemetry.Metrics
}

// NewHTTP2Detector initializes and returns a configured HTTP2Detector.
func NewHTTP2Detector(timeout time.Duration, metrics *telemetry.Metrics) *HTTP2Detector {
	transport := &http2.Transport{
		AllowHTTP: true,
	}

	return &HTTP2Detector{
		client: &http.Client{
			Transport: transport,
			Timeout:   timeout,
		},
		metrics: metrics,
	}
}

// Probe checks if the target supports HTTP/2.
func (d *HTTP2Detector) Probe(ctx context.Context, targetURL string) (*types.ProbeResult, error) {
	d.metrics.RecordRequest()

	req, err := http.NewRequestWithContext(ctx, "GET", targetURL, nil)
	if err != nil {
		d.metrics.RecordFailure()
		return nil, eris.Wrap(err, "http2: create request")
	}

	resp, err := d.client.Do(req)
	if err != nil {
		d.metrics.RecordFailure()
		return nil, eris.Wrap(err, "http2: perform request")
	}
	defer resp.Body.Close()

	d.metrics.RecordSuccess()

	supported := resp.ProtoMajor == 2

	return &types.ProbeResult{
		Target:    targetURL,
		Protocol:  "HTTP/2",
		Supported: supported,
		Metadata: map[string]string{
			"proto": resp.Proto,
		},
	}, nil
}
