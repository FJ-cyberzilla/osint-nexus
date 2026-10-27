package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	FacebookBaseURL      = "https://www.facebook.com"
	FacebookConfidence   = 0.9
	FacebookPlatformName = "Facebook"
	FacebookAccountID    = "facebook-detected"
)

// FacebookProvider probes Facebook profiles.
type FacebookProvider struct {
	client *http.Client
}

// NewFacebookProvider initializes a new FacebookProvider.
func NewFacebookProvider() *FacebookProvider {
	return &FacebookProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewFacebookProvider())
}

// Name returns the provider name.
func (p *FacebookProvider) Name() string {
	return FacebookPlatformName
}

// CheckUsername probes Facebook for the username.
func (p *FacebookProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s", FacebookBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "facebook: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("facebook: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := FacebookPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       FacebookAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: FacebookConfidence,
	}, nil
}
