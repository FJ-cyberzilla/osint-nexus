package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// OnlyFansProvider probes OnlyFans profile existence.
type OnlyFansProvider struct {
	client *http.Client
}

func NewOnlyFansProvider() *OnlyFansProvider {
	return &OnlyFansProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewOnlyFansProvider())
}

func (p *OnlyFansProvider) Name() string {
	return "OnlyFans"
}

func (p *OnlyFansProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://onlyfans.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "onlyfans: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "onlyfans: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "OnlyFans"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("onlyfans: rate limit exceeded")
	}
	return nil, nil
}
