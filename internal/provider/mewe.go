package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// MeWeProvider probes MeWe profile existence.
type MeWeProvider struct {
	client *http.Client
}

func NewMeWeProvider() *MeWeProvider {
	return &MeWeProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewMeWeProvider())
}

func (p *MeWeProvider) Name() string {
	return "MeWe"
}

func (p *MeWeProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://mewe.com/i/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "mewe: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "mewe: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "MeWe"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("mewe: rate limit exceeded")
	}
	return nil, nil
}
