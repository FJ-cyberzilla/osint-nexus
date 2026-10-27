package provider

import (
	"context"
	"fmt"
	"net/http"

	"github.com/FJ-cyberzilla/osint-nexus/internal/types"
	"github.com/rotisserie/eris"
)

const (
	PinterestBaseURL      = "https://www.pinterest.com"
	PinterestConfidence   = 0.9
	PinterestPlatformName = "Pinterest"
	PinterestAccountID    = "pinterest-detected"
)

// PinterestProvider probes Pinterest profiles.
type PinterestProvider struct {
	client *http.Client
}

// NewPinterestProvider initializes a new PinterestProvider.
func NewPinterestProvider() *PinterestProvider {
	return &PinterestProvider{
		client: NewHTTPClient(),
	}
}

func init() {
	Register(NewPinterestProvider())
}

// Name returns the provider name.
func (p *PinterestProvider) Name() string {
	return PinterestPlatformName
}

// CheckUsername probes Pinterest for the username.
func (p *PinterestProvider) CheckUsername(ctx context.Context, username string) (*types.IdentityProfile, error) {
	url := fmt.Sprintf("%s/%s", PinterestBaseURL, username)
	resp, err := PerformRequest(ctx, p.client, url)
	if err != nil {
		return nil, eris.Wrap(err, "pinterest: execute request failed")
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}

	if resp.StatusCode != http.StatusOK {
		return nil, eris.Errorf("pinterest: unexpected status code: %d", resp.StatusCode)
	}

	usernameCopy := username
	platform := PinterestPlatformName
	return &types.IdentityProfile{
		Username: username,
		Accounts: []types.Account{
			{
				ID:       PinterestAccountID,
				Username: &usernameCopy,
				Platform: &platform,
			},
		},
		ConfidenceScore: PinterestConfidence,
	}, nil
}
