package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	RedditBaseURL      = "https://www.reddit.com/user"
	RedditConfidence   = 0.9
	RedditPlatformName = "Reddit"
	RedditAccountID    = "reddit-detected"
)

// RedditProvider probes Reddit profiles.
type RedditProvider struct {
	client *http.Client
}

// NewRedditProvider initializes a new RedditProvider.
func NewRedditProvider() *RedditProvider {
	return &RedditProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewRedditProvider())
}

// Name returns the provider name.
func (p *RedditProvider) Name() string {
	return RedditPlatformName
}

// CheckUsername probes Reddit for the username.
func (p *RedditProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s", RedditBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "reddit: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("reddit: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := RedditPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       RedditAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: RedditConfidence,
	}, nil
}
