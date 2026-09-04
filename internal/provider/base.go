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

// NewHTTPClient returns a configured http.Client.
func NewHTTPClient() *http.Client {
	return &http.Client{
		Timeout: DefaultTimeout,
	}
}

// PerformRequest executes an HTTP GET request with context.
func PerformRequest(ctx context.Context, client *http.Client, url string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	
	// Add user agent to avoid being blocked immediately
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	
	return client.Do(req)
}
