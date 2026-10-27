package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// TumblrProvider probes Tumblr profile existence.
type TumblrProvider struct {
	client *http.Client
}

func NewTumblrProvider() *TumblrProvider {
	return &TumblrProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewTumblrProvider())
}

func (p *TumblrProvider) Name() string {
	return "Tumblr"
}

func (p *TumblrProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://%s.tumblr.com", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "tumblr: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "tumblr: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Tumblr"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("tumblr: rate limit exceeded")
	}
	return nil, nil
}
