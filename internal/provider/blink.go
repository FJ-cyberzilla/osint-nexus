package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// BlinkProvider probes Blink profile/site existence.
type BlinkProvider struct {
	client *http.Client
}

func NewBlinkProvider() *BlinkProvider {
	return &BlinkProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewBlinkProvider())
}

func (p *BlinkProvider) Name() string {
	return "Blink"
}

func (p *BlinkProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://blinkist.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "blink: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "blink: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Blink"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("blink: rate limit exceeded")
	}
	return nil, nil
}
