package detector

import (
	"context"
	"net/http"
	"time"

	"github.com/rotisserie/eris"
)

// HTTPResult holds the outcome of an HTTP probe.
type HTTPResult struct {
	StatusCode int                 `json:"status_code"`
	Headers    map[string][]string `json:"headers"`
	Latency    int64               `json:"latency_ms"`
}

// HTTPDetector probes HTTP configurations.
type HTTPDetector struct {
	client *http.Client
}

// NewHTTPDetector initializes a new HTTPDetector.
func NewHTTPDetector(timeout time.Duration) *HTTPDetector {
	return &HTTPDetector{
		client: &http.Client{
			Timeout: timeout,
		},
	}
}

// Probe performs an HTTP GET request to extract headers and status.
func (d *HTTPDetector) Probe(ctx context.Context, url string) (*HTTPResult, error) {
	start := time.Now()
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "detector: http request creation failed")
	}

	resp, err := d.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "detector: http request execution failed")
	}
	defer resp.Body.Close()

	return &HTTPResult{
		StatusCode: resp.StatusCode,
		Headers:    resp.Header,
		Latency:    time.Since(start).Milliseconds(),
	}, nil
}
