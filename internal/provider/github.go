package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
)

// GitHubProvider probes GitHub.
type GitHubProvider struct {
	client *http.Client
}

// NewGitHubProvider initializes a new GitHubProvider.
func NewGitHubProvider() *GitHubProvider {
	return &GitHubProvider{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// Name returns the provider name.
func (p *GitHubProvider) Name() string {
	return "GitHub"
}

// CheckUsername probes GitHub for the username.
func (p *GitHubProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://github.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("github: create request: %w", err)
	}

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("github: execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "GitHub"
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
	return nil, nil // Username not found or error
}
