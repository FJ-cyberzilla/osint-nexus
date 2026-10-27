package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// SteamProvider probes Steam Community profile existence.
type SteamProvider struct {
	client *http.Client
}

func NewSteamProvider() *SteamProvider {
	return &SteamProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewSteamProvider())
}

func (p *SteamProvider) Name() string {
	return "Steam"
}

func (p *SteamProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://steamcommunity.com/id/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "steam: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "steam: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Steam"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("steam: rate limit exceeded")
	}
	return nil, nil
}
