package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	LinkedInBaseURL       = "https://www.linkedin.com/in"
	LinkedInConfidence    = 0.9
	LinkedInPlatformName  = "LinkedIn"
	LinkedInAccountID     = "linkedin-detected"
)

// LinkedInProvider probes LinkedIn profiles.
type LinkedInProvider struct {
	client *http.Client
}

// NewLinkedInProvider initializes a new LinkedInProvider.
func NewLinkedInProvider() *LinkedInProvider {
	return &LinkedInProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewLinkedInProvider())
}

// Name returns the provider name.
func (p *LinkedInProvider) Name() string {
	return LinkedInPlatformName
}

// CheckUsername probes LinkedIn for the username.
func (p *LinkedInProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s", LinkedInBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "linkedin: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("linkedin: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := LinkedInPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       LinkedInAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: LinkedInConfidence,
	}, nil
}
