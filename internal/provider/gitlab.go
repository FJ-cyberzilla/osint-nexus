package provider

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

// GitLabProvider probes GitLab profile existence.
type GitLabProvider struct {
	client *http.Client
}

// NewGitLabProvider initializes a new GitLabProvider.
func NewGitLabProvider() *GitLabProvider {
	return &GitLabProvider{client: &http.Client{Timeout: 10 * time.Second}}
}

func init() {
	Register(NewGitLabProvider())
}

// Name returns the provider name.
func (p *GitLabProvider) Name() string {
	return "GitLab"
}

// CheckUsername checks if username exists on GitLab.
func (p *GitLabProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("https://gitlab.com/%s", username)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, eris.Wrap(err, "gitlab: create request")
	}
	req.Header.Set("User-Agent", "OSINT-Nexus/1.0")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, eris.Wrap(err, "gitlab: execute request")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		platform := "GitLab"
		return &types.IdentityProfile{
			Username: username,
			Accounts: []types.Account{{Username: &username, Platform: &platform}},
			ConfidenceScore: 0.9,
		}, nil
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, eris.New("gitlab: rate limit exceeded")
	}
	return nil, nil
}
