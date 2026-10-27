package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// PoppoLiveProvider probes Poppo Live profile existence.
type PoppoLiveProvider struct {
	client *http.Client
}

func NewPoppoLiveProvider() *PoppoLiveProvider {
	return &PoppoLiveProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewPoppoLiveProvider())
}

func (p *PoppoLiveProvider) Name() string {
	return "PoppoLive"
}

func (p *PoppoLiveProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://poppo.live/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "poppolive: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "poppolive: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "PoppoLive"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("poppolive: rate limit exceeded")
	}
	return nil, nil
}
