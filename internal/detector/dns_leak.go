package detector

import (
	"context"
	"net/http"

	"github.com/rotisserie/eris"
)

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
		client: &http.Client{},
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
		if err := resp.Body.Close(); err != nil {
			results = append(results, DNSLeakResult{URL: endpoint, IsLeaking: false, Error: eris.Wrap(err, "close response body").Error()})
			continue
		}

		// A successful reach indicates potential leak (if the endpoint is meant to test for it)
		results = append(results, DNSLeakResult{URL: endpoint, IsLeaking: resp.StatusCode == http.StatusOK})
	}

	return results, nil
}
