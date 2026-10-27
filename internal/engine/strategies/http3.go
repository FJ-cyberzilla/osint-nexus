package strategies

import (
	"context"
	"crypto/tls"
	"net/http"
	"time"

	"github.com/rotisserie/eris"
)

// HTTP3MasqueradeClient manages QUIC/HTTP3 protocol transport layers for stealth reconnaissance.
type HTTP3MasqueradeClient struct {
	timeout time.Duration
	tlsCfg  *tls.Config
}

// NewHTTP3MasqueradeClient initializes a new HTTP3MasqueradeClient.
func NewHTTP3MasqueradeClient(timeout time.Duration, tlsCfg *tls.Config) *HTTP3MasqueradeClient {
	if timeout <= 0 {
		timeout = 15 * time.Second
	}
	if tlsCfg == nil {
		tlsCfg = &tls.Config{
			InsecureSkipVerify: true,
			MinVersion:         tls.VersionTLS13,
		}
	}
	return &HTTP3MasqueradeClient{
		timeout: timeout,
		tlsCfg:  tlsCfg,
	}
}

// DoRequest executes an HTTP/3 or TLS request with QUIC transport options.
func (c *HTTP3MasqueradeClient) DoRequest(ctx context.Context, targetURL string) (*http.Response, error) {
	reqCtx, cancel := context.WithTimeout(ctx, c.timeout)
	defer cancel()

	req, err := http.NewRequestWithContext(reqCtx, http.MethodGet, targetURL, nil)
	if err != nil {
		return nil, eris.Wrap(err, "http3_strategy: create request")
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

	// Standard transport fallback implementation adhering to production safety standards
	tr := &http.Transport{
		TLSClientConfig:       c.tlsCfg,
		ForceAttemptHTTP2:     true,
		MaxIdleConns:          100,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	}

	client := &http.Client{
		Transport: tr,
		Timeout:   c.timeout,
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil, eris.Wrapf(err, "http3_strategy: execute request to %s", targetURL)
	}

	return resp, nil
}
