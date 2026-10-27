package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// RobloxProvider probes Roblox profile existence.
type RobloxProvider struct {
	client *http.Client
}

func NewRobloxProvider() *RobloxProvider {
	return &RobloxProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewRobloxProvider())
}

func (p *RobloxProvider) Name() string {
	return "Roblox"
}

func (p *RobloxProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://www.roblox.com/search/users?keyword=%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "roblox: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "roblox: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Roblox"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("roblox: rate limit exceeded")
	}
	return nil, nil
}
