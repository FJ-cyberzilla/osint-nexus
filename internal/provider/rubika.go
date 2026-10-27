package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// RubikaProvider probes Rubika profile existence.
type RubikaProvider struct {
	client *http.Client
}

func NewRubikaProvider() *RubikaProvider {
	return &RubikaProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewRubikaProvider())
}

func (p *RubikaProvider) Name() string {
	return "Rubika"
}

func (p *RubikaProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://rubika.ir/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "rubika: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "rubika: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Rubika"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.85,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("rubika: rate limit exceeded")
	}
	return nil, nil
}
