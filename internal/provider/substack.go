package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// SubstackProvider probes Substack profile existence.
type SubstackProvider struct {
	client *http.Client
}

func NewSubstackProvider() *SubstackProvider {
	return &SubstackProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewSubstackProvider())
}

func (p *SubstackProvider) Name() string {
	return "Substack"
}

func (p *SubstackProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://%s.substack.com", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "substack: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "substack: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Substack"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("substack: rate limit exceeded")
	}
	return nil, nil
}
