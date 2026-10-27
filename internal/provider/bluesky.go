package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// BlueskyProvider probes Bluesky profile existence.
type BlueskyProvider struct {
	client *http.Client
}

func NewBlueskyProvider() *BlueskyProvider {
	return &BlueskyProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewBlueskyProvider())
}

func (p *BlueskyProvider) Name() string {
	return "Bluesky"
}

func (p *BlueskyProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://bsky.app/profile/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "bluesky: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "bluesky: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Bluesky"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.95,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("bluesky: rate limit exceeded")
	}
	return nil, nil
}
