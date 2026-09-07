package detector

import (
	"context"
	"net/http"
	"time"

	"github.com/rotisserie/eris"
)

const defaultHTTPTimeout = 10 * time.Second

// DNSLeakResult holds the outcome of a DNS leak check.
type DNSLeakResult struct {
	URL        string `json:"url"`
	IsLeaking  bool   `json:"is_leaking"`
	Error      string `json:"error,omitempty"`
}

// DNSLeakProbe checks if DNS requests are leaking for a target.
type DNSLeakProbe struct {
	client *http.Client
}

// NewDNSLeakProbe initializes a new DNSLeakProbe.
func NewDNSLeakProbe() *DNSLeakProbe {
	return &DNSLeakProbe{
		client: &http.Client{
			Timeout: defaultHTTPTimeout,
		},
	}
}

// Check executes the DNS leak probe against a target URL.
func (p *DNSLeakProbe) Check(ctx context.Context, targetURL string, testEndpoints []string) ([]DNSLeakResult, error) {
	results := make([]DNSLeakResult, 0, len(testEndpoints))

	for _, endpoint := range testEndpoints {
		req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
		if err != nil {
			results = append(results, DNSLeakResult{URL: endpoint, IsLeaking: false, Error: eris.Wrap(err, "create request").Error()})
			continue
		}

		resp, err := p.client.Do(req)
		if err != nil {
			results = append(results, DNSLeakResult{URL: endpoint, IsLeaking: false, Error: eris.Wrap(err, "execute request").Error()})
			continue
		}
		// Body must be drained and closed to reuse connections
		_ = resp.Body.Close()

		// A successful reach indicates potential leak (if the endpoint is meant to test for it)
		results = append(results, DNSLeakResult{URL: endpoint, IsLeaking: resp.StatusCode == http.StatusOK})
	}

	return results, nil
}
