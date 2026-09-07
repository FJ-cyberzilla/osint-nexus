package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// TwitterProvider probes the Twitter/X platform.
type TwitterProvider struct {
	client *http.Client
}

// NewTwitterProvider initializes a new TwitterProvider.
func NewTwitterProvider() *TwitterProvider {
	return &TwitterProvider{
		client: NewHTTPClient(),
	}
}

// Name returns the provider name.
func (p *TwitterProvider) Name() string {
	return "TwitterProvider"
}

// CheckUsername performs a Twitter lookup for the given username.
func (p *TwitterProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://twitter.com/%s", username)

	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, fmt.Errorf("provider: twitter request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil // User not found
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("provider: twitter unexpected status: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := "Twitter"
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       "twitter-detected",
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: 0.9,
	}, nil
}
