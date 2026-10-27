package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// StackOverflowProvider probes StackOverflow profile existence.
type StackOverflowProvider struct {
	client *http.Client
}

// NewStackOverflowProvider initializes a new StackOverflowProvider.
func NewStackOverflowProvider() *StackOverflowProvider {
	return &StackOverflowProvider{
		client: &http.Client{Timeout: 10 * time.Second},
	}
}

func init() {
	Register(NewStackOverflowProvider())
}

// Name returns the provider name.
func (p *StackOverflowProvider) Name() string {
	return "StackOverflow"
}

// CheckUsername checks if a username/user ID exists on StackOverflow.
func (p *StackOverflowProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://stackoverflow.com/users/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "stackoverflow: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "stackoverflow: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "StackOverflow"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{
				{
					Username: &username,
					Platform: &platform,
				},
			},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("stackoverflow: rate limit exceeded")
	}
	return nil, nil
}
