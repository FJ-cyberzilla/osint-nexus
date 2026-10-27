package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// HackerOneProvider probes HackerOne profile existence.
type HackerOneProvider struct {
	client *http.Client
}

func NewHackerOneProvider() *HackerOneProvider {
	return &HackerOneProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewHackerOneProvider())
}

func (p *HackerOneProvider) Name() string {
	return "HackerOne"
}

func (p *HackerOneProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://hackerone.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "hackerone: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "hackerone: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "HackerOne"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("hackerone: rate limit exceeded")
	}
	return nil, nil
}
