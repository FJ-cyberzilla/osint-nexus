package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// InstagramProvider probes the Instagram platform.
type InstagramProvider struct {
	client  *http.Client
	baseURL string
}

// NewInstagramProvider initializes a new InstagramProvider.
func NewInstagramProvider() *InstagramProvider {
	return &InstagramProvider{
		client:  NewHTTPClient(),
		baseURL: "https://www.instagram.com",
	}
}

// NewInstagramProviderWithURL initializes a new InstagramProvider with a custom base URL.
func NewInstagramProviderWithURL(baseURL string) *InstagramProvider {
	return &InstagramProvider{
		client:  NewHTTPClient(),
		baseURL: baseURL,
	}
}

// Name returns the provider name.
func (p *InstagramProvider) Name() string {
	return "InstagramProvider"
}

// CheckUsername performs an Instagram lookup for the given username.
func (p *InstagramProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s/", p.baseURL, username)

	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, fmt.Errorf("provider: instagram request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil // User not found
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("provider: instagram unexpected status: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := "Instagram"
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       "instagram-detected",
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: 0.9,
	}, nil
}
