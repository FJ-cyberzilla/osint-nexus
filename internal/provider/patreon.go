package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// PatreonProvider probes Patreon profile existence.
type PatreonProvider struct {
	client *http.Client
}

func NewPatreonProvider() *PatreonProvider {
	return &PatreonProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewPatreonProvider())
}

func (p *PatreonProvider) Name() string {
	return "Patreon"
}

func (p *PatreonProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://www.patreon.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "patreon: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "patreon: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Patreon"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("patreon: rate limit exceeded")
	}
	return nil, nil
}
