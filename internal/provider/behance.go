package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// BehanceProvider probes Behance profile existence.
type BehanceProvider struct {
	client *http.Client
}

func NewBehanceProvider() *BehanceProvider {
	return &BehanceProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewBehanceProvider())
}

func (p *BehanceProvider) Name() string {
	return "Behance"
}

func (p *BehanceProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://www.behance.net/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "behance: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")
	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "behance: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "Behance"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("behance: rate limit exceeded")
	}
	return nil, nil
}
