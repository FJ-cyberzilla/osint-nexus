package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// HackerNewsProvider probes Hacker News profile existence.
type HackerNewsProvider struct {
	client *http.Client
}

func NewHackerNewsProvider() *HackerNewsProvider {
	return &HackerNewsProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewHackerNewsProvider())
}

func (p *HackerNewsProvider) Name() string {
	return "HackerNews"
}

func (p *HackerNewsProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://news.ycombinator.com/user?id=%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "hackernews: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "hackernews: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "HackerNews"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("hackernews: rate limit exceeded")
	}
	return nil, nil
}
