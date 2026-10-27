package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// BigoLiveProvider probes Bigo Live profile existence.
type BigoLiveProvider struct {
	client *http.Client
}

func NewBigoLiveProvider() *BigoLiveProvider {
	return &BigoLiveProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewBigoLiveProvider())
}

func (p *BigoLiveProvider) Name() string {
	return "BigoLive"
}

func (p *BigoLiveProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://www.bigo.tv/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "bigolive: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "bigolive: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "BigoLive"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("bigolive: rate limit exceeded")
	}
	return nil, nil
}
