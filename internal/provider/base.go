package provider

import (
	"context"
	"net/http"
	"time"
)

// DefaultTimeout for network operations.
const DefaultTimeout = 10 * time.Second

// FollowerProvider defines the contract for retrieving follower lists.
type FollowerProvider interface {
	GetFollowers(ctx context.Context, username string) ([]string, error)
}

// NewHTTPClient returns a configured http.Client with redirect handling.
func NewHTTPClient() *http.Client {
	return &http.Client{
		Timeout: DefaultTimeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) >= 5 {
				return http.ErrUseLastResponse
			}
			return nil
		},
	}
}

// PerformRequest executes an HTTP GET request with context and robust browser headers.
func PerformRequest(ctx context.Context, client *http.Client, url string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")

	return client.Do(req)
}
